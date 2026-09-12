"""Vercel Serverless Function entrypoint for FastAPI.
Exposes the FastAPI application instance for Vercel Python runtime.
"""
import sys
from pathlib import Path

# Ensure project root is in sys.path for Vercel Serverless Function execution
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.main import app
