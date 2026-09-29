import pandas as pd
from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    accuracy_score
)

from preprocessing import load_and_preprocess
from entity_extraction import extract_from_dataframe
from sif_detector import apply_sif_detection


print("=" * 70)
print("SIF PRECURSOR DETECTOR EVALUATION")
print("=" * 70)

# ------------------------------------------------------------
# LOAD AND PROCESS DATA
# ------------------------------------------------------------

file_path = "data/synthetic_reports.csv"

print("\nLoading reports...")

df = load_and_preprocess(file_path)

print("Reports loaded:", len(df))

# Entity extraction
df = extract_from_dataframe(df)

# SIF detection
df = apply_sif_detection(df)


# ------------------------------------------------------------
# CONVERT LABELS
# ------------------------------------------------------------

y_true = df["ground_truth_sif"].map({
    "NO": 0,
    "YES": 1
})

y_pred = df["predicted_sif"].map({
    "NO": 0,
    "YES": 1
})


# ------------------------------------------------------------
# CONFUSION MATRIX
# ------------------------------------------------------------

cm = confusion_matrix(y_true, y_pred)

tn, fp, fn, tp = cm.ravel()


print("\n" + "=" * 70)
print("DATASET SUMMARY")
print("=" * 70)

print("Total reports:", len(df))

print("\nActual SIF:")
print(df["ground_truth_sif"].value_counts())

print("\nPredicted SIF:")
print(df["predicted_sif"].value_counts())


# ------------------------------------------------------------
# CONFUSION MATRIX RESULTS
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("CONFUSION MATRIX")
print("=" * 70)

print()
print("                 PREDICTED")
print("                 NO       YES")
print()
print(f"ACTUAL NO       {tn:<8} {fp}")
print(f"ACTUAL YES      {fn:<8} {tp}")


print("\nTrue Negatives :", tn)
print("False Positives:", fp)
print("False Negatives:", fn)
print("True Positives :", tp)


# ------------------------------------------------------------
# PERFORMANCE
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("PERFORMANCE")
print("=" * 70)

accuracy = accuracy_score(y_true, y_pred)

print("\nAccuracy:", round(accuracy, 4))

print("\nClassification Report:")

print(
    classification_report(
        y_true,
        y_pred,
        target_names=["NO SIF", "SIF"],
        zero_division=0
    )
)


# ------------------------------------------------------------
# MISSED SIF REPORTS
# ------------------------------------------------------------

missed = df[
    (df["ground_truth_sif"] == "YES") &
    (df["predicted_sif"] == "NO")
]

print("\n" + "=" * 70)
print("MISSED SIF REPORTS")
print("=" * 70)

print("\nNumber of missed SIF reports:", len(missed))

for _, row in missed.iterrows():

    print("\nReport ID:", row["report_id"])
    print("Text:", row["free_text"])
    print("Hazard:", row["extracted_hazard"])
    print("Energy:", row["extracted_energy"])
    print("Score:", row["sif_score"])
    print("Indicators:", row["sif_indicators"])


print("\n" + "=" * 70)
print("EVALUATION COMPLETE")
print("=" * 70)