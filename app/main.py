"""Main FastAPI Application for LifeBridge AI.

Provides the emergency analysis API, deterministic demo endpoints,
health checks, and serves the Google AI command-center frontend.
"""

import logging
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.fallback import get_demo_scenario
from app.gemini_service import analyze_incident_with_gemini
from app.models import HealthResponse, LifeBridgeResponse, NexusDemoLead, NexusRoiRequest
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

class VercelPathRewriteMiddleware:
    """ASGI Middleware to restore the original client request path when running
    behind Vercel Serverless Function rewrites.
    
    When vercel.json rewrites /(.*) to /api/index.py, Vercel sets the ASGI scope['path']
    to '/api/index.py' while forwarding the actual client URI in the 'x-matched-path' header.
    This middleware extracts that header and restores the original path and raw_path in scope,
    allowing FastAPI's router to match the correct routes (/, /nexus/, /styles.css, etc.).
    If no matched-path header exists but path is /api/index.py or /api, it safely falls back to '/'.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            headers = dict(scope.get("headers", []))
            matched_header = (
                headers.get(b"x-matched-path")
                or headers.get(b"x-vercel-matched-path")
                or headers.get(b"x-forwarded-uri")
                or headers.get(b"x-original-url")
            )

            if matched_header:
                try:
                    decoded = matched_header.decode("utf-8")
                except UnicodeDecodeError:
                    decoded = matched_header.decode("latin1", errors="replace")

                if "?" in decoded:
                    path_part, query_part = decoded.split("?", 1)
                else:
                    path_part = decoded
                    query_part = None

                if not path_part.startswith("/"):
                    path_part = "/" + path_part

                scope["path"] = path_part
                scope["raw_path"] = path_part.encode("utf-8")

                if query_part and not scope.get("query_string"):
                    scope["query_string"] = query_part.encode("utf-8")

            elif scope.get("path") in ("/api/index.py", "/api/index", "/api", "/api/"):
                scope["path"] = "/"
                scope["raw_path"] = b"/"

        await self.app(scope, receive, send)


# Vercel Path Rewrite Middleware (outermost handler)
app.add_middleware(VercelPathRewriteMiddleware)

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
NEXUS_DIR = BASE_DIR / "nexus_ai"

# Serverless environment directory fallback (Vercel / Cloud Run)
if not NEXUS_DIR.exists():
    for candidate in [Path.cwd() / "nexus_ai", Path.cwd(), Path(__file__).resolve().parent]:
        if (candidate / "index.html").exists():
            NEXUS_DIR = candidate
            break
        if (candidate / "nexus_ai" / "index.html").exists():
            NEXUS_DIR = candidate / "nexus_ai"
            break

if not STATIC_DIR.exists():
    for candidate in [Path.cwd() / "static", Path.cwd(), Path(__file__).resolve().parent]:
        if (candidate / "static").exists():
            STATIC_DIR = candidate / "static"
            break

# Mount static directory for CSS, JS, and UI assets (LifeBridge AI)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Mount Nexus AI B2B SaaS MVP Landing Page
if NEXUS_DIR.exists():
    app.mount("/nexus", StaticFiles(directory=str(NEXUS_DIR), html=True), name="nexus")


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


@app.post("/api/nexus/demo-qualification", tags=["Nexus AI"])
async def handle_nexus_demo(lead: NexusDemoLead):
    """
    Handle Nexus AI demo qualification form submission.
    Captures qualified clinic leads and preferred calendar time slot.
    """
    logger.info(f"Nexus AI Demo Qualification lead received: {lead.email} ({lead.company})")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "success",
            "message": "Demo consultation successfully scheduled.",
            "data": lead.model_dump(),
        },
    )


@app.post("/api/nexus/roi-estimate", tags=["Nexus AI"])
async def calculate_nexus_roi(params: NexusRoiRequest):
    """
    Server-side validated ROI calculation for Nexus AI.
    Calculates labor savings, denial rework recovery, and payback timeline.
    """
    annual_labor = params.specialists * params.hours_per_week * 52 * params.hourly_rate
    annual_claims = params.monthly_claims * 12
    annual_denials = annual_claims * (params.denial_rate_pct / 100.0)
    direct_rework = annual_denials * 48.0
    total_drag = annual_labor + direct_rework

    labor_saved = annual_labor * 0.85
    rework_saved = direct_rework * 0.92
    platform_cost = max(16000.0, annual_claims * 0.38)
    net_savings = max(25000.0, round((labor_saved + rework_saved) - platform_cost))
    hours_saved = round(params.specialists * params.hours_per_week * 0.85)
    total_benefit = labor_saved + rework_saved
    payback_months = max(0.8, round((platform_cost / total_benefit) * 12.0, 1)) if total_benefit > 0 else 2.1

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "success",
            "net_annual_savings": net_savings,
            "current_operational_drag": round(total_drag),
            "hours_saved_weekly": hours_saved,
            "payback_months": payback_months,
            "roi_multiple": round(((labor_saved + rework_saved) / platform_cost), 1),
        },
    )


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Return empty 204 for favicon requests."""
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --------------------------------------------------------------------------
# Nexus AI B2B SaaS Landing Page Routes (Production Root, Aliases & /nexus/)
# --------------------------------------------------------------------------
def _resolve_nexus_file(filename: str) -> Optional[Path]:
    """Helper to locate a file in nexus_ai directory across serverless runtimes."""
    candidates = [
        NEXUS_DIR / filename,
        BASE_DIR / "nexus_ai" / filename,
        Path.cwd() / "nexus_ai" / filename,
        Path.cwd() / filename,
        Path(__file__).resolve().parent.parent / "nexus_ai" / filename,
        Path(__file__).resolve().parent / "nexus_ai" / filename,
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            return c.resolve()
    return None


@app.get("/", response_class=FileResponse, tags=["Nexus AI"])
@app.get("/api/index.py", response_class=FileResponse, tags=["Nexus AI"], include_in_schema=False)
@app.get("/api/index", response_class=FileResponse, tags=["Nexus AI"], include_in_schema=False)
@app.get("/api", response_class=FileResponse, tags=["Nexus AI"], include_in_schema=False)
@app.get("/api/", response_class=FileResponse, tags=["Nexus AI"], include_in_schema=False)
async def serve_nexus_root():
    """Serve the complete Nexus AI B2B SaaS MVP landing page directly at production root."""
    resolved = _resolve_nexus_file("index.html")
    if not resolved:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nexus AI landing page index.html not found.",
        )
    return FileResponse(str(resolved), media_type="text/html")


