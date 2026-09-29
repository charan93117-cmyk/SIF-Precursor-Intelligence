import re

import pandas as pd


ABBREVIATIONS = {
    "loto": "lockout tagout",
    "ptw": "permit to work",
    "ppe": "personal protective equipment",
    "lof": "line of fire",
}

# Narrow repairs for joined words observed in the synthetic templates.
TYPO_REPAIRS = {
    "nearthe": "near the",
    "noticednear": "noticed near",
    "supplyremained": "supply remained",
    "equipmentwhile": "equipment while",
    "withpersonnel": "with personnel",
    "werepresent": "were present",
    "controlto": "control to",
}


def clean_text(text):
    """Normalize a narrative without removing contextual punctuation."""
    if text is None or pd.isna(text):
        return ""

    text = str(text).lower()
    text = text.replace("\u2019", "'").replace("\u2018", "'")

    # Preserve the meaning of common negative contractions.
    text = re.sub(r"\bcan't\b", "cannot", text)
    text = re.sub(r"\bwon't\b", "will not", text)
    text = re.sub(r"\bshan't\b", "shall not", text)
    text = re.sub(r"\b([a-z]+)n't\b", r"\1 not", text)

    for abbreviation, replacement in ABBREVIATIONS.items():
        text = re.sub(
            rf"\b{re.escape(abbreviation)}\b",
            replacement,
            text,
        )

    for typo, replacement in TYPO_REPAIRS.items():
        text = re.sub(
            rf"\b{re.escape(typo)}\b",
            replacement,
            text,
        )

    return re.sub(r"\s+", " ", text).strip()


def preprocess_dataframe(df):
    """Return a copy with normalized text; preserve original columns."""
    if "free_text" not in df.columns:
        raise ValueError(
            "The dataframe must contain a 'free_text' column."
        )

    result = df.copy(deep=True)
    result["clean_text"] = result["free_text"].apply(clean_text)
    return result


def load_and_preprocess(csv_path):
    """Compatibility wrapper for loading and preprocessing a CSV."""
    # Keep categorical strings such as "None"; empty cells stay missing.
    df = pd.read_csv(
        csv_path,
        keep_default_na=False,
        na_values=[""],
    )
    return preprocess_dataframe(df)