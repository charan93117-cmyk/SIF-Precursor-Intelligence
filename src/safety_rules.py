"""Shared configuration for Phase 1 rule-based safety analysis.

Scores are heuristic values, not calibrated probabilities.
This module does not implement IOGP Life-Saving Rule predictions.
"""

RULESET_VERSION = "phase1-v1"

HIGH_RISK_INDICATORS = frozenset({
    "Electrical Energy",
    "Confined Space",
    "Working at Height",
    "Pressure",
    "Mechanical Energy",
    "Line of Fire",
    "Vehicle",
    "Hot Work",
    "Safety Control Bypass",
    "Work Authorization",
})

BARRIER_STATES = frozenset({
    "failed",
    "effective",
    "unknown",
    "conflicting",
})

ASSERTION_STATES = frozenset({
    "asserted",
    "negated",
    "uncertain",
})

# Existing numerical thresholds are preserved.
SIF_THRESHOLD = 60
MAX_SCORE = 100

RISK_THRESHOLDS = (
    (80, "CRITICAL"),
    (60, "HIGH"),
    (30, "MEDIUM"),
    (0, "LOW"),
)

# Existing risk weights. Contextual rules will determine whether
# each factor is actually supported by the narrative.
RISK_WEIGHTS = {
    "sif_detected": 40,
    "high_risk_indicator": 20,
    "hazardous_energy": 15,
    "barrier_failure": 15,
    "multiple_indicators": 10,
}