"""Evidence-backed barrier states for the rule-based prototype."""

import re

import pandas as pd

if __package__:
    from .entity_extraction import extract_entity_evidence
    from .preprocessing import clean_text
else:
    from entity_extraction import extract_entity_evidence
    from preprocessing import clean_text


# Sentence/clause boundaries. Decimal points are not boundaries.
CLAUSE_BREAK = re.compile(
    r"(?<!\d)\.(?!\d)|[;!?\n,]|\b(?:but|however|whereas|and)\b",
    re.IGNORECASE,
)

UNCERTAIN = re.compile(
    r"\b(?:may|might|possibly|perhaps|unclear|uncertain|"
    r"not known|not clear|could not confirm)\b"
)

# A negated failure does not, by itself, prove an effective control.
NEGATED_FAILURE = re.compile(
    r"\b(?:not|never)\s+(?:been\s+)?"
    r"(?:missing|absent|bypassed|defeated|overridden)\b"
    r"|\bno\s+(?:evidence|sign)\s+of\b"
)

FAILURE = re.compile(
    r"\bwithout\b"
    r"|\bmissing\b|\babsent\b"
    r"|\b(?:not|did not|does not|was not|were not)\s+"
    r"(?:(?:properly|positively|adequately|yet|fully)\s+)?"
    r"(?:verify|verified|confirm|confirmed|complete|completed|"
    r"use|used|provide|provided|follow|followed|isolate|isolated|"
    r"connect|connected|attach|attached|active|in place|"
    r"separate|separated|issue|issued)\b"
    r"|\b(?:bypassed|defeated|overridden|disabled)\b"
    r"|\bfailed\b",
    re.IGNORECASE,
)

SUCCESS = re.compile(
    r"\b(?:verified|confirmed|completed|used|provided|"
    r"followed|isolated|restored|active|in place)\b"
)

# Detect unsafe sequencing such as:
# "Equipment was opened before LOTO verification was completed."
BEFORE_CONTROL = re.compile(
    r"\b(?:entered|entering|entry|opened|opening|accessed|"
    r"started|began|commenced)\b.*\bbefore\b"
)

CONTROL_COMPLETION = re.compile(
    r"\b(?:completed|verified|confirmed|verification|testing)\b"
)


def _clauses(text):
    """Yield original clause text and exact character offsets."""
    start = 0
    for boundary in CLAUSE_BREAK.finditer(text):
        end = boundary.start()
        raw = text[start:end]
        left = len(raw) - len(raw.lstrip())
        right = len(raw.rstrip())
        if right > left:
            yield text[start + left:start + right], start + left, start + right
        start = boundary.end()

    raw = text[start:]
    left = len(raw) - len(raw.lstrip())
    right = len(raw.rstrip())
    if right > left:
        yield text[start + left:start + right], start + left, start + right


def _classify_clause(clause):
    normalized = clean_text(clause)

    if UNCERTAIN.search(normalized):
        return "unknown", "BARRIER_UNCERTAIN", True

    if NEGATED_FAILURE.search(normalized):
        return "unknown", "BARRIER_NEGATED_FAILURE", True

    sequencing = BEFORE_CONTROL.search(normalized)
    if sequencing:
        following = normalized[sequencing.end():]
        if CONTROL_COMPLETION.search(following):
            return "failed", "BARRIER_UNSAFE_SEQUENCE", False

    failures = list(FAILURE.finditer(normalized))

    # Remove failure phrases before checking for successful-control words.
    # This prevents "not verified" from also counting as "verified".
    remaining = list(normalized)
    for match in failures:
        remaining[match.start():match.end()] = " " * (
            match.end() - match.start()
        )

    successful = bool(SUCCESS.search("".join(remaining)))

    if failures and successful:
        return "conflicting", "BARRIER_MIXED_STATE", True
    if failures:
        return "failed", "BARRIER_FAILURE", False
    if successful:
        return "effective", "BARRIER_REPORTED_EFFECTIVE", False

    return "unknown", "BARRIER_MENTION_ONLY", True


def detect_barrier_states(text, entity_evidence=None):
    """Return clause-level barrier observations, preserving event history.

    'Effective' means reported as effective in the narrative, not independently
    verified. Unknown or conflicting observations require human interpretation.
    """
    if not isinstance(text, str) or not text.strip():
        return []

    if entity_evidence is None:
        entity_evidence = extract_entity_evidence(text)

    observations = []

    for clause, start, end in _clauses(text):
        mentions = [
            item for item in entity_evidence
            if item["entity_type"] == "barrier"
            and start <= item["start"]
            and item["end"] <= end
        ]
        categories = sorted({item["category"] for item in mentions})
        if not categories:
            continue

        state, rule_id, needs_review = _classify_clause(clause)

        # Do not assign one clause's control state indiscriminately
        # when it contains several different barrier categories.
        if len(categories) > 1:
            state = "unknown"
            rule_id = "BARRIER_MULTIPLE_CONTROLS"
            needs_review = True

        for category in categories:
            observations.append({
                "barrier": category,
                "state": state,
                "text": clause,
                "start": start,
                "end": end,
                "rule_id": rule_id,
                "needs_review": needs_review,
            })

    return observations


def apply_barrier_detection(df):
    """Add barrier observations without modifying the input dataframe."""
    if "free_text" in df.columns:
        source_column = "free_text"
    elif "clean_text" in df.columns:
        source_column = "clean_text"
    else:
        raise ValueError(
            "Barrier detection requires free_text or clean_text."
        )

    result = df.copy(deep=True)
    records = [
        detect_barrier_states(text)
        for text in result[source_column].tolist()
    ]
    result["barrier_states"] = pd.Series(
        records, index=result.index, dtype=object
    )
    return result