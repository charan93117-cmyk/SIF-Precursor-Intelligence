import pandas as pd
import re

# ============================================================
# SAFETY ENTITY KNOWLEDGE
# ============================================================

HAZARD_KEYWORDS = {
    "Electrical Energy": [
        "electrical",
        "energized",
        "electric shock",
        "live equipment"
    ],

    "Fire": [
        "fire",
        "flame",
        "ignition",
        "smoke"
    ],

    "Working at Height": [
        "height",
        "fall",
        "ladder",
        "scaffold"
    ],

    "Confined Space": [
        "confined space",
        "tank entry",
        "vessel entry"
    ],

    "Vehicle": [
        "vehicle",
        "truck",
        "crane",
        "forklift"
    ],

    "Pressure": [
        "pressure",
        "pressurized",
        "pressure release"
    ],

    "Chemical": [
        "chemical",
        "toxic",
        "chemical exposure"
    ],

    "Line of Fire": [
        "line of fire",
        "struck by",
        "caught between"
    ],

    "Material Obstruction": [
        "obstruction",
        "blocked",
        "material obstruction"
    ],

    "Housekeeping": [
        "housekeeping",
        "oil stain",
        "spill"
    ]
}


ENERGY_KEYWORDS = {
    "Electrical Energy": [
        "electrical",
        "energized",
        "electric"
    ],

    "Pressure Energy": [
        "pressure",
        "pressurized",
        "pressure release"
    ],

    "Mechanical Energy": [
        "mechanical",
        "moving equipment",
        "rotating"
    ],

    "Chemical Energy": [
        "chemical",
        "toxic"
    ],

    "Gravity": [
        "height",
        "fall",
        "dropped object"
    ]
}


BARRIER_KEYWORDS = {
    "Lockout Tagout": [
        "lockout",
        "tagout",
        "isolation",
        "isolated"
    ],

    "Permit to Work": [
        "permit",
        "ptw",
        "permit to work"
    ],

    "Personal Protective Equipment": [
        "ppe",
        "protective equipment",
        "helmet",
        "gloves"
    ],

    "Housekeeping Control": [
        "housekeeping",
        "obstruction",
        "material",
        "spill",
        "oil stain"
    ],

    "Fire Control": [
        "fire",
        "ignition",
        "hot work"
    ]
}


# ============================================================
# FIND KEYWORD MATCHES
# ============================================================

# Extend barrier coverage while retaining the existing categories.
BARRIER_KEYWORDS.update({
    "Gas Testing": [
        "gas testing", "gas test", "gas detector",
        "atmospheric testing", "atmosphere testing",
        "oxygen levels",
    ],
    "Fall Protection": [
        "fall protection", "harness", "lanyard",
        "guardrail", "guardrails", "edge protection",
    ],
    "Barricading": [
        "barricade", "barricades", "barricading",
        "exclusion zone", "drop zone",
    ],
    "Vehicle Separation": [
        "pedestrian control", "separation",
        "vehicle routes", "pedestrian routes",
    ],
    "Safety Interlock": [
        "interlock", "safety control", "protective control",
    ],
})

# Evidence is matched against original text, which may use abbreviations.
# Existing dictionary categories and legacy output formats are retained.
ENTITY_ALIASES = {
    ("barrier", "Lockout Tagout"): ["loto", "lockout tagout"],
    ("barrier", "Permit to Work"): [
    "ptw",
    "work authorization",
    "authorization requirements",
    "authorization",
    "authorisation",
],
    ("barrier", "Personal Protective Equipment"): ["ppe"],
    ("hazard", "Line of Fire"): ["lof"],
}


def _phrase_pattern(phrase):
    """Match a phrase at word boundaries, allowing flexible whitespace."""
    words = phrase.split()
    body = r"\s+".join(re.escape(word) for word in words)
    return re.compile(r"(?<!\w)" + body + r"(?!\w)", re.IGNORECASE)


def find_matches(text, keyword_dictionary):
    """Return matching categories in dictionary order."""
    if not isinstance(text, str):
        return []

    return [
        category
        for category, keywords in keyword_dictionary.items()
        if any(_phrase_pattern(keyword).search(text) for keyword in keywords)
    ]


