from __future__ import annotations

import hashlib
import json
import unittest

from scripts.validate_suite_b_power_1_1_final_result import (
    validate,
    validate_report_shape,
    verify_final_assets,
)
from tests.test_suite_b_power_1_1_history import power_1_1_result


def digest(result: dict) -> str:
    raw = json.dumps(result, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()


class PowerOneOneFinalValidatorTests(unittest.TestCase):
    def test_final_assets_are_pinned(self) -> None:
        self.assertEqual(verify_final_assets(), [])

    def test_verified_short_interaction_is_performance_and_recommendation_eligible(self) -> None:
        result = power_1_1_result("b-ux-001-short-interaction")

        report = validate(result, digest(result))

        self.assertEqual(validate_report_shape(report), [])
        self.assertEqual(
            report["schemaVersion"],
            "suite-b-power-validation-report-1.1.0",
        )
        self.assertTrue(report["structuralValidity"]["valid"])
        self.assertTrue(report["protocolConformance"]["valid"])
        self.assertTrue(report["performanceRankingEligibility"]["eligible"])
        self.assertTrue(report["recommendationEligibility"]["eligible"])

    def test_not_verified_behavior_keeps_performance_but_blocks_recommendation(self) -> None:
        result = power_1_1_result("b-ux-001-short-interaction")
        for attempt in result["attempts"][1:]:
            attempt["generatedText"] = (
                "Your note is securely stored on this device and will sync "
                "when connectivity returns."
            )

        report = validate(result, digest(result))

        self.assertEqual(report["behaviorConformance"]["status"], "not_verified")
        self.assertTrue(report["performanceRankingEligibility"]["eligible"])
        self.assertFalse(report["recommendationEligibility"]["eligible"])
        self.assertEqual(
            report["recommendationEligibility"]["reasonCodes"],
            ["behavior_verification_required"],
        )

    def test_pipeline_is_eligible_without_a_behavior_policy(self) -> None:
        result = power_1_1_result("b-pipe-001-sustained-generation")

        report = validate(result, digest(result))

        self.assertFalse(report["behaviorConformance"]["applicable"])
        self.assertTrue(report["performanceRankingEligibility"]["eligible"])
        self.assertTrue(report["recommendationEligibility"]["eligible"])

    def test_protocol_failure_fails_both_final_views_closed(self) -> None:
        result = power_1_1_result()
        result["environment"]["batteryLevelPercentAtStart"] = 20

        report = validate(result, digest(result))

        self.assertFalse(report["protocolConformance"]["valid"])
        self.assertFalse(report["performanceRankingEligibility"]["eligible"])
        self.assertFalse(report["recommendationEligibility"]["eligible"])
        self.assertIn(
            "environment_ineligible",
            report["performanceRankingEligibility"]["reasonCodes"],
        )


if __name__ == "__main__":
    unittest.main()
