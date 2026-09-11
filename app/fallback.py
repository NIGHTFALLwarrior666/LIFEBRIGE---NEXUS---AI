"""Deterministic Fallback Engine and Demo Scenarios for LifeBridge AI.

Guarantees 100% offline, zero-network, zero-credential operation with
three top-tier emergency scenarios and heuristic safe fallback for custom input.
"""

from typing import Dict, Any, Optional
from app.models import LifeBridgeResponse
from app.validation import apply_deterministic_validation


DEMO_SCENARIOS: Dict[str, Dict[str, Any]] = {
    "road_accident": {
        "title": "Road Accident",
        "description": "Multi-vehicle collision on highway with pinned passenger and smoking engine",
        "raw": {
            "incident_type": "Multi-Vehicle Highway Collision",
            "severity": "CRITICAL",
            "summary": "Two-vehicle high-speed collision observed on Route 9 southbound. One sedan has heavy front-end crushing with an occupant pinned in driver seat. Engine compartment is emitting dark smoke with visible fluid pooling beneath chassis. Second vehicle is overturned in adjacent ditch.",
            "detected_hazards": [
                "Engine smoke indicating active fire risk",
                "Flammable fluid / gasoline leak on hot asphalt",
                "Unstable vehicle balance on roadside slope",
                "High-speed traffic passing the collision zone",
                "Possible cervical spine / internal trauma to pinned occupant"
            ],
            "recommended_actions": [
                "Call 911 / emergency services immediately; state exact highway mile marker and report entrapment",
                "Deploy reflective hazard triangles or high-visibility markers 100 meters upstream if safe to do so",
                "Turn off ignitions of accessible vehicles if reachable without entering crushed compartments",
                "Communicate calmly with trapped driver from a safe distance; instruct them to keep head and neck still",
                "Keep a chemical fire extinguisher on standby at an upwind distance"
            ],
            "do_not_do": [
                "DO NOT attempt to pull or forcefully extricate the pinned occupant unless vehicle is actively on fire (prevents permanent spinal cord injury)",
                "DO NOT light road flares or smoke near leaking automotive fluids",
                "DO NOT allow bystanders to stand in active highway lanes or behind blinded corners",
                "DO NOT offer liquids, food, or medication to injured victims prior to surgical triage"
            ],
            "missing_information": [
                "Exact number of occupants inside overturned ditch vehicle",
                "Whether hazardous cargo or commercial transport was involved",
                "Presence of infants or children in rear passenger seats",
                "Consciousness and pulse status of pinned driver"
            ],
            "uncertainties": [
                "Whether the pooling liquid is coolant, transmission fluid, or pressurized gasoline",
                "Structural integrity of overturned vehicle roof"
            ],
            "confidence": 0.88,
            "escalation_required": "EMERGENCY_SERVICES",
            "sources_or_evidence": [
                "Visual report of frontal crush displacement and vehicle intrusion into cabin",
                "Observation of black acrid smoke and hydrocarbon odor from engine bay",
                "Audio of engine hissing and traffic horns"
            ]
        }
    },
    "flood_rescue": {
        "title": "Flood Rescue",
        "description": "Flash flood in residential basin, family stranded on roof, submerged transformer",
        "raw": {
            "incident_type": "Severe Flash Flood / Stranded Citizens",
            "severity": "CRITICAL",
            "summary": "Rapidly rising flash flood waters (estimated 5-6 feet depth) engulfing residential neighborhood. Family of four including one toddler is stranded on an exterior pitched roof. Water current is approximately 6-8 knots carrying large tree limbs and debris. Submerged electrical pad-mount transformer observed nearby.",
            "detected_hazards": [
                "Swift-water current capable of sweeping away humans and small watercraft",
                "Severe electrocution hazard from submerged electrical utility transformer",
                "Hypothermia from continuous rain and wind exposure",
                "Submerged obstacles, floating debris, and open sewer access points",
                "Risk of building foundation compromise or roof collapse under hydraulic pressure"
            ],
            "recommended_actions": [
                "Alert emergency dispatch for swift-water rescue team with GPS coordinates / address",
                "Instruct stranded individuals to tie themselves securely to chimney or load-bearing roof anchor",
                "Signal location using bright cloth, whistles, or phone flashlights (3 flashes = SOS)",
                "Request immediate regional power grid utility shutoff for the flooded sector",
                "Monitor water rise rate against identifiable exterior brick lines"
            ],
            "do_not_do": [
                "DO NOT enter or wade into moving flood water on foot under any circumstances (6 inches can sweep an adult)",
                "DO NOT attempt to swim toward the stranded individuals with makeshift floats",
                "DO NOT touch wet metal fences, lampposts, or water near the submerged transformer",
                "DO NOT take shelter in interior attics unless roof hatch access is verified (prevents drowning entrapment)"
            ],
            "missing_information": [
                "Structural load-bearing capacity of the flooded home",
                "Availability of boat or helicopter rescue units in local sector",
                "Medical conditions or mobility restrictions of the stranded family members"
            ],
            "uncertainties": [
                "Whether upstream dam or culvert has breached, which would cause secondary surge",
                "Whether electrical transformer is still energized on the substation side"
            ],
            "confidence": 0.85,
            "escalation_required": "EMERGENCY_SERVICES",
            "sources_or_evidence": [
                "Visual of brown churning water reaching gutter line",
                "Family signaling from second-story roof peak",
                "Sparks / transformer buzzing reported upstream prior to submersion"
            ]
        }
    },
    "medical_note": {
        "title": "Handwritten Medical Note",
        "description": "Confusing handwritten discharge/dosage instructions for elderly patient with suspected allergy contraindications",
        "raw": {
            "incident_type": "Ambiguous Medication Order & Allergy Risk",
            "severity": "HIGH",
            "summary": "Handwritten doctor note presented by anxious caregiver for 78-year-old cardiac patient. Note contains illegible decimal dosage (appears as '10mg' or '.10mg') of a potent blood thinner/antiarrhythmic, alongside a conflicting antibiotic prescription where patient has a documented severe penicillin anaphylaxis history.",
            "detected_hazards": [
                "Ten-fold overdose hazard due to ambiguous leading/trailing decimal point",
                "Fatal anaphylactic shock risk from beta-lactam cross-reactivity",
                "Unmonitored bleeding risk from unverified anticoagulant administration",
                "Caregiver anxiety and time pressure leading to hasty medication administration"
            ],
            "recommended_actions": [
                "Hold medication administration until verbal confirmation from prescribing physician or licensed pharmacist",
                "Contact prescribing clinic or 24-hour hospital pharmacy line to verify exact drug name, route, and dosage",
                "Cross-check patient's existing electronic health record or physical prescription bottles for current baseline medications",
                "Keep emergency contact numbers and epinephrine autoinjector readily accessible if accidental exposure occurs"
            ],
            "do_not_do": [
                "DO NOT guess or assume the dosage based on visual similarity of handwritten numerals",
                "DO NOT administer any penicillin-class or cephalosporin compound until allergy status is verified by clinician",
                "DO NOT split or crush unscored extended-release tablets without explicit pharmacist authorization",
                "DO NOT alter patient's established cardiovascular medication schedule without medical direction"
            ],
            "missing_information": [
                "Prescribing physician's registration number and direct telephone line",
                "Patient's baseline kidney and liver function panel",
                "Exact onset time of current acute symptoms"
            ],
            "uncertainties": [
                "Whether decimal point was intentional or ink splatter on paper",
                "Whether handwritten drug name refers to Amoxicillin or Ampicillin formulation"
            ],
            "confidence": 0.82,
            "escalation_required": "CONTACT_AUTHORITY",
            "sources_or_evidence": [
                "Photograph of crumpled paper note with cursive handwriting and unreadable signature",
                "Caregiver verbal testimony of patient's prior allergy hospital visit"
            ]
        }
    }
}


