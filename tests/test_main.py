"""Comprehensive automated test suite for LifeBridge AI.

Tests all operational gates:
- Root and health routes
- Multimodal analysis and fallback flows
- Deterministic safety validation and escalation rules
- Input limits, MIME allowlists, and size guards
- Gemini mocking and malformed recovery
- Security headers and privacy guards
"""

import asyncio
import io
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import EscalationEnum, LifeBridgeResponse, ProcessingStatusEnum, SeverityEnum
from app.security import sanitize_filename, sanitize_user_text
from app.validation import apply_deterministic_validation

client = TestClient(app)


# ==============================================================================
# 1. Operational & Routing Tests
# ==============================================================================

def test_root_serves_frontend():
    """Verify GET / delivers the Nexus AI landing page at production root."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Nexus" in response.text
    assert "Automate Claim Denials" in response.text
    assert "roi-calculator" in response.text


def test_lifebridge_frontend_route():
    """Verify GET /lifebridge delivers the emergency command-center frontend."""
    response = client.get("/lifebridge")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "LifeBridge AI" in response.text
    assert "Situational Input Console" in response.text


def test_health_check():
    """Verify GET /health returns 200 OK without requiring API key or external calls."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "lifebridge-ai"
    assert "version" in data
    assert "gemini_configured" in data


