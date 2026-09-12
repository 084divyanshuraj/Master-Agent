# Architecture Map

## System diagram

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
                  │
                  ▼
         ┌──────────────────┐
         │     MongoDB       │
         │ users · convos ·  │
         │ query_logs ·      │
         │ agents (optional) │
         └──────────────────┘
```

---

## Components

### Frontend / chatbot UI
- Login screen, then a home screen showing 4 category cards.
- Each category expands into 3–4 sub-parts.
- Each sub-part opens a chatbot scoped to that one agent's deployment link by default.
- Sends the user's query to the orchestrator and renders the final answer.

### Master agent orchestrator
The only backend component every request passes through. Responsible for:
- **Intent check** — is this query answerable by the single agent already selected via navigation, or does it need more than one agent (composite query)?
- **Decomposition** — for composite queries, breaks the query into sub-queries, each mapped to a target agent.
- **Synthesis** — combines partial results from multiple agents into one coherent final answer.

This is the only component that calls Groq directly. It does not hold any domain knowledge itself — that lives in the 40 deployment links.

### Groq key pool
- 4–5 API keys, assigned round-robin across concurrent calls.
- Used for the orchestrator's own reasoning steps (intent check, decomposition, synthesis) and, when fanning out to multiple agents in parallel, spread across calls to avoid hitting a single key's rate limit.
- On a rate-limit error, retry the call on the next key in the pool rather than failing outright.

### Category agent groups (the 40 deployment links)
- Grouped into 4 categories of 3–4 sub-part agents each, matching the frontend's navigation structure.
- Each is an independently deployed endpoint with its own description, used both for routing (matching queries to the right agent) and for actually answering.
- Ideally share one request/response contract (`{"query": "..."}` → `{"answer": "..."}`); if not, each needs a thin adapter.

### MongoDB
- `users` — login/auth records.
- `conversations` — chat sessions, message history, which agent(s)/category/sub-part a session is scoped to.
- `query_logs` — original query, decomposition output, per-part status and latency, final answer. Useful for debugging and for demoing "what happened under the hood."
- `agents` (optional) — the 40-agent registry, if you want to edit descriptions/endpoints without redeploying. At 40 records this could also just be a static JSON file; Mongo earns its place mainly through the other three collections.

---

## Data flow (composite query example)

1. User query arrives at the orchestrator from the frontend.
2. Orchestrator's intent check (Groq call) decides this needs more than one agent.
3. Orchestrator decomposes the query into 2–3 parts (Groq call), each tagged with a target agent.
4. Parts are dispatched in parallel to their category agents, using rotated Groq keys where the orchestrator itself needs to reason about each leg.
5. Orchestrator collects results, handling any timeouts or failures.
6. Orchestrator synthesizes one final answer from the partial results (Groq call).
7. Answer returned to the frontend; the full trace (query, parts, latencies, final answer) is written to `query_logs`.

For a single-agent query (the common case inside a scoped sub-part chatbot), steps 2–3 and 6 are skipped — the orchestrator calls the one relevant agent directly and returns its answer.
