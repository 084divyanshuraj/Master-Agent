import os
import sys
from urllib.parse import parse_qs

# Add project root to sys.path so backend and server can be imported by Vercel serverless runtime
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from server import app as fastapi_app


class VercelPathMiddleware:
    """
    ASGI Middleware to resolve request paths on Vercel Serverless runtime.
    Handles:
      1. Query param `__path` passed by vercel.json rewrite: /api/(.*) -> /api/index.py?__path=$1
      2. Header `x-matched-path` from Vercel Edge Proxy
      3. Stripping of /api or keeping /api matching dual FastAPI decorators
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            query_string = scope.get("query_string", b"").decode("utf-8")
            params = parse_qs(query_string)

            if "__path" in params and params["__path"]:
                target = params["__path"][0].lstrip("/")
                # Set path to /api/<target> (e.g., /api/auth/login or /api/health)
                scope["path"] = f"/api/{target}"
            else:
                headers = dict(scope.get("headers", []))
                matched_path = headers.get(b"x-matched-path", b"").decode("utf-8")
                if matched_path and not matched_path.endswith("index.py"):
                    scope["path"] = matched_path

        await self.app(scope, receive, send)


app = VercelPathMiddleware(fastapi_app)