def get_demo_scenario(scenario_key: str) -> LifeBridgeResponse:
    """Retrieve and deterministically validate one of the three verified demo scenarios."""
    key = scenario_key.lower().strip().replace("-", "_").replace(" ", "_")
    if key not in DEMO_SCENARIOS:
        # Default to road accident
        key = "road_accident"
    
    scenario_data = DEMO_SCENARIOS[key]["raw"]
    return apply_deterministic_validation(scenario_data, mode="fallback")


def generate_heuristic_fallback(text: str, filename: Optional[str] = None) -> LifeBridgeResponse:
    """
    Generate an intelligent, safe heuristic response for arbitrary inputs when Gemini API is offline.
    Never pretends to be Gemini; marks mode='fallback'.
    """
    text_lower = text.lower() if text else ""
    
    # Categorization heuristic
    if any(w in text_lower for w in ["fire", "smoke", "burn", "flame", "explosion"]):
        incident_type = "Fire / Thermal Hazard Incident"
        severity = "HIGH"
        hazards = ["Toxic smoke inhalation", "Thermal burn injury", "Structural collapse risk", "Flammable accelerants"]
        actions = [
            "Evacuate everyone immediately to an upwind location away from the structure",
            "Call emergency fire services (911/112) with address and building occupancy count",
            "Close interior doors behind you during egress if safe to do so to starve the fire of oxygen"
        ]
        dnd = [
            "DO NOT re-enter burning building for personal belongings or pets",
            "DO NOT open doors that feel warm to the back of your hand",
            "DO NOT use elevators during fire evacuation"
        ]
        escalation = "EMERGENCY_SERVICES"
    elif any(w in text_lower for w in ["crash", "car", "accident", "highway", "collision", "vehicle"]):
        incident_type = "Motor Vehicle Incident"
        severity = "HIGH"
        hazards = ["Secondary traffic collisions", "Fuel leak and fire ignition", "Possible cervical spine injuries"]
        actions = [
            "Contact emergency dispatch with exact location and vehicle count",
            "Set hazard lights and place warning markers up-traffic if safe",
            "Keep victims still and reassure them until first responders arrive"
        ]
        dnd = [
            "DO NOT move injured individuals unless imminent life danger (e.g. fire)",
            "DO NOT light flares or smoke cigarettes near crashed vehicles",
            "DO NOT step into active traffic lanes"
        ]
        escalation = "EMERGENCY_SERVICES"
    elif any(w in text_lower for w in ["water", "flood", "drown", "river", "surge"]):
        incident_type = "Water / Flood Danger"
        severity = "HIGH"
        hazards = ["Swift-water current force", "Electrocution from submerged wiring", "Hypothermia and waterborne contaminants"]
        actions = [
            "Move immediately to the highest accessible ground or stable roof",
            "Call emergency services with GPS coordinates or roof markers",
            "Signal rescuers with high-visibility objects or whistle"
        ]
        dnd = [
            "DO NOT walk or drive through moving water (turn around, don't drown)",
            "DO NOT enter attics without roof egress hatches",
            "DO NOT touch wet electrical panels or submerged utility cables"
        ]
        escalation = "EMERGENCY_SERVICES"
    elif any(w in text_lower for w in ["pill", "dose", "medicine", "allergic", "reaction", "faint", "bleed"]):
        incident_type = "Medical / Pharmacological Alert"
        severity = "MODERATE"
        hazards = ["Medication toxicity or adverse drug interaction", "Allergic anaphylaxis risk", "Dosage misunderstanding"]
        actions = [
            "Hold suspected medication until verified by pharmacist or healthcare provider",
            "Gather all original medication bottles and containers for responder inspection",
            "Monitor patient airway, breathing, consciousness, and skin reactions"
        ]
        dnd = [
            "DO NOT administer unverified doses or guess handwritten numbers",
            "DO NOT induce vomiting unless explicitly directed by Poison Control",
            "DO NOT leave symptomatic patient unattended"
        ]
        escalation = "CONTACT_AUTHORITY"
    else:
        incident_type = "General Emergency Situation"
        severity = "MODERATE"
        hazards = ["Unidentified environmental or situational risks", "Fragmented caller information"]
        actions = [
            "Establish perimeter safety and ensure personal protection first",
            "Gather objective facts: who, what, where, and any casualties",
            "Contact relevant emergency authorities or municipal support"
        ]
        dnd = [
            "DO NOT enter unknown dangerous environments without proper gear",
            "DO NOT guess medical or technical procedures without qualification"
        ]
        escalation = "MONITOR"

    raw = {
        "incident_type": incident_type,
        "severity": severity,
        "summary": f"Situational assessment based on provided report: {text[:250]}..." if len(text) > 250 else (text or "Emergency input received."),
        "detected_hazards": hazards,
        "recommended_actions": actions,
        "do_not_do": dnd,
        "missing_information": ["Exact physical location coordinates", "Verified status of all persons involved", "Presence of specialized first responders"],
        "uncertainties": ["Report details received without direct sensor verification"],
        "confidence": 0.70,
        "escalation_required": escalation,
        "sources_or_evidence": [f"Caller textual statement: '{text[:80]}...'" if text else "Raw emergency input", f"Attachment: {filename}" if filename else "Direct report"]
    }
    return apply_deterministic_validation(raw, mode="fallback")
