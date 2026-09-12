# Master Agent — Query Processing Workflow

## 1. Overview

The app has two layers that work together:

- **Navigation layer** (UI): Login → 4 categories → 3–4 sub-parts each → chatbot. This narrows down *which agents are even in play* before a query is typed.
- **Query processing layer** (backend): once a query hits the chatbot, it may need one agent or several. This document covers that pipeline — decomposition, parallel dispatch across Groq API keys, aggregation, and final synthesis.

---

## 2. Architecture map

```
┌─────────────────────────────────┐
│      Frontend / chatbot UI      │
│  Login → categories → sub-parts │
└────────────────┬─────────────────┘
                  │ query / final answer
                  ▼
┌─────────────────────────────────┐        ┌──────────────────┐
│   Master agent orchestrator     │───────▶│   Groq key pool   │
│  Intent check · decompose ·     │◀───────│    Round-robin    │
│         synthesize              │        │     4–5 keys      │
└────────────────┬─────────────────┘        └──────────────────┘
                  │ parallel dispatch (Stage 3)
     ┌────────────┼────────────┬────────────┐
     ▼            ▼            ▼            ▼
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│Category1│  │Category2│  │Category3│  │Category4│
│3-4 agent│  │3-4 agent│  │3-4 agent│  │3-4 agent│
│ links   │  │ links   │  │ links   │  │ links   │
└─────────┘  └─────────┘  └─────────┘  └─────────┘
```

- The orchestrator is the **only** component that talks to Groq directly — it uses the key pool for its own reasoning steps (intent check, decomposition, synthesis), not for the domain answers themselves.
- The 4 category groups represent the 40 deployment links, grouped the same way as the UI. Responses flow back up through the orchestrator to the frontend.
- This maps onto the pipeline below: Frontend → Orchestrator is Stage 1, Orchestrator ↔ Groq pool covers Stages 2 and 6, Orchestrator → Category groups is Stage 3.

---

## 3. Pipeline stages

```
User query
    │
    ▼
[1] Intent check — single-agent or composite?
    │
    ├── single agent ──────────────► [4] Call that one deployment link
    │                                         │
    └── composite ──► [2] Decompose into parts
                              │
                              ▼
                      [3] Parallel dispatch
                      (fan out to relevant
                       deployment links, using
                       a pool of Groq keys)
                              │
                              ▼
                      [5] Collect partial results
                              │
                              ▼
                      [6] Final synthesis call
                      (Groq, combines everything
                       into one answer)
                              │
                              ▼
                         Response to user
```

### Stage 1 — Intent check
A cheap, fast Groq call (small model, short prompt) decides: does this query map cleanly to the one agent already selected via navigation, or does it span multiple sub-parts/categories?

- If the user is inside a **scoped chatbot** (they navigated to a specific sub-part) and the query fits that scope → skip straight to Stage 4. No decomposition needed. This is the common case and should be the fast path.
- If the query is broader, or the chatbot is a **global entry point**, → go to Stage 2.

This check matters because decomposition + parallel calls + synthesis is 3–4x the latency and API cost of a direct call. Don't pay that cost unless the query actually needs it.

### Stage 2 — Decomposition
One Groq call takes the user's query and the registry of relevant agent descriptions, and returns a structured breakdown: which sub-questions map to which agents.

Example output shape:
```json
{
  "parts": [
    { "sub_query": "...", "agent_id": "cat2_sub1", "endpoint_url": "..." },
    { "sub_query": "...", "agent_id": "cat3_sub4", "endpoint_url": "..." }
  ]
}
```

Keep this list short — 2–4 parts max. If the model wants to split into more than that, the query is probably too broad; consider asking the user to narrow it instead of fanning out further.

### Stage 3 — Parallel dispatch across Groq keys
Each part is sent to its target agent endpoint concurrently. Since you have 4–5 Groq API keys, assign them **round-robin across the concurrent calls** rather than using one key for everything.

Why this matters: Groq enforces per-key rate limits (requests/minute and tokens/minute). If Stage 1's intent check, Stage 2's decomposition, all of Stage 3's parallel parts, and Stage 6's synthesis all share a single key, you'll hit throttling under any real concurrent load — which is exactly when a hackathon demo tends to fall over (judges hammering it, multiple users at once). A small key pool absorbs that.

Suggested allocation:
- Reserve **1 key** for Stage 1 (intent check) + Stage 2 (decomposition) + Stage 6 (synthesis) — these are sequential, low-volume, latency-sensitive.
- Rotate the **remaining 3–4 keys** round-robin across Stage 3's parallel part-calls.
- If a key errors with a rate-limit response, retry that one part on the next key in the pool rather than failing the whole request.

### Stage 4 — Direct call (single-agent path)
Straightforward: call the one endpoint with the query, get the response, return it (optionally lightly reformatted). No fan-out, no synthesis call needed.

### Stage 5 — Collect partial results
Wait for all Stage 3 calls with a timeout per call (e.g. 8–10s). If a part fails or times out:
- Don't fail the whole response — proceed with whatever came back.
- Note internally which part is missing so Stage 6 can account for it (e.g. "I couldn't reach the pricing agent, here's what I found on the rest").

