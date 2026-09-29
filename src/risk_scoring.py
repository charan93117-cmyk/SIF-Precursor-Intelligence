"""Transparent heuristic risk scoring based on contextual evidence.

Risk scores are screening heuristics, not calibrated probabilities.
"""

import pandas as pd

if __package__:
    from .barrier_detection import detect_barrier_states
    from .safety_rules import (
        HIGH_RISK_INDICATORS,
        MAX_SCORE,
        RISK_THRESHOLDS,
        RISK_WEIGHTS,
    )
else:
    from barrier_detection import detect_barrier_states
    from safety_rules import (
        HIGH_RISK_INDICATORS,
        MAX_SCORE,
        RISK_THRESHOLDS,
        RISK_WEIGHTS,
    )


def _as_indicators(value):
    """Normalize the existing list/string indicator formats."""
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    if isinstance(value, (list, tuple, set)):
        return [str(part).strip() for part in value if str(part).strip()]
    return []


def _as_text(value):
    """Safely convert an optional field to text."""
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def detect_barrier_failure(text, barrier_states=None):
    """Return names of barriers explicitly classified as failed.

    Generic phrases such as "without incident" do not count as failures.
    """
    if not isinstance(text, str):
        text = ""

    states = (
        detect_barrier_states(text)
        if barrier_states is None
        else barrier_states
    )

    if not isinstance(states, list):
        return []

    return list(dict.fromkeys(
        state["barrier"]
        for state in states
        if isinstance(state, dict) and state.get("state") == "failed"
    ))


def calculate_risk(
    text,
    predicted_sif,
    sif_score,
    sif_indicators,
    extracted_hazard="",
    extracted_energy="",
    extracted_barrier="",
    barrier_states=None,
):
    """Calculate a bounded, explainable heuristic risk score.

    Existing positional arguments are preserved for compatibility.
    `sif_score` remains accepted but is not treated as a probability.
    """
    indicators = _as_indicators(sif_indicators)
    high_risk_matches = [
        indicator
        for indicator in indicators
        if indicator in HIGH_RISK_INDICATORS
    ]

    failures = detect_barrier_failure(text, barrier_states)
    factors = []
    score = 0

    if predicted_sif == "YES":
        score += RISK_WEIGHTS["sif_detected"]
        factors.append("Contextual SIF precursor flagged; review required")

    if high_risk_matches:
        score += RISK_WEIGHTS["high_risk_indicator"]
        factors.append("High-risk category: " + ", ".join(high_risk_matches))

    if _as_text(extracted_energy):
        score += RISK_WEIGHTS["hazardous_energy"]
        factors.append("Hazardous energy mentioned")

    if failures:
        score += RISK_WEIGHTS["barrier_failure"]
        factors.append("Reported failed barrier: " + ", ".join(failures))

    if len(set(indicators)) >= 2:
        score += RISK_WEIGHTS["multiple_indicators"]
        factors.append("Multiple contextual SIF categories")

    score = min(int(score), MAX_SCORE)

    risk_level = "LOW"
    for threshold, label in RISK_THRESHOLDS:
        if score >= threshold:
            risk_level = label
            break

    if high_risk_matches:
        primary_risk = high_risk_matches[0]
    elif _as_text(extracted_hazard):
        primary_risk = _as_text(extracted_hazard)
    else:
        primary_risk = "General Safety Observation"

    if factors:
        reason = "; ".join(factors)
    else:
        reason = (
            "No contextual risk trigger matched; "
            "this does not establish that conditions were safe."
        )

    return {
        "risk_score": score,
        "risk_level": risk_level,
        "primary_risk": primary_risk,
        "risk_factors": factors,
        "barrier_failures": failures,
        "risk_reason": reason,
    }


def apply_risk_scoring(df):
    """Add risk fields to a copy while retaining legacy output columns."""
    if "clean_text" not in df.columns and "free_text" not in df.columns:
        raise ValueError("Risk scoring requires free_text or clean_text.")

    result = df.copy(deep=True)
    text_column = "free_text" if "free_text" in result.columns else "clean_text"

    records = []
    for _, row in result.iterrows():
        states = row.get("barrier_states", None)
        if not isinstance(states, list):
            states = None

        records.append(calculate_risk(
            row.get(text_column, ""),
            row.get("predicted_sif", "NO"),
            row.get("sif_score", 0),
            row.get("sif_indicators", ""),
            row.get("extracted_hazard", ""),
            row.get("extracted_energy", ""),
            row.get("extracted_barrier", ""),
            states,
        ))

    for column in (
        "risk_score",
        "risk_level",
        "primary_risk",
        "risk_factors",
        "barrier_failures",
        "risk_reason",
    ):
        values = [record[column] for record in records]
        if column in {"risk_factors", "barrier_failures"}:
            values = [", ".join(value) for value in values]
        result[column] = pd.Series(values, index=result.index)

    return result


def load_and_score(file_path):
    """Compatibility wrapper for loading and scoring a CSV."""
    if __package__:
        from .sif_detector import load_and_detect
    else:
        from sif_detector import load_and_detect

    return apply_risk_scoring(load_and_detect(file_path))


if __name__ == "__main__":
    df = load_and_score("data/synthetic_reports.csv")
    print("Reports processed:", len(df))
    print(df["risk_level"].value_counts())
    print(df[[
        "report_id",
        "predicted_sif",
        "risk_score",
        "risk_level",
        "barrier_failures",
    ]].head(10).to_string(index=False))