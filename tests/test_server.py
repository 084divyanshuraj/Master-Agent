import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))
sys.stdout.reconfigure(encoding='utf-8')

from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    print("✓ Health endpoint OK:", data)

def test_status():
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert data["groq_keys_total"] == 5
    print("✓ Status endpoint OK (Groq Pool 5 keys):", data["groq_keys_total"])

def test_agents():
    res = client.get("/api/agents")
    assert res.status_code == 200
    data = res.json()
    assert data["total_agents"] == 72
    assert len(data["groups"]) == 14
    print(f"✓ Agents endpoint OK: {data['total_agents']} agents loaded across {len(data['groups'])} groups.")

def test_scoped_chat():
    payload = {
        "query": "Generate a 50-mark question paper for Machine Learning with Bloom's taxonomy.",
        "mode": "scoped",
        "agent_id": "agent_31"
    }
    res = client.post("/api/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["mode"] == "scoped"
    print("✓ Scoped chat endpoint OK (Agent 31):", data["answer"][:100], "...")

def test_global_chat():
    payload = {
        "query": "Review faculty workload and journal quartile publications in CSE department.",
        "mode": "global"
    }
    res = client.post("/api/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "trace" in data
    stages = data["trace"]["stages"]
    print(f"✓ Global 6-stage chat OK:")
    print("  - Stage 1 route:", stages["stage_1"]["route"])
    print("  - Stage 6 synthesis model:", stages["stage_6"]["model_used"])
    print("  - Stage 6 Groq key used:", stages["stage_6"]["key_used"])

def test_auth():
    import uuid
    test_code = f"VFSTR-TEST-{uuid.uuid4().hex[:6].upper()}"
    test_email = f"user_{uuid.uuid4().hex[:6]}@vignan.ac.in"

    # 1. Test Register
    reg_payload = {
        "name": "Dr. Automated Test",
        "employee_code": test_code,
        "email": test_email,
        "role": "faculty",
        "department": "AIML",
        "password": "securePass123"
    }
    reg_res = client.post("/api/auth/register", json=reg_payload)
    assert reg_res.status_code == 200
    assert reg_res.json()["success"] is True
    print(f"✓ Auth Register OK ({test_code}):", reg_res.json()["message"])

    # 2. Test Login Success
    login_res = client.post("/api/auth/login", json={
        "employee_code": test_code,
        "password": "securePass123"
    })
    assert login_res.status_code == 200
    assert login_res.json()["success"] is True
    assert login_res.json()["user"]["name"] == "Dr. Automated Test"
    print("✓ Auth Login Success OK:", login_res.json()["user"]["rollNumber"])

    # 3. Test Login Wrong Password
    bad_login = client.post("/api/auth/login", json={
        "employee_code": test_code,
        "password": "wrongpassword"
    })
    assert bad_login.status_code == 401
    print("✓ Auth Wrong Password Rejected OK (HTTP 401)")

    # 4. Test Demo Pre-seeded Login
    demo_login = client.post("/api/auth/login", json={
        "employee_code": "VFSTR-HOD-CSE-01",
        "password": "vignan123"
    })
    assert demo_login.status_code == 200
    assert demo_login.json()["user"]["name"] == "Dr. K. V. Rao"
    print("✓ Demo User Login OK (Dr. K. V. Rao)")

if __name__ == "__main__":
    test_health()
    test_status()
    test_agents()
    test_auth()
    test_scoped_chat()
    test_global_chat()
    print("\n🎉 ALL TESTS PASSED SUCCESSFULLY!")
