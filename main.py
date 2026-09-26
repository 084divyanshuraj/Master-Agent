"""
Vercel Serverless Entry Point
Exports FastAPI app for Vercel's Python runtime.
"""
import os
import sys

# Add project root directory to sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from server import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"\n========================================================")
    print(f"🚀 Vignan University Master Agent Server Starting...")
    print(f"📍 Web Portal: http://localhost:{port}")
    print(f"📍 API Docs:   http://localhost:{port}/docs")
    print(f"📍 API Health: http://localhost:{port}/api/health")
    print(f"========================================================\n")
    uvicorn.run("server:app", host=host, port=port, reload=True)

