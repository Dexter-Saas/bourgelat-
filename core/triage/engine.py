import os

MILD = float(os.getenv("MILD_THRESHOLD", 0.85))
MODERATE = float(os.getenv("MODERATE_THRESHOLD", 0.60))
CONFIDENCE = float(os.getenv("CONFIDENCE_THRESHOLD", 0.75))

def triage(confidence: float, severity_score: float) -> dict:
    if confidence < CONFIDENCE:
        return {
            "level": "inconclusive",
            "action": "escalate",
            "reason": "Low confidence - routing to vet"
        }
    if severity_score >= MILD:
        return {
            "level": "mild",
            "action": "home_remedy",
            "reason": "Mild symptoms detected"
        }
    elif severity_score >= MODERATE:
        return {
            "level": "moderate",
            "action": "medication",
            "reason": "Moderate symptoms detected"
        }
    else:
        return {
            "level": "severe",
            "action": "escalate",
            "reason": "Severe symptoms - vet required"
        }