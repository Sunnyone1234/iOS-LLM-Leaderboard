from __future__ import annotations

import statistics
import unittest

from scripts.validate_suite_b_context_assistance_bundle import (
    DOCUMENT_SHA256,
    POINTS,
    QUESTION_SHA256,
    evaluate_contract,
    validate,
)

PASSING_TEXT = "The note is safe in the local vault. After the network is stable for 30 seconds, sync waits below 20 percent until connected to power. Avoid deleting or reinstalling; reference ORCHID-47."
FAILING_TEXT = "The note is safe locally. Reference ORCHID-47."


def attempt(target: int, index: int, role: str, text: str) -> dict:
    first = target * 1_000_000 + index * 1_000
    contract = evaluate_contract(text)
    return {
        "runIndex": index, "role": role, "outcome": "completed", "errorMessage": None,
        "promptTokenCount": target, "outputTokenCount": 2, "stopReason": "endOfSequence",
        "visibleText": text, "answerContract": contract, "answerEligible": all(contract.values()),
        "thermalStateBefore": "nominal", "thermalStateAfter": "nominal",
        "metrics": {"ttftMilliseconds": first / 1_000_000, "userVisibleTTFTMilliseconds": first / 1_000_000 + 1, "requestCompletionMilliseconds": first / 1_000_000 + 100, "peakMemoryMegabytes": 400 + target / 2},
        "tokenEvents": [{"index": 0, "tokenID": 1, "elapsedNanoseconds": first}, {"index": 1, "tokenID": 2, "elapsedNanoseconds": first + 10_000_000}],
    }


def bundle(text: str = FAILING_TEXT) -> dict:
    points = []
    for target, (padding, digest) in POINTS.items():
        attempts = [attempt(target, 0, "warmup", text)] + [attempt(target, i, "measured", text) for i in range(1, 6)]
        measured = attempts[1:]
        passing = sum(a["answerEligible"] for a in measured)
        points.append({
            "targetInputTokens": target, "fixtureSHA256": digest, "paddingRepetitions": padding,
            "successfulMeasuredRuns": 5, "answerContractPassingRuns": passing,
            "uxPerformanceEligible": passing == 5, "timingEvidenceRetained": True,
            "medianPipelineTTFTMilliseconds": statistics.median(a["metrics"]["ttftMilliseconds"] for a in measured),
            "medianUserVisibleTTFTMilliseconds": statistics.median(a["metrics"]["userVisibleTTFTMilliseconds"] for a in measured),
            "medianRequestCompletionMilliseconds": statistics.median(a["metrics"]["requestCompletionMilliseconds"] for a in measured),
            "medianPeakMemoryMegabytes": 400 + target / 2, "finalThermalState": "nominal", "attempts": attempts,
        })
    return {
        "schemaVersion": "suite-b-context-assistance-bundle-0.1", "officialResultEligible": False,
        "workloadID": "b-ux-002-context-assistance", "workloadVersion": "0.2.0-pilot",
        "documentSHA256": DOCUMENT_SHA256, "questionSHA256": QUESTION_SHA256,
        "pointOrder": list(POINTS), "outputTokenLimit": 128,
        "modelPreparation": {"eligibleForPerformanceMeasurement": True, "downloadOccurredDuringSession": False, "cacheStateBeforePreparation": "cached"},
        "points": points,
    }


class ContextAssistanceBundleTests(unittest.TestCase):
    def test_quality_failure_retains_valid_timing_evidence(self) -> None:
        value = bundle()
        self.assertEqual(validate(value), [])
        self.assertTrue(all(not point["uxPerformanceEligible"] for point in value["points"]))
        self.assertTrue(all(point["timingEvidenceRetained"] for point in value["points"]))

    def test_all_contracts_must_pass_for_ux_eligibility(self) -> None:
        value = bundle(PASSING_TEXT)
        self.assertEqual(validate(value), [])
        self.assertTrue(all(point["uxPerformanceEligible"] for point in value["points"]))

    def test_contract_is_recomputed_from_visible_text(self) -> None:
        value = bundle(PASSING_TEXT)
        value["points"][0]["attempts"][1]["visibleText"] = FAILING_TEXT
        self.assertTrue(any("answer contract mismatch" in error for error in validate(value)))

    def test_zero_of_five_cannot_be_marked_eligible(self) -> None:
        value = bundle()
        value["points"][0]["uxPerformanceEligible"] = True
        self.assertIn("points[0] UX eligibility mismatch", validate(value))


if __name__ == "__main__": unittest.main()
