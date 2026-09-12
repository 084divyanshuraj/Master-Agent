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
