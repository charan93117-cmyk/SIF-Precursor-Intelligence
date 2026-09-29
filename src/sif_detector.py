"""Contextual, rule-based SIF screening.

Predictions are screening outputs, not HSE verification.
Scores are heuristic values, not calibrated probabilities.
"""

import re

import pandas as pd

if __package__:
    from .barrier_detection import detect_barrier_states, _clauses
    from .preprocessing import clean_text, load_and_preprocess
    from .entity_extraction import extract_from_dataframe
    from .safety_rules import HIGH_RISK_INDICATORS, SIF_THRESHOLD
else:
    from barrier_detection import detect_barrier_states, _clauses
    from preprocessing import clean_text, load_and_preprocess
    from entity_extraction import extract_from_dataframe
    from safety_rules import HIGH_RISK_INDICATORS, SIF_THRESHOLD


# A failed barrier needs relevant activity/exposure context.
# These are screening categories, not predicted IOGP rules.
BARRIER_CONTEXT = {
    "Lockout Tagout": (
        "Electrical Energy",
        r"\b(?:maintenance|equipment|electrical|panel|energy|"
        r"opening|opened|isolation|loto|lockout)\b",
    ),
    "Gas Testing": (
        "Confined Space",
        r"\b(?:entry|entering|entered|entrant|tank|vessel|confined)\b",
    ),
    "Fall Protection": (
        "Working at Height",
        r"\b(?:height|elevated|edge|scaffold|ladder|roof|platform)\b",
    ),
    "Barricading": (
        "Line of Fire",
        r"\b(?:lifting|lifted|load|crane|moving|machinery|drop zone)\b",
    ),
    "Vehicle Separation": (
        "Vehicle",
        r"\b(?:vehicle|pedestrian|truck|forklift|reversing|reversed)\b",
    ),
    "Safety Interlock": (
        "Safety Control Bypass",
        r"\b(?:equipment|machine|machinery|operation|operating|"
        r"production|interlock)\b",
    ),
    "Permit to Work": (
        "Work Authorization",
       r"\b(?:work|working|maintenance|entry|operation|activity|"
       r"task|pipeline|commenced|started)\b",
    ),
    "Fire Control": (
        "Hot Work",
        r"\b(?:hot work|welding|cutting|grinding)\b",
    ),
}

