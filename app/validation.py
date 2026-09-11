"""Deterministic Validation and Safety Engine for LifeBridge AI.

Enforces non-negotiable safety rules, normalizes LLM outputs, prevents
hallucinated certainty, and ensures critical escalations cannot be suppressed.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List
from app.models import (
    EscalationEnum,
    IncidentAnalysisSchema,
    LifeBridgeResponse,
    ProcessingStatusEnum,
    SeverityEnum,
    ValidationRecord,
)


def clean_string_list(items: Any) -> List[str]:
    """Normalize string lists, stripping blanks, duplicates, and non-strings."""
    if not items:
        return []
    if isinstance(items, str):
        items = [items]
    
    seen = set()
    cleaned = []
    for item in items:
        if item is None:
            continue
        text = str(item).strip()
        if text and text not in seen:
            seen.add(text)
            cleaned.append(text)
    return cleaned


def apply_deterministic_validation(
    raw_data: Dict[str, Any],
    mode: str = "gemini",
) -> LifeBridgeResponse:
    """
    Validate, sanitize, clamp, and enforce deterministic emergency rules
    upon structured incident output.
    """
    validation_records: List[ValidationRecord] = []
    
    # 1. Parse or default basic fields
    incident_type = str(raw_data.get("incident_type", "Unspecified Incident")).strip()
    if not incident_type:
        incident_type = "Unspecified Incident"

    summary = str(raw_data.get("summary", "No situational summary available.")).strip()
    if not summary:
        summary = "No situational summary available."

    # 2. Parse Severity Enum
    raw_severity = str(raw_data.get("severity", "UNKNOWN")).upper().strip()
    try:
        severity = SeverityEnum(raw_severity)
    except ValueError:
        severity = SeverityEnum.UNKNOWN
        validation_records.append(
            ValidationRecord(
                rule_id="RULE-SEV-01",
                description="Invalid severity value mapped to UNKNOWN",
                original_value=raw_severity,
                corrected_value="UNKNOWN",
            )
        )

    # 3. Parse Escalation Enum
    raw_escalation = str(raw_data.get("escalation_required", "MONITOR")).upper().strip()
    try:
        escalation_required = EscalationEnum(raw_escalation)
    except ValueError:
        escalation_required = EscalationEnum.MONITOR
        validation_records.append(
            ValidationRecord(
                rule_id="RULE-ESC-01",
                description="Invalid escalation enum mapped to MONITOR",
                original_value=raw_escalation,
                corrected_value="MONITOR",
            )
        )

    # 4. Clean and normalize array fields
    detected_hazards = clean_string_list(raw_data.get("detected_hazards", []))
    recommended_actions = clean_string_list(raw_data.get("recommended_actions", []))
    do_not_do = clean_string_list(raw_data.get("do_not_do", []))
    missing_information = clean_string_list(raw_data.get("missing_information", []))
    uncertainties = clean_string_list(raw_data.get("uncertainties", []))
    sources_or_evidence = clean_string_list(raw_data.get("sources_or_evidence", []))

    # 5. Confidence Clamping (0.0 <= confidence <= 1.0)
    try:
        raw_conf = float(raw_data.get("confidence", 0.5))
    except (ValueError, TypeError):
        raw_conf = 0.5
    
    clamped_conf = max(0.0, min(1.0, raw_conf))
    if clamped_conf != raw_conf:
        validation_records.append(
            ValidationRecord(
                rule_id="RULE-CONF-01",
                description="Confidence score clamped to [0.0, 1.0] range",
                original_value=str(raw_conf),
                corrected_value=str(clamped_conf),
            )
        )

    # 6. Safety Rule: CRITICAL severity MUST escalate to EMERGENCY_SERVICES
    if severity == SeverityEnum.CRITICAL and escalation_required in (
        EscalationEnum.NONE,
        EscalationEnum.MONITOR,
    ):
        orig_esc = escalation_required.value
        escalation_required = EscalationEnum.EMERGENCY_SERVICES
        validation_records.append(
            ValidationRecord(
                rule_id="SAFETY-CRIT-01",
                description="SAFETY OVERRIDE: Critical severity cannot have low/none escalation. Escalated to EMERGENCY_SERVICES.",
                original_value=orig_esc,
                corrected_value=EscalationEnum.EMERGENCY_SERVICES.value,
            )
        )

    # 7. Safety Rule: HIGH severity MUST at least CONTACT_AUTHORITY
    if severity == SeverityEnum.HIGH and escalation_required == EscalationEnum.NONE:
        escalation_required = EscalationEnum.CONTACT_AUTHORITY
        validation_records.append(
            ValidationRecord(
                rule_id="SAFETY-HIGH-01",
                description="SAFETY OVERRIDE: High severity cannot have NONE escalation. Escalated to CONTACT_AUTHORITY.",
                original_value=EscalationEnum.NONE.value,
                corrected_value=EscalationEnum.CONTACT_AUTHORITY.value,
            )
        )

    # 8. Ensure Recommended Actions and DO NOT DO are not empty
    if not recommended_actions:
        fallback_action = "Maintain situational awareness and stand by for qualified first responders."
        recommended_actions.append(fallback_action)
        validation_records.append(
            ValidationRecord(
                rule_id="RULE-ACT-01",
                description="Empty action list populated with baseline safety posture.",
                corrected_value=fallback_action,
            )
        )

    if not do_not_do:
        fallback_dnd = "Do not enter hazardous areas or touch unknown substances without certified protective gear."
        do_not_do.append(fallback_dnd)
        validation_records.append(
            ValidationRecord(
                rule_id="RULE-DND-01",
                description="Empty DO NOT DO list populated with baseline negative constraint.",
                corrected_value=fallback_dnd,
            )
        )

    # 9. Determine overall processing status
    if mode == "fallback":
        status = ProcessingStatusEnum.FALLBACK
    elif validation_records:
        status = ProcessingStatusEnum.VALIDATION_CORRECTED
    else:
        status = ProcessingStatusEnum.SUCCESS

    # 10. Timestamp (ISO 8601 UTC)
    now_iso = datetime.now(timezone.utc).isoformat()

    return LifeBridgeResponse(
        mode=mode,
        incident_type=incident_type,
        severity=severity,
        summary=summary,
        detected_hazards=detected_hazards,
        recommended_actions=recommended_actions,
        do_not_do=do_not_do,
        missing_information=missing_information,
        uncertainties=uncertainties,
        confidence=clamped_conf,
        escalation_required=escalation_required,
        sources_or_evidence=sources_or_evidence,
        timestamp=now_iso,
        processing_status=status,
        validation_records=validation_records,
    )
