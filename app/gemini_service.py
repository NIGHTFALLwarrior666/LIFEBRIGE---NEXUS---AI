"""Gemini API Integration Service using the official google-genai SDK.

Handles multimodal inputs (text, photos, audio), enforces structured Pydantic
output, bounds generation parameters, and handles all network/quota/auth failures safely.
"""

import json
import logging
from typing import Optional
from app.config import settings
from app.models import IncidentAnalysisSchema, LifeBridgeResponse
from app.validation import apply_deterministic_validation
from app.fallback import generate_heuristic_fallback

logger = logging.getLogger("lifebridge.gemini")

# Lazy-loaded singleton genai Client
_genai_client = None


def get_genai_client():
    """Obtain or initialize the Google GenAI client."""
    global _genai_client
    if _genai_client is None:
        if not settings.has_gemini_key:
            return None
        try:
            from google import genai
            _genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        except Exception as exc:
            logger.error(f"Failed to initialize Google GenAI client: {type(exc).__name__}")
            _genai_client = None
    return _genai_client


SYSTEM_INSTRUCTION = """You are LifeBridge AI, an emergency multimodal understanding system.
Your mission is to analyze messy real-world human input (frantic text descriptions, disaster photos, audio clips, handwritten medical notes)
and extract structured, objective incident intelligence to support emergency decision-making.

Operating Principles:
1. Fact-based: Distinguish observed evidence from assumptions.
2. Safety-first: Identify critical physical, chemical, electrical, or medical hazards immediately.
3. Negative Constraints ("DO NOT DO"): Specify life-saving actions to explicitly AVOID (e.g., do not move injured necks unless on fire, do not walk into floodwaters).
4. Preserve Uncertainty: Highlight missing information and unverified facts. Never invent certainty.
5. Decision Support: You provide situational clarity and decision support; you do NOT certify medical diagnoses or claim automated emergency dispatch.
"""


async def analyze_incident_with_gemini(
    text: str,
    file_bytes: Optional[bytes] = None,
    mime_type: Optional[str] = None,
    filename: Optional[str] = None,
) -> LifeBridgeResponse:
    """
    Invoke Gemini multimodal model with bounded generation parameters and structured schema.
    Gracefully degrades to deterministic fallback on any failure.
    """
    client = get_genai_client()
    if not client:
        logger.info("Gemini API key not configured or client unavailable. Routing to deterministic fallback.")
        return generate_heuristic_fallback(text, filename)

    try:
        from google.genai import types

        contents = []

        # 1. Attach multimodal media if present
        if file_bytes and mime_type:
            media_part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
            contents.append(media_part)

        # 2. Attach user situational text
        user_prompt = text.strip() if text else "Analyze the attached media and provide emergency decision support."
        contents.append(user_prompt)

        # 3. Call Gemini with structured output
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=IncidentAnalysisSchema,
            temperature=0.1,  # Low temperature for deterministic, factual extraction
            candidate_count=1,
            system_instruction=SYSTEM_INSTRUCTION,
        )

        model_name = settings.GEMINI_MODEL or "gemini-2.5-flash"
        logger.info(f"Calling Gemini model '{model_name}' for multimodal analysis...")

        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=config,
        )

        if not response or not response.text:
            logger.warning("Empty response received from Gemini. Falling back to heuristic engine.")
            return generate_heuristic_fallback(text, filename)

        # 4. Parse JSON and apply deterministic validation
        raw_json = json.loads(response.text)
        return apply_deterministic_validation(raw_json, mode="gemini")

    except Exception as exc:
        # Safe logging without leaking secrets, tokens, or raw client data
        logger.error(f"Gemini API processing failed ({type(exc).__name__}: {str(exc)[:150]}). Routing to fallback.")
        return generate_heuristic_fallback(text, filename)