# Direct exposure can support a flag even without a named failed barrier.
EXPOSURE_RULES = (
    (
        "EXPOSURE_LIVE_CONTACT",
        "Electrical Energy",
        r"\b(?:contacted|touching|touched|contact with)\b.{0,70}"
        r"\b(?:energized|live|electrical)\b",
    ),
    (
        "EXPOSURE_CONNECTED_ENERGY",
        "Electrical Energy",
        r"\b(?:supply|power|energy source)\b.{0,35}"
        r"\bremained connected\b",
    ),
    (
        "EXPOSURE_MOVING_MACHINERY",
        "Mechanical Energy",
        r"\b(?:worker|person|technician|personnel|hands)\b.{0,90}"
        r"\b(?:near|close to|danger zone)\b.{0,45}"
        r"\b(?:moving|rotating|active)\b",
    ),
    (
        "EXPOSURE_SUSPENDED_LOAD",
        "Line of Fire",
        r"\b(?:beneath|under)\b.{0,30}\bsuspended\b"
        r"|\b(?:worker|personnel|person)\b.{0,65}"
        r"\b(?:drop zone|exclusion zone|swing area)\b.{0,65}"
        r"\b(?:load|lifting|suspended|crane)\b",
    ),
    (
        "EXPOSURE_UNPROTECTED_EDGE",
        "Working at Height",
        r"\b(?:worker|technician|employee|personnel)\b.{0,80}"
        r"\b(?:unprotected|unguarded)\s+edge\b",
    ),
    (
        "EXPOSURE_VEHICLE_PATH",
        "Vehicle",
        r"\b(?:worker|pedestrian|personnel)\b.{0,60}"
        r"\b(?:entered|within|in)\b.{0,35}"
        r"\bvehicle\s+(?:movement path|operating zone)\b",
    ),
    (
        "EXPOSURE_LINE_OF_FIRE",
        "Line of Fire",
        r"\b(?:line of fire|danger zone|swing area|"
        r"lifting exclusion zone|potential line of fire)\b",
    ),
    (
        "EXPOSURE_MECHANICAL_ENERGY",
        "Mechanical Energy",
        r"\b(?:stored mechanical energy|moving components|"
        r"active machine|moving mechanical equipment)\b",
    ),
    (
        "EXPOSURE_HOT_WORK",
        "Hot Work",
        r"\b(?:welding|grinding|hot work|sparks)\b.{0,100}"
        r"\b(?:without|not|before|combustible|controls|"
        r"permit|authorization|gas testing)\b"
        r"|\b(?:without|not|before)\b.{0,80}"
        r"\b(?:welding|grinding|hot work|permit|authorization|"
        r"gas testing)\b",
    ),
    (
        "EXPOSURE_HEIGHT",
        "Working at Height",
        r"\b(?:working at height|elevated structure|open edge|"
        r"unprotected edge|fall arrest equipment|safety harness|"
        r"lanyard)\b.{0,80}"
        r"\b(?:without|not|missing|unprotected|unconnected|"
        r"near|attached)\b"
        r"|\b(?:without|not|missing|unprotected|unconnected|"
        r"attached)\b.{0,80}"
        r"\b(?:fall protection|harness|lanyard|edge)\b",
    ),
    (
        "EXPOSURE_CONFINED_ENTRY",
        "Confined Space",
        r"\b(?:confined space|tank|vessel|atmosphere|oxygen levels)"
        r"\b.{0,100}"
        r"\b(?:without|not|before|incomplete|unconfirmed|"
        r"unverified|hazardous)\b"
        r"|\b(?:without|not|before|incomplete|unconfirmed|"
        r"unverified|hazardous)\b.{0,100}"
        r"\b(?:gas testing|gas test|atmosphere|oxygen|"
        r"entry|tank|vessel)\b",
    ),
    (
        "EXPOSURE_LIFTING",
        "Line of Fire",
        r"\b(?:suspended load|suspended component|"
        r"load was being lifted|drop zone|lifting exclusion zone|"
        r"crane operation)\b"
        r"|\b(?:worker|personnel|person|pedestrian)\b.{0,80}"
        r"\b(?:beneath|under|inside|within|close to|near|entered)"
        r"\b.{0,50}\b(?:load|lifting|crane|zone|component)\b",
    ),
    (
        "EXPOSURE_VEHICLE_INTERACTION",
        "Vehicle",
        r"\b(?:pedestrian walked close to a moving vehicle|"
        r"vehicle reversed while personnel|vehicle movement path|"
        r"vehicle operating zone|vehicle routes|pedestrian routes|"
        r"vehicle moved through an area occupied by pedestrians|"
        r"moving vehicle during site movement)\b",
    ),
    (
        "EXPOSURE_BYPASS",
        "Safety Control Bypass",
        r"\b(?:bypassed|overridden|defeated|not active|"
        r"not operational)\b.{0,80}"
        r"\b(?:safety|control|interlock|protection|equipment|"
        r"production)\b"
        r"|\b(?:safety|control|interlock|protection)\b.{0,80}"
        r"\b(?:bypassed|overridden|defeated|not active)\b",
    ),
    (
        "EXPOSURE_UNAUTHORIZED_WORK",
        "Work Authorization",
        r"\b(?:work|maintenance|pipeline work|task|activity)\b"
        r".{0,90}"
        r"\b(?:without|before|not issued|missing|not completed|"
        r"not approved)\b.{0,60}"
        r"\b(?:permit|authorization|approval|requirements)\b"
        r"|\b(?:without|before|missing|not issued|not approved)\b"
        r".{0,70}\b(?:permit|authorization|approval)\b",
    ),
)

ADDITIONAL_EXPOSURE_RULES = (
    (
        "EXPOSURE_UNATTACHED_HARNESS_AT_HEIGHT",
        "Working at Height",
        r"\bnot attached\b.{0,60}\bworking at height\b",
    ),
)

UNCERTAIN_EXPOSURE = re.compile(
    r"\b(?:may|might|possibly|perhaps|hypothetical|"
    r"training|simulation|drill|if)\b"
)

NEGATED_EXPOSURE = re.compile(
    r"\b(?:no|never)\s+"
    r"(?:fire|ignition|workers?|personnel|pedestrians|exposure|contact)\b"
    r"|\bnot exposed\b"
    r"|\bnot in (?:the )?"
    r"(?:line of fire|danger zone|vehicle path|drop zone)\b",
    re.IGNORECASE,
)

HAZARD_MENTION = re.compile(
    r"\b(?:electrical|energized|pressure|confined|tank|vessel|"
    r"height|scaffold|ladder|lifting|suspended|vehicle|"
    r"machinery|hot work|welding|fire|ignition)\b"
)


