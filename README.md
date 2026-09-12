# Vignan's University — Master Agent Enterprise Portal

An Enterprise AI Orchestration Platform built for **Vignan's Foundation for Science, Technology & Research (VFSTR)** to coordinate and unify institutional intelligence across **72 specialized departmental hackathon agents**.

---

## Architecture & System Workflow

The Master Agent operates on an autonomous **6-stage pipeline** designed for fault-tolerant query execution:

1. **Stage 1 (Intent Check)**: Determines if the incoming query targets a single specialized department or is a composite cross-cutting operational inquiry.
2. **Stage 2 (Query Decomposition)**: LLM decomposes composite requests into 2–4 targeted sub-queries mapped directly to relevant departmental agents.
3. **Stage 3 (Parallel Dispatch)**: Dispatches requests in parallel across an active **Groq Key Pool** using round-robin rotation to avoid rate limits.
4. **Stage 4 (Direct Execution)**: High-speed fast-path for single-agent scoped chat rooms.
5. **Stage 5 (Fault Isolation)**: Catches individual agent timeouts/failures so partial responses still contribute to institutional synthesis without pipeline termination.
6. **Stage 6 (Executive Synthesis)**: Combines partial agent answers into a comprehensive institutional executive report using `openai/gpt-oss-120b`.

---

## Key Features

- **72 Departmental Agents**: Categorized into 4 Core Divisions and 14 Sub-Category Groups (Academics, Examinations, Research, Placements, Governance, Student Affairs, and IQAC Strategy).
- **Groq Key Pool**: Round-robin load balancing across multiple API keys with automatic 15-second cooldown on HTTP 429 rate limit backoff.
- **MongoDB Atlas Integration**: Live persistent storage for query audit logs (`query_logs`), faculty credentials (`users`), and dynamic agent deployment URLs (`agent_endpoints`).
- **Faculty & Staff Authentication**: Authorized access portal with role-based designations (HoDs, Deans, Faculty, Examination Cell) and salted SHA-256 password hashing.
- **Live Deployed Webview**: Embedded interactive container enabling direct interaction with external deployed agent web applications and microservices.

---

## Tech Stack

- **Backend**: Python 3.13, FastAPI, Uvicorn, Pydantic, HTTPX, PyMongo
- **LLM Engine**: Groq API (`openai/gpt-oss-20b` for fast decomposition; `openai/gpt-oss-120b` for synthesis)
- **Database**: MongoDB Atlas Cluster
- **Frontend**: Vanilla HTML5, CSS3 Glassmorphism Design System, JavaScript ES6+, HTML5 Canvas Constellation Network

---

## Local Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/084divyanshuraj/Master-Agent.git
cd Master-Agent
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your API credentials:
```bash
cp .env.example .env
```
Configure your Groq API keys and MongoDB Atlas connection string in `.env`:
```env
GROQ_API_KEYS=gsk_key1,gsk_key2,gsk_key3
GROQ_MODEL_FAST=openai/gpt-oss-20b
GROQ_MODEL_SYNTHESIS=openai/gpt-oss-120b
MONGODB_URI=mongodb+srv://<user>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority
PORT=8000
HOST=0.0.0.0
```

### 4. Run the Server
```bash
python server.py
```

Open your browser at `http://localhost:8000` to launch the Master Agent Portal.
Interactive API documentation is available at `http://localhost:8000/docs`.

---

## License & University Attribution
Developed for **Vignan's Foundation for Science, Technology & Research (Deemed to be University)**.
