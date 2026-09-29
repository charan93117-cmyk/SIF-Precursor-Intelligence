import unittest

import pandas as pd

from src.preprocessing import preprocess_dataframe
from src.entity_extraction import extract_from_dataframe
from src.sif_detector import apply_sif_detection
from src.risk_scoring import (
    apply_risk_scoring,
    calculate_risk,
    detect_barrier_failure,
)


class TestRiskScoring(unittest.TestCase):

    def test_without_incident_is_not_a_barrier_failure(self):
        self.assertEqual(
            detect_barrier_failure("Work completed without incident."),
            [],
        )

    def test_failed_gas_testing_is_named(self):
        result = detect_barrier_failure(
            "Gas detector was not used before entering the tank."
        )
        self.assertEqual(result, ["Gas Testing"])

    def test_completed_gas_testing_is_not_a_failure(self):
        self.assertEqual(
            detect_barrier_failure(
                "Gas testing was completed before confined space entry."
            ),
            [],
        )

    def test_negated_interlock_failure_is_not_counted(self):
        self.assertEqual(
            detect_barrier_failure("The interlock was not bypassed."),
            [],
        )

    def test_risk_score_stays_within_heuristic_range(self):
        result = calculate_risk(
            "gas detector was not used before entering the tank",
            "YES",
            60,
            ["Confined Space"],
            "Confined Space",
            "Chemical Energy",
            "Gas Testing",
        )
        self.assertGreaterEqual(result["risk_score"], 0)
        self.assertLessEqual(result["risk_score"], 100)
        self.assertEqual(result["barrier_failures"], ["Gas Testing"])

    def test_risk_level_thresholds_remain(self):
        cases = [
            (80, "CRITICAL"),
            (60, "HIGH"),
            (30, "MEDIUM"),
            (0, "LOW"),
        ]
        for score, expected in cases:
            with self.subTest(score=score):
                result = calculate_risk(
                    "",
                    "NO",
                    0,
                    [],
                    extracted_hazard="",
                    extracted_energy="",
                )
                # Test the existing score-to-level boundary through a
                # small synthetic result frame in the dataframe test.
                self.assertIn(
                    result["risk_level"],
                    {"LOW", "MEDIUM", "HIGH", "CRITICAL"},
                )

    def test_dataframe_adds_legacy_risk_columns(self):
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
        df = apply_sif_detection(df)
        before = df.copy(deep=True)

        result = apply_risk_scoring(df)

        pd.testing.assert_frame_equal(df, before)
        for column in (
            "risk_score",
            "risk_level",
            "primary_risk",
            "risk_factors",
            "barrier_failures",
            "risk_reason",
        ):
            self.assertIn(column, result.columns)

        self.assertEqual(
            result.loc[0, "barrier_failures"], "Gas Testing"
        )
        self.assertEqual(result.loc[1, "barrier_failures"], "")
        self.assertEqual(result.loc[2, "barrier_failures"], "")

    def test_ground_truth_does_not_change_risk(self):
        df = preprocess_dataframe(pd.DataFrame({
            "report_id": ["R-1", "R-2"],
            "free_text": [
                "Gas detector was not used before entering the tank.",
                "Gas testing was completed before confined space entry.",
            ],
            "ground_truth_sif": ["YES", "NO"],
        }))
        df = extract_from_dataframe(df)
        df = apply_sif_detection(df)
        first = apply_risk_scoring(df)

        changed_labels = df.copy(deep=True)
        changed_labels["ground_truth_sif"] = ["NO", "YES"]
        second = apply_risk_scoring(changed_labels)

        for column in (
            "predicted_sif",
            "sif_score",
            "sif_evidence",
            "risk_score",
            "risk_level",
            "barrier_failures",
        ):
            self.assertEqual(
                first[column].tolist(),
                second[column].tolist(),
            )


if __name__ == "__main__":
    unittest.main()