def detect_sif(
    text,
    extracted_hazard="",
    extracted_energy="",
    *,
    barrier_states=None,
):
    """Preserve legacy arguments and return evidence-backed screening."""
    if not isinstance(text, str):
        text = ""

    states = (
        detect_barrier_states(text)
        if barrier_states is None
        else barrier_states
    )
    evidence = []
    notes = []
    needs_review = any(item["needs_review"] for item in states)

    for item in states:
        if item["state"] == "conflicting":
            notes.append("Conflicting barrier statements require review.")
            continue

        if item["state"] != "failed":
            continue

        context_rule = BARRIER_CONTEXT.get(item["barrier"])
        if context_rule is None:
            needs_review = True
            notes.append(
                f"Reported failure of {item['barrier']} needs "
                "additional SIF context."
            )
            continue

        category, context_pattern = context_rule
        if re.search(context_pattern, clean_text(item["text"])):
            evidence.append({
                "category": category,
                "barrier": item["barrier"],
                "text": item["text"],
                "start": item["start"],
                "end": item["end"],
                "rule_id": item["rule_id"],
            })
        else:
            needs_review = True
            notes.append(
                f"{item['barrier']} failure found, but relevant "
                "exposure/activity context is insufficient."
            )

    for clause, start, end in _clauses(text):
        normalized = clean_text(clause)
        
        for rule_id, category, pattern in (
            EXPOSURE_RULES + ADDITIONAL_EXPOSURE_RULES
            ):
            if not re.search(pattern, normalized):
                continue

            related_barrier = {
                "Confined Space": "Gas Testing",
                "Working at Height": "Fall Protection",
                "Safety Control Bypass": "Safety Interlock",
            }.get(category)

            related_states = [
                state for state in states
                if state["barrier"] == related_barrier
                and state["start"] >= start
                and state["end"] <= end
            ] if related_barrier else []

            # A completed or uncertain control does not support
            # an unsafe-exposure trigger in the same clause.
            if related_states and not any(
                state["state"] == "failed"
                for state in related_states
            ):
                if any(
                    state["state"] in {"unknown", "conflicting"}
                    for state in related_states
                ):
                    needs_review = True
                continue

            if (
                UNCERTAIN_EXPOSURE.search(normalized)
                or NEGATED_EXPOSURE.search(normalized)
            ):
                needs_review = True
                notes.append(
                    "An exposure-like phrase was uncertain or negated; "
                    "it was not used as positive evidence."
                )
                continue

            evidence.append({
                "category": category,
                "barrier": None,
                "text": clause,
                "start": start,
                "end": end,
                "rule_id": rule_id,
            })
    # Stable ordering, without duplicate scoring for the same category.
    indicators = list(dict.fromkeys(
        item["category"] for item in evidence
    ))

    score = 0
    if indicators:
        score = 60 if len(indicators) == 1 else 80

    prediction = "YES" if score >= SIF_THRESHOLD else "NO"

    if not evidence:
        normalized = clean_text(text)
        if HAZARD_MENTION.search(normalized) and not states:
            needs_review = True
            notes.append(
                "Hazard-related wording was found without enough "
                "contextual evidence for a positive SIF flag."
            )
        notes.append(
            "No contextual SIF trigger matched; this does not establish safety."
        )
    else:
        notes.append(
            "Potential SIF precursor flagged by contextual rules; "
            "human review is required."
        )
        needs_review = True

    return {
        "sif_prediction": prediction,
        "sif_score": score,
        "sif_indicators": indicators,
        "sif_evidence": evidence,
        "barrier_states": states,
        "needs_review": needs_review,
        "assessment_notes": list(dict.fromkeys(notes)),
    }


def apply_sif_detection(df):
    """Add predictions while preserving input rows and legacy columns."""
    if "clean_text" not in df.columns:
        raise ValueError("SIF detection requires clean_text.")

    result = df.copy(deep=True)
    source = "free_text" if "free_text" in result.columns else "clean_text"

    records = [
        detect_sif(text)
        for text in result[source].tolist()
    ]

    result["predicted_sif"] = [
        item["sif_prediction"] for item in records
    ]
    result["sif_score"] = [
        item["sif_score"] for item in records
    ]
    result["sif_indicators"] = [
        ", ".join(item["sif_indicators"]) for item in records
    ]

    for column in (
        "sif_evidence",
        "barrier_states",
        "assessment_notes",
    ):
        result[column] = pd.Series(
            [item[column] for item in records],
            index=result.index,
            dtype=object,
        )

    result["needs_review"] = pd.Series(
        [item["needs_review"] for item in records],
        index=result.index,
        dtype=bool,
    )
    return result


def load_and_detect(file_path):
    """Compatibility wrapper: preprocessing, extraction, then detection."""
    df = load_and_preprocess(file_path)
    df = extract_from_dataframe(df)
    return apply_sif_detection(df)