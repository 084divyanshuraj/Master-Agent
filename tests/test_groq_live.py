import asyncio
import json
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))
from dotenv import load_dotenv
load_dotenv(override=True)

from backend.groq_pool import GroqKeyPool
from backend.orchestrator import MasterOrchestrator

async def main():
    pool = GroqKeyPool()
    print(f"=== Groq Pool Initialized: {pool.total_keys} Keys ===")
    for s in pool.get_pool_status():
        print(f"Key {s['index']}: {s['masked_key']} | Active: {s['is_active']}")

    print("\n--- Testing Round-Robin Rotation Across Keys ---")
    for i in range(4):
        res = await pool.chat_completion(
            messages=[{"role": "user", "content": f"Reply with the number {i+1} only."}],
            model="openai/gpt-oss-20b"
        )
        print(f"Call {i+1}: Key={res.get('key_used')}, Latency={res.get('latency_ms')}ms, Status={res.get('status')}, Content={repr(res.get('content').strip())}")

    print("\n--- Testing Full 6-Stage Master Orchestrator Pipeline ---")
    orchestrator = MasterOrchestrator()
    query = "Students with attendance under 75% in Computer Science and faculty timetable rescheduling."
    result = await orchestrator.execute_query(query=query, mode="global")

    print(f"\nPipeline Status: {result.get('status')}")
    print(f"Route: {result.get('route')}")
    stages = result.get("trace", {}).get("stages", {})
    print("Stage 1 (Intent):", stages.get("stage_1"))
    print("Stage 2 (Decomposition parts):", len(stages.get("stage_2", {}).get("parts", [])))
    print("Stage 3 & 5 (Dispatched parts):", stages.get("stage_3_and_5", {}).get("total_dispatched"))
    print("Stage 6 (Synthesis): Model used:", stages.get("stage_6", {}).get("model_used"), "Key used:", stages.get("stage_6", {}).get("key_used"))
    print("\n=== Synthesized Final Answer Snippet ===")
    sys.stdout.reconfigure(encoding='utf-8')
    print(result.get("answer"))

if __name__ == "__main__":
    asyncio.run(main())
