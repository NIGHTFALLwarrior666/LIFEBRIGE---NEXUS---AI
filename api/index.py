"""Vercel Serverless Function entrypoint for FastAPI.
Exposes the FastAPI application instance for Vercel Python runtime.
"""
from app.main import app