def extract_entity_evidence(text):
    """Return exact entity spans in the supplied original narrative.

    Assertion is initially uncertain: this lexical stage detects mentions.
    Contextual analysis must determine negation, exposure and control state.
    Offsets are Python string character offsets; end is exclusive.
    """
    if not isinstance(text, str) or not text:
        return []

    evidence = []
    dictionaries = (
        ("hazard", HAZARD_KEYWORDS),
        ("energy", ENERGY_KEYWORDS),
        ("barrier", BARRIER_KEYWORDS),
    )

    for entity_type, dictionary in dictionaries:
        for category, keywords in dictionary.items():
            phrases = list(keywords) + ENTITY_ALIASES.get(
                (entity_type, category), []
            )
            candidates = {}

            for phrase in phrases:
                for match in _phrase_pattern(phrase).finditer(text):
                    key = (match.start(), match.end())
                    candidates[key] = {
                        "entity_type": entity_type,
                        "category": category,
                        "text": text[match.start():match.end()],
                        "start": match.start(),
                        "end": match.end(),
                        "assertion": "uncertain",
                        "rule_id": "ENTITY_PHRASE_MATCH",
                    }

            # Prefer a complete phrase over its overlapping shorter alias,
            # within the same entity type and category.
            selected = []
            for item in sorted(
                candidates.values(),
                key=lambda item: (
                    -(item["end"] - item["start"]),
                    item["start"],
                ),
            ):
                if not any(
                    item["start"] < other["end"]
                    and other["start"] < item["end"]
                    for other in selected
                ):
                    selected.append(item)

            evidence.extend(selected)

    return sorted(
        evidence,
        key=lambda item: (
            item["start"], item["end"],
            item["entity_type"], item["category"],
        ),
    )


def extract_entities(text):
    """Preserve legacy category lists and add structured evidence."""
    if not isinstance(text, str):
        text = ""

    evidence = extract_entity_evidence(text)

    def categories(entity_type, dictionary):
        found = {
            item["category"]
            for item in evidence
            if item["entity_type"] == entity_type
        }
        return [category for category in dictionary if category in found]

    return {
        "hazards": categories("hazard", HAZARD_KEYWORDS),
        "energy": categories("energy", ENERGY_KEYWORDS),
        "barriers": categories("barrier", BARRIER_KEYWORDS),
        "evidence": evidence,
    }


def extract_from_dataframe(df):
    """Add extraction columns without changing input rows or source text."""
    if "clean_text" not in df.columns:
        raise ValueError(
            "Entity extraction requires a 'clean_text' column. "
            "Run preprocessing first."
        )

    result = df.copy(deep=True)

    # Prefer original text so evidence offsets remain valid for display.
    # Keep clean_text-only callers supported.
    source_column = "free_text" if "free_text" in result.columns else "clean_text"
    records = [
        extract_entities(text)
        for text in result[source_column].tolist()
    ]

    result["extracted_hazard"] = [
        ", ".join(record["hazards"]) for record in records
    ]
    result["extracted_energy"] = [
        ", ".join(record["energy"]) for record in records
    ]
    result["extracted_barrier"] = [
        ", ".join(record["barriers"]) for record in records
    ]
    result["entity_evidence"] = pd.Series(
        [record["evidence"] for record in records],
        index=result.index,
        dtype=object,
    )

    return result


# ============================================================
# EXTRACT ENTITIES FROM ONE REPORT
# ============================================================


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    from preprocessing import load_and_preprocess

    file_path = "data/synthetic_reports.csv"

    df = load_and_preprocess(file_path)

    df = extract_from_dataframe(df)

    print("=" * 70)
    print("ENTITY EXTRACTION TEST")
    print("=" * 70)

    print()
    print("Reports processed:", len(df))

    print()
    print("Extracted entities:")
    print()

    for _, row in df.head(10).iterrows():

        print("Report ID:", row["report_id"])
        print("Text:", row["free_text"])
        print("Hazard:", row["extracted_hazard"])
        print("Energy:", row["extracted_energy"])
        print("Barrier:", row["extracted_barrier"])

        print("-" * 70)