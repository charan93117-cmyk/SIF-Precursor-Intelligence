import unittest

import pandas as pd

from src.barrier_detection import (
    apply_barrier_detection,
    detect_barrier_states,
)


class TestBarrierDetection(unittest.TestCase):

    def states(self, text):
        return [
            (item["barrier"], item["state"])
            for item in detect_barrier_states(text)
        ]

    def test_completed_gas_testing(self):
        self.assertEqual(
            self.states(
                "Gas testing was completed before confined space entry."
            ),
            [("Gas Testing", "effective")],
        )

    def test_verified_isolation(self):
        self.assertEqual(
            self.states("Electrical isolation was verified before maintenance."),
            [("Lockout Tagout", "effective")],
        )

    def test_missing_gas_testing(self):
        self.assertEqual(
            self.states("Gas detector was not used before entering the tank."),
            [("Gas Testing", "failed")],
        )

    def test_without_incident_is_not_barrier_failure(self):
        self.assertEqual(
            self.states("Work completed without incident."), []
        )

    def test_unsafe_sequence(self):
        self.assertEqual(
            self.states(
                "Equipment was opened before LOTO verification was completed."
            ),
            [("Lockout Tagout", "failed")],
        )

    def test_separate_controls_keep_separate_states(self):
        self.assertEqual(
            self.states(
                "LOTO was verified, but gas testing was not completed."
            ),
            [
                ("Lockout Tagout", "effective"),
                ("Gas Testing", "failed"),
            ],
        )

    def test_remediation_does_not_erase_failure(self):
        self.assertEqual(
            self.states(
                "Gas testing was not completed before entry. "
                "Gas testing was completed afterward."
            ),
            [
                ("Gas Testing", "failed"),
                ("Gas Testing", "effective"),
            ],
        )

    def test_uncertainty_requires_review(self):
        result = detect_barrier_states("Gas testing might be completed.")
        self.assertEqual(result[0]["state"], "unknown")
        self.assertTrue(result[0]["needs_review"])

    def test_negated_failure_does_not_prove_effectiveness(self):
        result = detect_barrier_states("Interlock was not bypassed.")
        self.assertEqual(result[0]["state"], "unknown")
        self.assertTrue(result[0]["needs_review"])

    def test_mention_only_is_unknown(self):
        self.assertEqual(
            self.states("Gas testing discussed."),
            [("Gas Testing", "unknown")],
        )

    def test_conflicting_state_requires_review(self):
        result = detect_barrier_states(
            "LOTO was verified although not properly verified."
        )
        self.assertEqual(result[0]["state"], "conflicting")
        self.assertTrue(result[0]["needs_review"])

    def test_multiple_controls_are_not_assigned_one_state(self):
        result = detect_barrier_states(
            "LOTO with gas testing was verified."
        )
        self.assertEqual(len(result), 2)
        self.assertTrue(all(item["state"] == "unknown" for item in result))
        self.assertTrue(all(item["needs_review"] for item in result))

    def test_evidence_offsets_match_original(self):
        text = (
            "  LOTO was verified; "
            "Gas detector was not used before entering the tank.  "
        )
        result = detect_barrier_states(text)
        self.assertEqual(len(result), 2)
        for item in result:
            self.assertEqual(
                text[item["start"]:item["end"]], item["text"]
            )

    def test_empty_or_missing_text(self):
        for value in ("", None, float("nan"), pd.NA):
            with self.subTest(value=value):
                self.assertEqual(detect_barrier_states(value), [])

    def test_dataframe_not_mutated(self):
        df = pd.DataFrame({
            "report_id": ["R-2", "R-1"],
            "free_text": ["LOTO verified.", "Gas testing missing."],
        }, index=[7, 3])
        before = df.copy(deep=True)

        result = apply_barrier_detection(df)

        pd.testing.assert_frame_equal(df, before)
        pd.testing.assert_frame_equal(result[df.columns], before)
        self.assertEqual(
            result.loc[3, "barrier_states"][0]["state"], "failed"
        )

    def test_empty_dataframe(self):
        result = apply_barrier_detection(
            pd.DataFrame(columns=["free_text"])
        )
        self.assertTrue(result.empty)
        self.assertIn("barrier_states", result.columns)

    def test_clean_text_only_compatibility(self):
        result = apply_barrier_detection(pd.DataFrame({
            "clean_text": ["lockout tagout missing"],
        }))
        self.assertEqual(
            result.loc[0, "barrier_states"][0]["state"], "failed"
        )

    def test_missing_text_column_rejected(self):
        with self.assertRaises(ValueError):
            apply_barrier_detection(
                pd.DataFrame({"report_id": ["R-1"]})
            )


if __name__ == "__main__":
    unittest.main()