### Stage 6 — Final synthesis
One last Groq call takes the original query + all partial results (with labels for which agent/sub-part each came from) and produces a single coherent answer. This is also where you handle:
- Conflicting information between parts (say so, don't silently pick one)
- Missing parts (acknowledge what wasn't available)
- Formatting the final answer for the chat UI

---

## 4. Data contracts

**Decomposition output** (Stage 2 → Stage 3): see JSON shape above.

**Per-agent call** (Stage 3/4 request):
```json
{ "query": "the sub_query or original query text" }
```

**Per-agent response** (expected back):
```json
{ "answer": "...", "agent_id": "..." }
```

If the 40 deployment links don't already share this shape, you'll need a thin adapter per agent that maps its actual request/response format to this contract — decide this early since it blocks everything downstream.

**Synthesis input** (Stage 5 → Stage 6):
```json
{
  "original_query": "...",
  "parts": [
    { "agent_id": "...", "sub_query": "...", "answer": "...", "status": "ok" },
    { "agent_id": "...", "sub_query": "...", "answer": null, "status": "failed" }
  ]
}
```

---

## 5. Data storage — MongoDB

MongoDB is a solid fit here, mainly because your data is naturally nested rather than relational, and a hackathon has no time for schema migrations.

**What it's genuinely good for in this project:**
- `users` — login/auth records
- `conversations` — chat sessions, each with a nested array of messages, which agent(s) answered, and which category/sub-part the session was scoped to
- `query_logs` — original query, the decomposition output, each part's result and status, the final synthesized answer, and latency per stage. This is worth keeping even just for the hackathon demo — being able to show "here's what happened under the hood" for a query is a strong demo moment.
- `agents` (the registry) — id, name, description, category, sub-part, endpoint URL, auth type, expected input/output schema. Storing it in Mongo (vs. a static JSON file) means you can edit descriptions without redeploying, which matters if you're still tuning routing accuracy close to the deadline.

**One honest caveat:** at only 40 agents, the registry alone doesn't *need* a database — a static JSON config file works fine and is one less moving part to debug during the hackathon. Mongo earns its place because of `users` and `conversations`/`query_logs`, not because 40 records requires a database. If you want to cut scope under time pressure, keep the registry as a JSON file and only put user/session data in Mongo.

**If you later want semantic/embedding-based routing** (from the earlier discussion — comparing a query against agent description embeddings), MongoDB Atlas has native Vector Search, so you could store description embeddings right on the `agents` documents instead of standing up a separate vector database.

Example document shapes:
```json
// agents collection
{
  "_id": "cat1_sub2",
  "name": "...",
  "description": "...",
  "category": "Category 1",
  "sub_part": "Sub-part 2",
  "endpoint_url": "...",
  "auth_type": "api_key"
}

// query_logs collection
{
  "user_id": "...",
  "query": "...",
  "route": "single | composite",
  "parts": [ { "agent_id": "...", "status": "ok", "latency_ms": 420 } ],
  "final_answer": "...",
  "created_at": "..."
}
```

---

## 6. Error handling

| Failure | Handling |
|---|---|
| One part times out | Continue with remaining parts, flag as missing in synthesis |
| A Groq key hits rate limit | Retry that call on the next key in the pool |
| Decomposition returns 0 parts / malformed JSON | Fall back to treating it as a single-agent query using the best-matching agent |
| All parts fail | Return a direct apology/fallback message rather than calling synthesis on nothing |
| Synthesis call itself fails | Return the raw partial answers concatenated, rather than nothing |

---

## 7. Hackathon scope

**Build first:**
- Stage 4 (direct single-agent path) — this covers the majority of scoped-chatbot queries and needs no decomposition or key rotation at all.
- Stage 1 intent check, kept simple (even a rule: "if scoped chatbot and query mentions nothing outside current sub-part, go direct").

**Build second (if time allows):**
- Full decomposition → parallel dispatch → synthesis loop (Stages 2, 3, 5, 6) for the global/composite case.
- Key rotation pool and retry-on-rate-limit logic.

**Cut if short on time:**
- Sophisticated conflict resolution in synthesis — a simple "here's what each source said" listing is an acceptable fallback.
- Retry logic — a single attempt per part with a clear failure message is fine for a demo.

---

## 8. Open questions to resolve before building

- Do all 40 deployment links already return a consistent JSON shape, or do you need per-agent adapters?
- Should the intent check (Stage 1) be a real LLM call, or can it just be "scoped chatbot = always direct, global chatbot = always decompose"? The latter is simpler and may be good enough.
- What's an acceptable max latency for a composite query (decomposition + parallel calls + synthesis is at least 3 sequential LLM round-trips)? This affects whether you show a loading/progress indicator in the UI.
- Registry in Mongo vs. static JSON file — worth deciding now, since it affects how you edit agent descriptions while tuning routing accuracy later.
