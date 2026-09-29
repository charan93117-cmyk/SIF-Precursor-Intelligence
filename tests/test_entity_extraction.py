import unittest

import pandas as pd

from src.entity_extraction import (
    extract_entities,
    extract_entity_evidence,
    extract_from_dataframe,
    find_matches,
)
from src.preprocessing import preprocess_dataframe


class TestEntityExtraction(unittest.TestCase):

    def test_whole_word_matching(self):
        dictionary = {"Fire": ["fire"]}
        self.assertEqual(find_matches("fire nearby", dictionary), ["Fire"])
        self.assertEqual(find_matches("firewall inspected", dictionary), [])

    def test_flexible_whitespace(self):
        dictionary = {"Confined Space": ["confined space"]}
        self.assertEqual(
            find_matches("CONFINED   SPACE", dictionary),
            ["Confined Space"],
        )

    def test_original_categories_preserved(self):
        result = extract_entities("Electrical isolation was verified.")
        self.assertIn("Electrical Energy", result["hazards"])
        self.assertIn("Electrical Energy", result["energy"])
        self.assertIn("Lockout Tagout", result["barriers"])

    def test_loto_alias(self):
        result = extract_entities("LOTO was verified.")
        self.assertIn("Lockout Tagout", result["barriers"])

    def test_gas_testing_barrier(self):
        result = extract_entities("Gas detector was not used.")
        self.assertIn("Gas Testing", result["barriers"])

    def test_additional_barriers(self):
        cases = {
            "Lanyard missing.": "Fall Protection",
            "Barricading absent.": "Barricading",
            "Pedestrian control missing.": "Vehicle Separation",
            "Interlock defeated.": "Safety Interlock",
        }
        for text, category in cases.items():
            with self.subTest(text=text):
                self.assertIn(category, extract_entities(text)["barriers"])

    def test_evidence_offsets_match_original(self):
        text = "LOTO was verified. Gas detector was not used."
        evidence = extract_entity_evidence(text)
        self.assertTrue(evidence)

        for item in evidence:
            self.assertEqual(
                text[item["start"]:item["end"]],
                item["text"],
            )
            self.assertGreater(item["end"], item["start"])

    def test_repeated_mentions_retained(self):
        evidence = extract_entity_evidence("LOTO checked; LOTO missing.")
        matches = [
            item for item in evidence
            if item["category"] == "Lockout Tagout"
        ]
        self.assertEqual(len(matches), 2)
        self.assertNotEqual(matches[0]["start"], matches[1]["start"])

    def test_overlapping_aliases_deduplicated(self):
        evidence = extract_entity_evidence("lockout tagout")
        matches = [
            item for item in evidence
            if item["category"] == "Lockout Tagout"
        ]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["text"], "lockout tagout")

    def test_mentions_do_not_claim_control_state(self):
        evidence = extract_entity_evidence("Gas testing was completed.")
        self.assertTrue(evidence)
        self.assertTrue(
            all(item["assertion"] == "uncertain" for item in evidence)
        )

    def test_deterministic_output(self):
        text = "Gas detector and LOTO checked."
        self.assertEqual(extract_entities(text), extract_entities(text))

    def test_missing_text(self):
        for value in (None, float("nan"), pd.NA, ""):
            with self.subTest(value=value):
                result = extract_entities(value)
                self.assertEqual(result["hazards"], [])
                self.assertEqual(result["energy"], [])
                self.assertEqual(result["barriers"], [])
                self.assertEqual(result["evidence"], [])

    def test_dataframe_preserved_and_legacy_columns_present(self):
        original = preprocess_dataframe(pd.DataFrame({
            "report_id": ["R-2", "R-1"],
            "free_text": ["LOTO missing.", "Gas testing completed."],
            "ground_truth_sif": ["YES", "NO"],
        }, index=[7, 3]))
        snapshot = original.copy(deep=True)

        result = extract_from_dataframe(original)

        pd.testing.assert_frame_equal(original, snapshot)
        pd.testing.assert_frame_equal(
            result[original.columns], snapshot
        )
        for column in (
            "extracted_hazard",
            "extracted_energy",
            "extracted_barrier",
            "entity_evidence",
        ):
            self.assertIn(column, result.columns)

        self.assertEqual(
            result.loc[7, "entity_evidence"][0]["text"], "LOTO"
        )

    def test_clean_text_only_compatibility(self):
        result = extract_from_dataframe(pd.DataFrame({
            "clean_text": ["lockout tagout missing"],
        }))
        self.assertIn(
            "Lockout Tagout", result.loc[0, "extracted_barrier"]
        )

    def test_empty_dataframe(self):
        df = pd.DataFrame(columns=["free_text", "clean_text"])
        result = extract_from_dataframe(df)
        self.assertTrue(result.empty)
        self.assertIn("entity_evidence", result.columns)

    def test_missing_clean_text_rejected(self):
        with self.assertRaisesRegex(ValueError, "clean_text"):
            extract_from_dataframe(pd.DataFrame({
                "free_text": ["Inspection completed."],
            }))


if __name__ == "__main__":
    unittest.main()