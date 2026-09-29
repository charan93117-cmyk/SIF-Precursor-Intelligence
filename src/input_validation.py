"""Read report CSVs and validate inputs without modifying source data."""

from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
import re

import pandas as pd


REQUIRED_COLUMNS = (
    "report_id",
    "date",
    "site",
    "location",
    "activity",
    "report_type",
    "free_text",
)

KNOWN_REPORT_TYPES = {
    "unsafe act",
    "unsafe condition",
    "near miss",
    "incident",
}


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self):
        return not self.errors

    def raise_for_errors(self):
        if self.errors:
            raise ValueError("\n".join(self.errors))


def _blank(value):
    if isinstance(value, str):
        return not value.strip()
    return bool(pd.isna(value))


def _row_numbers(mask):
    """Return CSV row numbers, counting the header as row 1."""
    return ", ".join(
        str(position + 2)
        for position, flagged in enumerate(mask)
        if flagged
    )


def read_reports_csv(source):
    """Read CSV bytes, a path, or a file-like object.

    Read values as strings to preserve IDs such as 001 and literal None.
    Empty cells are represented as missing values.
    """
    if isinstance(source, bytes):
        source = BytesIO(source)

    if not isinstance(source, (str, Path)) and not hasattr(source, "read"):
        raise TypeError("CSV input must be bytes, a path, or a file-like object.")

    try:
        return pd.read_csv(
            source,
            dtype=str,
            encoding="utf-8-sig",
            keep_default_na=False,
            na_values=[""],
            on_bad_lines="error",
        )
    except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeError) as exc:
        raise ValueError(f"Could not parse reports CSV: {exc}") from exc


def validate_sif_labels(labels):
    """Return normalized YES/NO labels for evaluation only.

    The input series is never modified. Missing or invalid labels block
    evaluation rather than being silently excluded.
    """
    if len(labels) == 0:
        raise ValueError("Cannot evaluate an empty label series.")

    normalized = labels.astype("string").str.strip().str.upper()
    invalid = ~normalized.isin(["YES", "NO"])

    if invalid.any():
        raise ValueError(
            "SIF labels must be YES or NO. Invalid or missing labels at "
            f"CSV rows: {_row_numbers(invalid)}."
        )

    return normalized


def validate_reports(df):
    """Return errors and warnings without changing the input dataframe."""
    result = ValidationResult()

    if not isinstance(df, pd.DataFrame):
        result.errors.append("Reports must be provided as a pandas dataframe.")
        return result

    if df.columns.duplicated().any():
        result.errors.append("Duplicate column names are not allowed.")
        return result

    missing = [name for name in REQUIRED_COLUMNS if name not in df.columns]
    if missing:
        result.errors.append(
            "Missing required columns: " + ", ".join(missing) + "."
        )

    if df.empty:
        result.errors.append("The report dataset is empty.")

    if result.errors:
        return result

    ids = df["report_id"]
    blank_ids = ids.map(_blank)
    if blank_ids.any():
        result.errors.append(
            f"Blank report IDs at CSV rows: {_row_numbers(blank_ids)}."
        )

    # Compare trimmed IDs, but leave the original values untouched.
    normalized_ids = ids.astype("string").str.strip()
    duplicates = normalized_ids.duplicated(keep=False) & ~blank_ids
    if duplicates.any():
        result.errors.append(
            f"Duplicate report IDs at CSV rows: {_row_numbers(duplicates)}."
        )

    invalid_text = df["free_text"].map(
        lambda value: not isinstance(value, str) or not value.strip()
    )
    if invalid_text.any():
        result.errors.append(
            "Narratives must be nonblank text. Invalid narratives at "
            f"CSV rows: {_row_numbers(invalid_text)}."
        )

    for column in ("date", "site", "location", "activity", "report_type"):
        blank = df[column].map(_blank)
        if blank.any():
            result.warnings.append(
                f"Missing {column} at CSV rows: {_row_numbers(blank)}."
            )

    dates = df["date"]
    blank_dates = dates.map(_blank)
    date_text = dates.astype("string").str.strip()
    iso_format = date_text.str.fullmatch(r"\d{4}-\d{2}-\d{2}", na=False)
    parsed = pd.to_datetime(
        date_text.where(iso_format),
        format="%Y-%m-%d",
        errors="coerce",
    )
    invalid_dates = ~blank_dates & (~iso_format | parsed.isna())
    if invalid_dates.any():
        result.errors.append(
            "Dates must be valid YYYY-MM-DD values. Invalid dates at "
            f"CSV rows: {_row_numbers(invalid_dates)}."
        )

    report_types = df["report_type"].astype("string").str.strip().str.lower()
    unknown_types = (
        ~df["report_type"].map(_blank)
        & ~report_types.isin(KNOWN_REPORT_TYPES)
    )
    if unknown_types.any():
        result.warnings.append(
            "Unrecognized report types preserved at CSV rows: "
            f"{_row_numbers(unknown_types)}."
        )

    if "ground_truth_sif" in df.columns:
        try:
            validate_sif_labels(df["ground_truth_sif"])
        except ValueError as exc:
            result.warnings.append(
                f"SIF evaluation unavailable: {exc}"
            )

    return result