@app.get("/nexus", response_class=FileResponse, tags=["Nexus AI"])
@app.get("/nexus/", response_class=FileResponse, tags=["Nexus AI"])
async def serve_nexus_page():
    """Serve the Nexus AI B2B SaaS MVP landing page at '/nexus/'."""
    return await serve_nexus_root()


@app.get("/styles.css", include_in_schema=False)
@app.get("/nexus/styles.css", include_in_schema=False)
async def serve_root_styles():
    """Serve styles.css when index.html is loaded from root or /nexus/ path."""
    resolved = _resolve_nexus_file("styles.css")
    if resolved:
        return FileResponse(str(resolved), media_type="text/css")
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="styles.css not found")


@app.get("/app.js", include_in_schema=False)
@app.get("/nexus/app.js", include_in_schema=False)
async def serve_root_js():
    """Serve app.js when index.html is loaded from root or /nexus/ path."""
    resolved = _resolve_nexus_file("app.js")
    if resolved:
        return FileResponse(str(resolved), media_type="application/javascript")
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="app.js not found")


# --------------------------------------------------------------------------
# LifeBridge AI Emergency Command Center Frontend
# --------------------------------------------------------------------------
@app.get("/lifebridge", response_class=FileResponse, tags=["LifeBridge AI"])
@app.get("/lifebridge/", response_class=FileResponse, tags=["LifeBridge AI"])
async def serve_lifebridge_frontend():
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
