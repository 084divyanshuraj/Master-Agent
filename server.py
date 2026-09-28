"""
Vignan's University — Master Agent Orchestration Server (FastAPI)
Exposes the Master Agent API, Groq Key Pool metrics, MongoDB audit logs, and serves the frontend.
"""

import os
import sys
import time

# Ensure UTF-8 output encoding on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

from backend.orchestrator import orchestrator
from backend.groq_pool import groq_pool
from backend.db import db

load_dotenv()

app = FastAPI(
    title="Vignan's University — Master Agent API",
    description="Centralized Master Agent Orchestrator across 72 specialized departmental hackathon agents.",
    version="2.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def vercel_path_resolver(request: Request, call_next):
    """
    Normalizes request paths across Vercel Serverless Functions, proxy rewrites, and direct calls.
    Ensures that routes like /api/auth/login, /api/health, and /api/chat always match
    regardless of how Vercel or any proxy rewrote the path.
    """
    path = request.scope.get("path", "")

    # 1. Query parameter __path from vercel.json rewrite
    if "__path" in request.query_params and request.query_params["__path"]:
        target = request.query_params["__path"].lstrip("/")
        request.scope["path"] = f"/api/{target}"
        request._url = None
    # 2. Check if path was rewritten to index.py
    elif path in ("/api/index.py", "/index.py", "/api", "/api/"):
        invoke_path = request.headers.get("x-invoke-path") or request.headers.get("x-forwarded-uri")
        if invoke_path and not invoke_path.endswith("index.py"):
            request.scope["path"] = invoke_path
            request._url = None
        else:
            matched = request.headers.get("x-matched-path", "")
            if matched and not matched.endswith("index.py"):
                request.scope["path"] = matched
                request._url = None

    # 3. Always reset root_path to avoid Starlette stripping /api prefix
    request.scope["root_path"] = ""

    response = await call_next(request)
    return response


class ChatRequest(BaseModel):
    query: str
    mode: Optional[str] = "global"  # 'global' or 'scoped'
    agent_id: Optional[str] = None
    user: Optional[Dict[str, Any]] = None


class UserRegisterRequest(BaseModel):
    name: str
    employee_code: str
    email: str
    role: str = "faculty"
    department: str = "CSE"
    password: str


class UserLoginRequest(BaseModel):
    employee_code: str
    password: str


@app.post("/api/auth/register")
@app.post("/auth/register")
async def register_user_endpoint(req: UserRegisterRequest):
    """Registers a new faculty or staff member into MongoDB Atlas."""
    if len(req.password.strip()) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters.")
    res = db.register_user(
        name=req.name,
        employee_code=req.employee_code,
        email=req.email,
        role=req.role,
        department=req.department,
        password=req.password
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message", "Registration failed."))
    return res


@app.post("/api/auth/login")
@app.post("/auth/login")
async def login_user_endpoint(req: UserLoginRequest):
    """Authenticates faculty credentials against MongoDB Atlas."""
    res = db.authenticate_user(
        employee_code=req.employee_code,
        password=req.password
    )
    if not res.get("success"):
        raise HTTPException(status_code=401, detail=res.get("message", "Authentication failed."))
    return res


@app.post("/api/auth/session")
@app.post("/auth/session")
async def save_session_endpoint(req: Dict[str, Any]):
    """Saves user session profile into MongoDB Atlas."""
    db.save_user_session(req)
    return {"status": "success", "synced": True}


@app.get("/api/health")
@app.get("/health")
async def health_check():
    return {
        "status": "online",
        "university": "Vignan's Foundation for Science, Technology & Research",
        "orchestrator": "Active",
        "groq_pool": groq_pool.get_pool_status(),
        "database": db.get_status(),
    }


@app.get("/api/status")
@app.get("/status")
async def get_system_status():
    """Returns real-time status of Groq keys, MongoDB connection, and registered agents."""
    return {
        "orchestrator_agents_loaded": len(orchestrator.agents_map),
        "groups_count": len(orchestrator.groups_list),
        "groq_keys_total": groq_pool.total_keys,
        "groq_pool_details": groq_pool.get_pool_status(),
        "database_status": db.get_status(),
    }


@app.get("/api/agents")
@app.get("/agents")
async def get_agents():
    """Returns the full 40-agent registry categorized by the 4 official groups."""
    return {
        "groups": orchestrator.groups_list,
        "total_agents": len(orchestrator.agents_map),
    }


@app.post("/api/chat")
@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """
    Main Master Agent execution endpoint:
    Executes Intent Check -> Decomposition -> Parallel Dispatch -> Fault Isolation -> Synthesis.
    """
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        result = await orchestrator.execute_query(
            query=req.query,
            mode=req.mode or "global",
            agent_id=req.agent_id,
            user_info=req.user,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Master Agent Orchestration Error: {str(e)}")


class EndpointUpdateRequest(BaseModel):
    endpoint_url: str


@app.post("/api/agents/{agent_id}/endpoint")
@app.post("/agents/{agent_id}/endpoint")
async def update_agent_endpoint(agent_id: str, req: EndpointUpdateRequest):
    """Saves custom deployed URL for an agent into MongoDB Atlas."""
    if not req.endpoint_url.strip():
        raise HTTPException(status_code=400, detail="Endpoint URL cannot be empty.")
    success = orchestrator.set_agent_endpoint(agent_id, req.endpoint_url.strip())
    return {
        "status": "success" if success else "warning",
        "agent_id": agent_id,
        "endpoint_url": req.endpoint_url.strip(),
        "database": db.get_status(),
    }


@app.get("/api/analytics")
@app.get("/analytics")
async def get_analytics():
    """Provides high-level institutional metrics and top queried agents from MongoDB."""
    return db.get_analytics_summary()


@app.get("/api/logs")
@app.get("/logs")
async def get_audit_logs(limit: int = 20):
    """Returns recent query traces from MongoDB query_logs for live demonstration."""
    return {
        "recent_traces": db.get_recent_logs(limit=limit),
        "database": db.get_status(),
    }


class ReportExportRequest(BaseModel):
    query: str
    answer: str
    format: Optional[str] = "markdown"  # 'markdown', 'text', 'json'
    citations: Optional[List[Dict[str, Any]]] = None
    trace: Optional[Dict[str, Any]] = None
    user_info: Optional[Dict[str, Any]] = None
    session_title: Optional[str] = "Master Agent Executive Report"


@app.post("/api/report/export")
@app.post("/report/export")
async def export_report_endpoint(req: ReportExportRequest):
    """
    Exports a structured accreditation audit report generated by the Master Agent.
    Supports markdown (.md), plain text (.txt), and technical json (.json) formatting.
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    report_id = f"VFSTR-MA-RPT-{int(time.time())}"
    user_name = (req.user_info or {}).get("name", "Faculty / Staff")
    user_dept = (req.user_info or {}).get("department", "CSE")
    user_role = str((req.user_info or {}).get("role", "Faculty")).upper()

    citations_list = req.citations or []
    citations_md = "\n".join([f"- **{c.get('name', 'Agent')}**: {c.get('url', 'N/A')}" for c in citations_list]) if citations_list else "None"
    citations_txt = "\n".join([f"  * {c.get('name', 'Agent')}: {c.get('url', 'N/A')}" for c in citations_list]) if citations_list else "  * None"

    if req.format and req.format.lower() in ("md", "markdown"):
        content = f"""# VIGNAN'S FOUNDATION FOR SCIENCE, TECHNOLOGY & RESEARCH
## Master Agent Executive Intelligence Report & Accreditation Audit
**Document Control ID:** `{report_id}`  
**Generated Timestamp:** {timestamp}  
**Authorized Official:** {user_name} ({user_dept} — {user_role})  
**Institutional Accreditation:** NAAC 'A+' Grade | NBA Tier-1 Compliant | UGC Section 3

---

### 1. Executive Objective / Administrative Query
> {req.query}

---

### 2. Synthesized Master Agent Findings & Analysis
{req.answer}

---

### 3. Verified Sub-Agent Intelligence Sources & Citations
{citations_md}

---

### 4. Orchestration Pipeline Audit Telemetry
- **Total Latency:** {req.trace.get('total_time_ms', 'N/A') if req.trace else 'N/A'} ms
- **Operational Mode:** {req.trace.get('mode', 'Global Master') if req.trace else 'Global Master'}
- **Groq Model:** {req.trace.get('stages', {}).get('stage_6', {}).get('model', 'openai/gpt-oss-120b') if req.trace else 'openai/gpt-oss-120b'}
- **Verification Seal:** VFSTR-ORCHESTRATOR-VERIFIED-SECURE

*CONFIDENTIAL — FOR INTERNAL UNIVERSITY GOVERNANCE & NBA/NAAC ACCREDITATION EVALUATION ONLY*
"""
        return {"report_id": report_id, "format": "markdown", "filename": f"{report_id}.md", "content": content}

    elif req.format and req.format.lower() in ("txt", "text"):
        content = f"""================================================================================
VIGNAN'S FOUNDATION FOR SCIENCE, TECHNOLOGY & RESEARCH (VFSTR)
MASTER AGENT EXECUTIVE AUDIT REPORT & ORCHESTRATION DOSSIER
================================================================================
Report ID     : {report_id}
Date & Time   : {timestamp}
User Profile  : {user_name} [{user_dept} - {user_role}]
Accreditation : NAAC 'A+' Grade | NBA Tier-1 Accredited

--------------------------------------------------------------------------------
1. QUERY / ADMINISTRATIVE OBJECTIVE:
--------------------------------------------------------------------------------
{req.query}

--------------------------------------------------------------------------------
2. MASTER AGENT SYNTHESIZED FINDINGS:
--------------------------------------------------------------------------------
{req.answer}

--------------------------------------------------------------------------------
3. VERIFIED SUB-AGENT CITATIONS:
--------------------------------------------------------------------------------
{citations_txt}

--------------------------------------------------------------------------------
4. ORCHESTRATION PIPELINE TELEMETRY:
--------------------------------------------------------------------------------
- Latency     : {req.trace.get('total_time_ms', 'N/A') if req.trace else 'N/A'} ms
- Scope       : {req.trace.get('mode', 'Global Master') if req.trace else 'Global Master'}
- Digital Seal: VFSTR-ORCHESTRATOR-AUTHENTICATED
================================================================================
CONFIDENTIAL - OFFICIAL VFSTR ACCREDITATION AUDIT RECORD
================================================================================
"""
        return {"report_id": report_id, "format": "text", "filename": f"{report_id}.txt", "content": content}

    else:
        return {
            "report_id": report_id,
            "format": "json",
            "filename": f"{report_id}.json",
            "metadata": {
                "university": "Vignan's Foundation for Science, Technology & Research",
                "timestamp": timestamp,
                "user": req.user_info,
                "report_id": report_id
            },
            "query": req.query,
            "answer": req.answer,
            "citations": citations_list,
            "trace": req.trace
        }


# Mount static frontend files
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), "public")
if os.path.exists(PUBLIC_DIR):
    app.mount("/", StaticFiles(directory=PUBLIC_DIR, html=True), name="static")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"\n========================================================")
    print(f"🚀 Vignan University Master Agent Server Starting...")
    print(f"📍 Web Portal: http://localhost:{port}")
    print(f"📍 API Docs:   http://localhost:{port}/docs")
    print(f"📍 API Health: http://localhost:{port}/api/health")
    print(f"========================================================\n")
    uvicorn.run("server:app", host=host, port=port, reload=True)
