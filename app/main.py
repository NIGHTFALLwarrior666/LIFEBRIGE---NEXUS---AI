"""Main FastAPI Application for LifeBridge AI.

Provides the emergency analysis API, deterministic demo endpoints,
health checks, and serves the Google AI command-center frontend.
"""

import logging
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.fallback import get_demo_scenario
from app.gemini_service import analyze_incident_with_gemini
from app.models import HealthResponse, LifeBridgeResponse
from app.security import sanitize_user_text, validate_uploaded_file

# Setup application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("lifebridge.app")

app = FastAPI(
    title="LifeBridge AI",
    description="Emergency multimodal understanding & deterministic validation decision support system.",
    version="1.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    # Content Security Policy allowing local styles, fonts, and scripts
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "script-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; "
        "media-src 'self' blob:; "
        "connect-src 'self';"
    )
    return response


# Global Exception Handler: Prevent stack trace leakage
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {type(exc).__name__}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal processing error",
            "message": "The system encountered an unexpected condition. Safe emergency fallback protocol is recommended.",
        },
    )


# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

# Mount static directory for CSS, JS, and UI assets
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/health", response_model=HealthResponse, tags=["Operational"])
async def health_check():
    """
    Standard Cloud Run health probe.
    Must always return HTTP 200 without requiring API keys or external network calls.
    """
    return HealthResponse(
        status="ok",
        service="lifebridge-ai",
        version="1.0.0",
        gemini_configured=settings.has_gemini_key,
    )


@app.post("/api/analyze", response_model=LifeBridgeResponse, tags=["Analysis"])
async def analyze_incident(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    demo_scenario: Optional[str] = Form(None),
):
    """
    Primary multimodal emergency understanding endpoint.
    Accepts text descriptions, disaster photos, audio recordings, or 1-click demo keys.
    """
    # 1. Deterministic Demo Scenario Handler (Zero-network, instant, reliable)
    if demo_scenario:
        clean_scenario = demo_scenario.strip().lower()
        logger.info(f"Processing instant demo scenario: '{clean_scenario}'")
        return get_demo_scenario(clean_scenario)

    # 2. Input Validation
    clean_text = sanitize_user_text(text)
    file_info = await validate_uploaded_file(file)

    if not clean_text and not file_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty emergency input. Please provide a situational description, an image, an audio file, or select a demo scenario.",
        )

    file_bytes, safe_name, mime_type = (file_info if file_info else (None, None, None))

    # 3. Route to Multimodal Intelligence & Deterministic Validation
    result = await analyze_incident_with_gemini(
        text=clean_text,
        file_bytes=file_bytes,
        mime_type=mime_type,
        filename=safe_name,
    )
    return result


@app.get("/", response_class=FileResponse, tags=["UI"])
async def serve_index():
    """Serve the Google AI emergency command-center frontend."""
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Frontend interface index.html not found.",
        )
    return FileResponse(str(index_path))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
    )
