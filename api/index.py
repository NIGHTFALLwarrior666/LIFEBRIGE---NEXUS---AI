"""Vercel Serverless Function entrypoint for FastAPI.
Exposes the FastAPI application instance for Vercel Python runtime.
Includes ASGI path rewrite middleware to seamlessly handle Vercel routing rewrites.
"""
import sys
from pathlib import Path

# Ensure project root is in sys.path for Vercel Serverless Function execution
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.main import app, VercelPathRewriteMiddleware

# Wrap the FastAPI application instance to ensure Vercel rewrites
# correctly restore the original request path from x-matched-path in ASGI scope
app = VercelPathRewriteMiddleware(app)
