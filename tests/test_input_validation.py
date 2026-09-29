import unittest
from io import StringIO

import pandas as pd

from src.input_validation import (
    read_reports_csv,
    validate_reports,
    validate_sif_labels,
)


def valid_reports():
    return pd.DataFrame({
        "report_id": ["001", "002"],
        "date": ["2025-01-02", "2025-02-03"],
        "site": ["Site A", "Site B"],
        "location": ["Workshop", "Tank area"],
        "activity": ["Maintenance", "Inspection"],
        "report_type": ["Unsafe Condition", "Near Miss"],
        "free_text": ["Isolation was missing.", "Inspection completed."],
    })


class TestInputValidation(unittest.TestCase):

    def test_valid_reports_without_labels(self):
        result = validate_reports(valid_reports())
        self.assertTrue(result.is_valid)
        self.assertEqual(result.warnings, [])

    def test_missing_required_column(self):
        df = valid_reports().drop(columns=["site"])
        result = validate_reports(df)
        self.assertFalse(result.is_valid)
        self.assertIn("site", " ".join(result.errors))

    def test_empty_dataset(self):
        result = validate_reports(valid_reports().iloc[:0])
        self.assertFalse(result.is_valid)

    def test_blank_report_id(self):
        df = valid_reports()
        df.loc[0, "report_id"] = " "
        self.assertFalse(validate_reports(df).is_valid)

    def test_duplicate_ids_after_trimming(self):
        df = valid_reports()
        df["report_id"] = ["001", " 001 "]
        result = validate_reports(df)
        self.assertFalse(result.is_valid)
        self.assertIn("Duplicate", " ".join(result.errors))

    def test_invalid_narratives(self):
        for value in ("", "   ", None, 123):
            with self.subTest(value=value):
                df = valid_reports()
                df["free_text"] = pd.Series(
                    [value, "Inspection completed."], dtype=object
                )
                self.assertFalse(validate_reports(df).is_valid)

    def test_invalid_dates(self):
        for value in ("2025-02-30", "03/04/2025", "not a date"):
            with self.subTest(value=value):
                df = valid_reports()
                df.loc[0, "date"] = value
                self.assertFalse(validate_reports(df).is_valid)

    def test_blank_metadata_warns_without_rejecting(self):
        for column in ("date", "site", "location", "activity", "report_type"):
            with self.subTest(column=column):
                df = valid_reports()
                df.loc[0, column] = ""
                result = validate_reports(df)
                self.assertTrue(result.is_valid)
                self.assertIn(column, " ".join(result.warnings))

    def test_incident_is_accepted(self):
        df = valid_reports()
        df.loc[0, "report_type"] = "Incident"
        result = validate_reports(df)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.warnings, [])

    def test_unknown_report_type_warns(self):
        df = valid_reports()
        df.loc[0, "report_type"] = "Other Observation"
        result = validate_reports(df)
        self.assertTrue(result.is_valid)
        self.assertTrue(result.warnings)

    def test_input_and_extra_columns_unchanged(self):
        df = valid_reports()
        df["extra_notes"] = ["Keep this", "Keep that"]
        snapshot = df.copy(deep=True)
        validate_reports(df)
        pd.testing.assert_frame_equal(df, snapshot)

    def test_invalid_reference_labels_only_warn_for_inference(self):
        df = valid_reports()
        df["ground_truth_sif"] = ["YES", "UNKNOWN"]
        result = validate_reports(df)
        self.assertTrue(result.is_valid)
        self.assertTrue(result.warnings)

    def test_label_normalization_does_not_mutate_input(self):
        labels = pd.Series([" yes ", "no"])
        snapshot = labels.copy()
        normalized = validate_sif_labels(labels)
        self.assertEqual(normalized.tolist(), ["YES", "NO"])
        pd.testing.assert_series_equal(labels, snapshot)

    def test_invalid_labels_block_evaluation(self):
        for labels in (
            pd.Series(["YES", "UNKNOWN"]),
            pd.Series(["YES", None]),
            pd.Series([], dtype=str),
        ):
            with self.subTest(labels=labels.tolist()):
                with self.assertRaises(ValueError):
                    validate_sif_labels(labels)

    def test_csv_preserves_ids_and_none(self):
        csv = StringIO(
            "report_id,free_text,ground_truth_energy\n"
            "001,Inspection completed.,None\n"
        )
        df = read_reports_csv(csv)
        self.assertEqual(df.loc[0, "report_id"], "001")
        self.assertEqual(df.loc[0, "ground_truth_energy"], "None")

    def test_csv_bytes_supported(self):
        df = read_reports_csv(b"report_id,free_text\n001,Inspection\n")
        self.assertEqual(df.loc[0, "report_id"], "001")

    def test_malformed_csv_rejected(self):
        with self.assertRaises(ValueError):
            read_reports_csv(StringIO('report_id,free_text\n001,"unfinished'))

    def test_empty_csv_rejected(self):
        with self.assertRaises(ValueError):
            read_reports_csv(b"")

    def test_duplicate_dataframe_columns_rejected(self):
        df = valid_reports()
        df = pd.concat([df, df[["site"]]], axis=1)
        self.assertFalse(validate_reports(df).is_valid)

    def test_raise_for_errors(self):
        result = validate_reports(valid_reports().drop(columns=["site"]))
        with self.assertRaises(ValueError):
            result.raise_for_errors()


if __name__ == "__main__":
    unittest.main()