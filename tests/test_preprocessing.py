import unittest
from io import StringIO

import pandas as pd

from src.preprocessing import (
    clean_text,
    load_and_preprocess,
    preprocess_dataframe,
)


class TestPreprocessing(unittest.TestCase):

    def test_whole_word_abbreviations(self):
        self.assertEqual(
            clean_text("LOTO PTW PPE LOF"),
            "lockout tagout permit to work "
            "personal protective equipment line of fire",
        )

    def test_embedded_letters_unchanged(self):
        self.assertEqual(
            clean_text("stopped supplies aloft"),
            "stopped supplies aloft",
        )

    def test_negation_preserved(self):
        self.assertEqual(
            clean_text("Isolation wasn’t verified."),
            "isolation was not verified.",
        )
        self.assertEqual(
            clean_text("No fire was present."),
            "no fire was present.",
        )

    def test_punctuation_and_numbers_preserved(self):
        self.assertEqual(
            clean_text("Pressure: 1.5 bar; isolation not verified."),
            "pressure: 1.5 bar; isolation not verified.",
        )

    def test_missing_text(self):
        for value in (None, float("nan"), pd.NA, ""):
            with self.subTest(value=value):
                self.assertEqual(clean_text(value), "")

    def test_known_joined_words(self):
        self.assertEqual(
            clean_text("withpersonnel werepresent controlto"),
            "with personnel were present control to",
        )

    def test_normalization_is_idempotent(self):
        text = "  LOTO wasn’t verified; PPE missing.  "
        normalized = clean_text(text)
        self.assertEqual(clean_text(normalized), normalized)

    def test_original_dataframe_preserved(self):
        original = pd.DataFrame({
            "report_id": ["R-2", "R-1"],
            "free_text": ["LOTO missing.", "No fire."],
            "ground_truth_sif": ["YES", "NO"],
        })
        snapshot = original.copy(deep=True)

        result = preprocess_dataframe(original)

        pd.testing.assert_frame_equal(original, snapshot)
        pd.testing.assert_frame_equal(
            result[original.columns], snapshot
        )
        self.assertIn("clean_text", result.columns)

    def test_missing_narrative_column(self):
        with self.assertRaisesRegex(ValueError, "free_text"):
            preprocess_dataframe(pd.DataFrame({"report_id": ["R-1"]}))

    def test_csv_preserves_none_category(self):
        csv = StringIO(
            "report_id,free_text,ground_truth_energy\n"
            "R-1,Inspection completed.,None\n"
        )
        result = load_and_preprocess(csv)
        self.assertEqual(result.loc[0, "ground_truth_energy"], "None")

    def test_empty_dataframe(self):
        result = preprocess_dataframe(
            pd.DataFrame(columns=["report_id", "free_text"])
        )
        self.assertTrue(result.empty)
        self.assertIn("clean_text", result.columns)


if __name__ == "__main__":
    unittest.main()