from __future__ import annotations

import statistics
import unittest

from scripts.validate_suite_b_ux_bundle import PROMPT_SHA256, validate


def attempt(index: int, role: str) -> dict:
    pipeline = 180_000_000 + index * 1_000_000
    return {
        "runIndex": index,
        "role": role,
        "outcome": "completed",
        "errorMessage": None,
        "promptTokenCount": 70,
        "outputTokenCount": 2,
        "stopReason": "endOfSequence",
        "visibleText": "The note is safe locally and will sync when connectivity returns.",
        "thermalStateBefore": "nominal",
        "thermalStateAfter": "nominal",
        "metrics": {
            "ttftMilliseconds": pipeline / 1_000_000,
            "userVisibleTTFTMilliseconds": pipeline / 1_000_000 + 1,
            "requestCompletionMilliseconds": pipeline / 1_000_000 + 100,
        },
        "tokenEvents": [
            {"index": 0, "tokenID": 10, "elapsedNanoseconds": pipeline},
            {"index": 1, "tokenID": 11, "elapsedNanoseconds": pipeline + 10_000_000},
        ],
    }


def bundle() -> dict:
    attempts = [attempt(0, "warmup")] + [attempt(i, "measured") for i in range(1, 6)]
    measured = attempts[1:]
    return {
        "schemaVersion": "suite-b-ux-bundle-0.1",
        "officialResultEligible": False,
        "plan": {
            "id": "b-ux-001-validation",
            "version": "0.2.0-pilot",
            "promptSHA256": PROMPT_SHA256,
            "warmupRuns": 1,
            "measuredRuns": 5,
            "outputTokenLimit": 128,
        },
        "workload": {
            "id": "b-ux-001-short-interaction",
            "category": "user-experience",
            "promptSHA256": PROMPT_SHA256,
        },
        "measurementMode": {"userVisibleTTFTAvailable": True},
        "generationConfiguration": {
            "thinkingMode": "disabled-via-chat-template",
            "samplingEnabled": False,
            "temperature": 0,
        },
        "modelPreparation": {
            "eligibleForPerformanceMeasurement": True,
            "downloadOccurredDuringSession": False,
            "cacheStateBeforePreparation": "cached",
        },
        "summary": {
            "successfulMeasuredRuns": 5,
            "failedMeasuredRuns": 0,
            "modelInputTokens": 70,
            "medianPipelineTTFTMilliseconds": statistics.median(
                a["metrics"]["ttftMilliseconds"] for a in measured
            ),
            "medianUserVisibleTTFTMilliseconds": statistics.median(
                a["metrics"]["userVisibleTTFTMilliseconds"] for a in measured
            ),
            "medianRequestCompletionMilliseconds": statistics.median(
                a["metrics"]["requestCompletionMilliseconds"] for a in measured
            ),
        },
        "attempts": attempts,
    }


class UXBundleValidatorTests(unittest.TestCase):
    def test_valid_bundle_recalculates(self) -> None:
        self.assertEqual(validate(bundle()), [])

    def test_visible_timing_cannot_precede_pipeline(self) -> None:
        value = bundle()
        value["attempts"][1]["metrics"]["userVisibleTTFTMilliseconds"] = 1
        self.assertTrue(any("out of order" in error for error in validate(value)))

    def test_summary_is_recalculated(self) -> None:
        value = bundle()
        value["summary"]["medianRequestCompletionMilliseconds"] = 999
        self.assertIn(
            "summary.medianRequestCompletionMilliseconds does not match attempts",
            validate(value),
        )

    def test_download_session_is_rejected(self) -> None:
        value = bundle()
        value["modelPreparation"]["downloadOccurredDuringSession"] = True
        self.assertIn(
            "downloaded model cannot be measured in the same session",
            validate(value),
        )


if __name__ == "__main__":
    unittest.main()
