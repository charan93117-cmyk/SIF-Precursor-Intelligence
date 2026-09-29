import ast
import unittest
from pathlib import Path

import pandas as pd

from src.entity_extraction import extract_from_dataframe
from src.preprocessing import preprocess_dataframe
from src.sif_detector import apply_sif_detection, detect_sif


class TestSIFDetector(unittest.TestCase):

    def test_five_reproduced_cases(self):
        cases = [
            ("Gas testing was completed before confined space entry.", "NO"),
            ("Electrical isolation was verified before maintenance.", "NO"),
            ("No fire or ignition source was present.", "NO"),
            ("Work completed without incident.", "NO"),
            ("Gas detector was not used before entering the tank.", "YES"),
        ]

        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(
                    detect_sif(text)["sif_prediction"], expected
                )

    def test_negated_exposure_not_flagged(self):
        cases = [
            "No workers were near moving machinery.",
            "No pedestrian entered the vehicle path.",
            "The interlock was not bypassed.",
            "Training drill: worker entered the danger zone near moving mechanical equipment.",
        ]
        for text in cases:
            with self.subTest(text=text):
                self.assertEqual(
                    detect_sif(text)["sif_prediction"], "NO"
                )

    def test_harness_and_authorization_templates(self):
        cases = [
            "Harness was available but was not attached while working at height.",
            "Required authorization was missing when the task commenced.",
        ]
        for text in cases:
            with self.subTest(text=text):
                self.assertEqual(
                    detect_sif(text)["sif_prediction"], "YES"
                )

    def test_evidence_offsets_match_original(self):
        text = "Gas detector was not used before entering the tank."
        result = detect_sif(text)
        self.assertTrue(result["sif_evidence"])

        for item in result["sif_evidence"]:
            self.assertEqual(
                text[item["start"]:item["end"]],
                item["text"],
            )

    def test_positive_prediction_requires_review(self):
        result = detect_sif(
            "Gas detector was not used before entering the tank."
        )
        self.assertEqual(result["sif_prediction"], "YES")
        self.assertTrue(result["needs_review"])
        self.assertTrue(result["assessment_notes"])

    def test_empty_text_is_not_flagged(self):
        for text in ("", None, float("nan")):
            with self.subTest(text=text):
                result = detect_sif(text)
                self.assertEqual(result["sif_prediction"], "NO")

    def test_ground_truth_labels_do_not_change_predictions_or_evidence(self):
        df = preprocess_dataframe(pd.DataFrame({
            "report_id": ["R-1", "R-2", "R-3"],
            "free_text": [
                "Gas detector was not used before entering the tank.",
                "Gas testing was completed before confined space entry.",
                "Work completed without incident.",
            ],
            "ground_truth_sif": ["YES", "NO", "NO"],
        }))
        df = extract_from_dataframe(df)

        first = apply_sif_detection(df)

        changed_labels = df.copy(deep=True)
        changed_labels["ground_truth_sif"] = ["NO", "YES", "YES"]
        second = apply_sif_detection(changed_labels)

        self.assertEqual(
            first["predicted_sif"].tolist(),
            second["predicted_sif"].tolist(),
        )
        self.assertEqual(
            first["sif_score"].tolist(),
            second["sif_score"].tolist(),
        )
        self.assertEqual(
            first["sif_evidence"].tolist(),
            second["sif_evidence"].tolist(),
        )

    def test_predictions_work_without_ground_truth_columns(self):
        df = preprocess_dataframe(pd.DataFrame({
            "report_id": ["R-1"],
            "free_text": [
                "Gas detector was not used before entering the tank."
            ],
        }))
        df = extract_from_dataframe(df)
        result = apply_sif_detection(df)
        self.assertEqual(result.loc[0, "predicted_sif"], "YES")

    def test_all_positive_generator_templates(self):
        path = Path("generate_data.py")
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        patterns = None

        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name)
                and target.id == "patterns"
                for target in node.targets
            ):
                patterns = ast.literal_eval(node.value)
                break

        self.assertIsNotNone(patterns)

        narratives = [
            text
            for pattern in patterns
            for text in pattern["texts"]
        ]
        self.assertEqual(len(narratives), 72)

        predictions = [
            detect_sif(text)["sif_prediction"]
            for text in narratives
        ]
        self.assertEqual(predictions.count("YES"), 72)


if __name__ == "__main__":
    unittest.main()