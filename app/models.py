"""Pydantic schemas and enums for LifeBridge AI."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class SeverityEnum(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class EscalationEnum(str, Enum):
    NONE = "NONE"
    MONITOR = "MONITOR"
    CONTACT_AUTHORITY = "CONTACT_AUTHORITY"
    EMERGENCY_SERVICES = "EMERGENCY_SERVICES"


class ProcessingStatusEnum(str, Enum):
    SUCCESS = "SUCCESS"
    FALLBACK = "FALLBACK"
    VALIDATION_CORRECTED = "VALIDATION_CORRECTED"
    ERROR = "ERROR"


class IncidentAnalysisSchema(BaseModel):
    """Schema for Gemini structured JSON output."""
    incident_type: str = Field(
        description="Concise categorization of the incident, e.g., 'Vehicle Collision', 'Flash Flood', 'Suspected Drug Interaction'"
    )
    severity: SeverityEnum = Field(
        description="Assessed severity level: LOW, MODERATE, HIGH, CRITICAL, UNKNOWN"
    )
    summary: str = Field(
        description="Factual, objective summary of the emergency situation without assumptions"
    )
    detected_hazards: List[str] = Field(
        default_factory=list,
        description="Physical, chemical, electrical, or environmental hazards identified from input"
    )
    recommended_actions: List[str] = Field(
        default_factory=list,
        description="Prioritized, clear, actionable next steps for responders or bystanders"
    )
    do_not_do: List[str] = Field(
        default_factory=list,
        description="Critical negative constraints and actions to explicitly avoid to prevent injury or worsening"
    )
    missing_information: List[str] = Field(
        default_factory=list,
        description="Crucial details not provided in the input that responders must discover"
    )
    uncertainties: List[str] = Field(
        default_factory=list,
        description="Ambiguities or unverified assumptions in the messy input"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 (high uncertainty) and 1.0 (verified certainty)"
    )
    escalation_required: EscalationEnum = Field(
        description="Required escalation tier: NONE, MONITOR, CONTACT_AUTHORITY, EMERGENCY_SERVICES"
    )
    sources_or_evidence: List[str] = Field(
        default_factory=list,
        description="Specific observed clues, sounds, text, or visual features supporting the assessment"
    )


class ValidationRecord(BaseModel):
    """Details of any deterministic correction applied to AI output."""
    rule_id: str
    description: str
    original_value: Optional[str] = None
    corrected_value: Optional[str] = None


class LifeBridgeResponse(BaseModel):
    """Final validated response returned to client."""
    mode: str = Field(
        description="'gemini' for live AI interpretation or 'fallback' for demo/safe-mode guidance"
    )
    incident_type: str
    severity: SeverityEnum
    summary: str
    detected_hazards: List[str]
    recommended_actions: List[str]
    do_not_do: List[str]
    missing_information: List[str]
    uncertainties: List[str]
    confidence: float = Field(ge=0.0, le=1.0)
    escalation_required: EscalationEnum
    sources_or_evidence: List[str]
    timestamp: str
    processing_status: ProcessingStatusEnum
    validation_records: List[ValidationRecord] = Field(default_factory=list)
    disclaimer: str = Field(
        default=(
            "DECISION SUPPORT ONLY: LifeBridge AI provides structured situational interpretation "
            "and deterministic validation. It does not provide certified medical diagnoses, "
            "guaranteed safety, or automatic emergency dispatch. In immediate danger, contact local emergency services directly."
        )
    )


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "lifebridge-ai"
    version: str = "1.0.0"
    gemini_configured: bool = False