def test_security_headers():
    """Verify security headers are applied to HTTP responses."""
    response = client.get("/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert "default-src" in response.headers.get("Content-Security-Policy", "")


# ==============================================================================
# 2. Deterministic Demo Scenarios Tests (Phase 8)
# ==============================================================================

def test_demo_road_accident():
    """Verify deterministic Road Accident scenario."""
    response = client.post("/api/analyze", data={"demo_scenario": "road_accident"})
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "fallback"
    assert data["severity"] == SeverityEnum.CRITICAL.value
    assert data["escalation_required"] == EscalationEnum.EMERGENCY_SERVICES.value
    assert len(data["recommended_actions"]) > 0
    assert len(data["do_not_do"]) > 0
    assert any("spinal" in d.lower() or "neck" in d.lower() for d in data["do_not_do"])
    assert "DECISION SUPPORT ONLY" in data["disclaimer"]


def test_demo_flood_rescue():
    """Verify deterministic Flood Rescue scenario."""
    response = client.post("/api/analyze", data={"demo_scenario": "flood_rescue"})
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "fallback"
    assert data["severity"] == SeverityEnum.CRITICAL.value
    assert data["escalation_required"] == EscalationEnum.EMERGENCY_SERVICES.value
    assert any("water" in h.lower() for h in data["detected_hazards"])
    assert any("wade" in d.lower() or "swim" in d.lower() for d in data["do_not_do"])


def test_demo_medical_note():
    """Verify deterministic Handwritten Medical Note scenario."""
    response = client.post("/api/analyze", data={"demo_scenario": "medical_note"})
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "fallback"
    assert data["severity"] == SeverityEnum.HIGH.value
    assert data["escalation_required"] in (EscalationEnum.CONTACT_AUTHORITY.value, EscalationEnum.EMERGENCY_SERVICES.value)
    assert any("allergy" in h.lower() or "dose" in h.lower() for h in data["detected_hazards"])


# ==============================================================================
# 3. Fallback Engine & Unconfigured Key Resilience
# ==============================================================================

def test_custom_text_fallback_without_key():
    """Verify arbitrary custom text gracefully routes to safe heuristic fallback when API key is missing."""
    response = client.post(
        "/api/analyze",
        data={"text": "Large chemical spill on factory floor, strong chlorine smell, workers coughing"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "fallback"
    assert data["processing_status"] == ProcessingStatusEnum.FALLBACK.value
    assert len(data["recommended_actions"]) >= 1
    assert len(data["do_not_do"]) >= 1
    assert data["confidence"] > 0.0


# ==============================================================================
# 4. Input Validation & Security Rejections (Phase 5 & 14)
# ==============================================================================

def test_empty_input_rejected():
    """Verify completely empty input returns HTTP 400."""
    response = client.post("/api/analyze", data={})
    assert response.status_code == 400
    assert "Empty emergency input" in response.json()["detail"]


def test_empty_file_rejected():
    """Verify zero-byte file upload returns HTTP 400."""
    empty_file = io.BytesIO(b"")
    response = client.post(
        "/api/analyze",
        files={"file": ("empty.jpg", empty_file, "image/jpeg")}
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_unsupported_mime_rejected():
    """Verify executable or dangerous MIME uploads are blocked (HTTP 415)."""
    fake_exe = io.BytesIO(b"MZ\x90\x00executable_payload")
    response = client.post(
        "/api/analyze",
        files={"file": ("malware.exe", fake_exe, "application/x-msdownload")}
    )
    assert response.status_code == 415
    assert "Unsupported file type" in response.json()["detail"]


def test_oversized_file_rejected():
    """Verify files larger than 10MB are rejected with HTTP 413."""
    oversized = io.BytesIO(b"X" * (10 * 1024 * 1024 + 50))
    response = client.post(
        "/api/analyze",
        files={"file": ("massive.jpg", oversized, "image/jpeg")}
    )
    assert response.status_code == 413
    assert "exceeds maximum allowed size" in response.json()["detail"].lower()


def test_filename_sanitization():
    """Verify path traversal filenames are normalized safely."""
    assert sanitize_filename("../../../etc/passwd.png") == "passwd.png"
    assert sanitize_filename("..\\..\\windows\\system32\\calc.jpg") == "calc.jpg"
    assert sanitize_filename("safe_crash_photo.webp") == "safe_crash_photo.webp"


def test_text_length_limit():
    """Verify oversized text payloads are rejected."""
    with pytest.raises(Exception):
        sanitize_user_text("A" * 15000)


# ==============================================================================
# 5. Deterministic Validation & Safety Engine (Phase 7)
# ==============================================================================

def test_safety_override_critical_severity():
    """CRITICAL severity MUST override escalation_required to EMERGENCY_SERVICES."""
    raw_output = {
        "incident_type": "Severe Train Derailment",
        "severity": "CRITICAL",
        "summary": "Train cars off tracks near populated town.",
        "escalation_required": "NONE",  # Deliberately erroneous AI output
        "confidence": 0.95,
        "recommended_actions": ["Call emergency services"],
        "do_not_do": ["Do not walk on tracks"]
    }
    validated = apply_deterministic_validation(raw_output, mode="gemini")
    assert validated.severity == SeverityEnum.CRITICAL
    assert validated.escalation_required == EscalationEnum.EMERGENCY_SERVICES
    assert any(rec.rule_id == "SAFETY-CRIT-01" for rec in validated.validation_records)


def test_safety_override_high_severity():
    """HIGH severity MUST override NONE escalation to CONTACT_AUTHORITY."""
    raw_output = {
        "incident_type": "Downed High-Voltage Wire",
        "severity": "HIGH",
        "summary": "Powerline sparking on roadway.",
        "escalation_required": "NONE",
        "confidence": 0.85,
    }
    validated = apply_deterministic_validation(raw_output, mode="gemini")
    assert validated.severity == SeverityEnum.HIGH
    assert validated.escalation_required == EscalationEnum.CONTACT_AUTHORITY
    assert any(rec.rule_id == "SAFETY-HIGH-01" for rec in validated.validation_records)


def test_confidence_score_clamping():
    """Confidence scores outside [0.0, 1.0] must be clamped."""
    raw_output = {
        "incident_type": "Test Incident",
        "severity": "LOW",
        "summary": "Minor fender bender.",
        "confidence": 1.45,  # Out of range
    }
    validated = apply_deterministic_validation(raw_output, mode="gemini")
    assert validated.confidence == 1.0
    assert any(rec.rule_id == "RULE-CONF-01" for rec in validated.validation_records)

    raw_output_neg = {
        "incident_type": "Test Incident",
        "severity": "LOW",
        "summary": "Minor fender bender.",
        "confidence": -0.2,  # Out of range
    }
    validated_neg = apply_deterministic_validation(raw_output_neg, mode="gemini")
    assert validated_neg.confidence == 0.0


def test_empty_actions_safety_injection():
    """Empty actions list must be populated with baseline safety posture."""
    raw_output = {
        "incident_type": "Unknown Event",
        "severity": "MODERATE",
        "summary": "Sirens heard in distance.",
        "recommended_actions": [],
        "do_not_do": []
    }
    validated = apply_deterministic_validation(raw_output, mode="gemini")
    assert len(validated.recommended_actions) >= 1
    assert len(validated.do_not_do) >= 1


# ==============================================================================
# 6. Gemini Integration & Malformed Recovery (Phase 4)
# ==============================================================================

def test_gemini_service_mocked_success():
    """Test successful Gemini API execution with mocked google-genai client."""
    from app.gemini_service import analyze_incident_with_gemini

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '''{
        "incident_type": "Industrial Chemical Hazard",
        "severity": "HIGH",
        "summary": "Ammonia tank valve leak in warehouse.",
        "detected_hazards": ["Toxic vapor cloud", "Respiratory distress"],
        "recommended_actions": ["Evacuate facility upwind", "Notify hazmat team"],
        "do_not_do": ["Do not enter without breathing apparatus"],
        "missing_information": ["Current valve pressure"],
        "uncertainties": ["Containment integrity"],
        "confidence": 0.91,
        "escalation_required": "EMERGENCY_SERVICES",
        "sources_or_evidence": ["Visual mist from valve nozzle"]
    }'''
    mock_client.models.generate_content.return_value = mock_response

    with patch("app.gemini_service.get_genai_client", return_value=mock_client):
        result = asyncio.run(analyze_incident_with_gemini(text="Ammonia leak in warehouse"))
        assert result.mode == "gemini"
        assert result.incident_type == "Industrial Chemical Hazard"
        assert result.severity == SeverityEnum.HIGH
        assert result.confidence == 0.91
        assert "Toxic vapor cloud" in result.detected_hazards


def test_gemini_service_malformed_json_recovery():
    """Test recovery when Gemini returns malformed non-JSON text."""
    from app.gemini_service import analyze_incident_with_gemini

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "This is not valid JSON at all: error 500 occurred"
    mock_client.models.generate_content.return_value = mock_response

    with patch("app.gemini_service.get_genai_client", return_value=mock_client):
        # Should gracefully recover via heuristic fallback without crashing
        result = asyncio.run(analyze_incident_with_gemini(text="House fire with smoke"))
        assert result.mode == "fallback"
        assert result.severity in (SeverityEnum.HIGH, SeverityEnum.CRITICAL)
        assert len(result.recommended_actions) >= 1


# ==============================================================================
# 9. Nexus AI B2B SaaS MVP Landing Page Tests
# ==============================================================================

def test_nexus_landing_serves_html():
    """Verify GET /nexus/ serves the complete Nexus AI B2B SaaS landing page."""
    response = client.get("/nexus/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Nexus" in response.text
    assert "Automate Claim Denials" in response.text
    assert "roi-calculator" in response.text
    assert "Midwest Specialty" in response.text
    assert "HIPAA" in response.text


def test_nexus_demo_qualification_endpoint():
    """Verify POST /api/nexus/demo-qualification processes qualified clinic leads."""
    lead_payload = {
        "email": "sarah.lin@beaconhealth.org",
        "name": "Sarah Lin",
        "company": "Beacon Health Partners",
        "job_title": "VP of Operations",
        "company_size": "5000-15000",
        "primary_workflow": "Prior-authorization delays and claim rejections",
        "selected_slot": "Tomorrow at 10:00 AM EST",
    }
    response = client.post("/api/nexus/demo-qualification", json=lead_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "Demo consultation" in data["message"]
    assert data["data"]["email"] == "sarah.lin@beaconhealth.org"


def test_nexus_roi_estimate_endpoint():
    """Verify POST /api/nexus/roi-estimate computes accurate operational ROI."""
    calc_payload = {
        "specialists": 8,
        "hours_per_week": 22,
        "hourly_rate": 38.0,
        "monthly_claims": 4500,
        "denial_rate_pct": 14.0,
    }
    response = client.post("/api/nexus/roi-estimate", json=calc_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["net_annual_savings"] > 100000
    assert data["hours_saved_weekly"] > 100
    assert data["payback_months"] < 12.0
    assert data["roi_multiple"] > 1.0


def test_nexus_demo_qualification_validation_error():
    """Verify POST /api/nexus/demo-qualification rejects invalid/missing required fields."""
    invalid_payload = {
        "email": "not-an-email",
        # missing required name and company
    }
    response = client.post("/api/nexus/demo-qualification", json=invalid_payload)
    assert response.status_code == 422


def test_nexus_landing_without_trailing_slash():
    """Verify GET /nexus (without trailing slash) serves Nexus AI landing page."""
    response = client.get("/nexus")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Nexus" in response.text
    assert "Automate Claim Denials" in response.text


def test_nexus_root_static_assets():
    """Verify GET /styles.css and GET /app.js deliver assets for root-level loading."""
    css_res = client.get("/styles.css")
    assert css_res.status_code == 200
    assert "text/css" in css_res.headers["content-type"]
    assert len(css_res.content) > 1000

    js_res = client.get("/app.js")
    assert js_res.status_code == 200
    assert "javascript" in js_res.headers["content-type"]
    assert len(js_res.content) > 1000
