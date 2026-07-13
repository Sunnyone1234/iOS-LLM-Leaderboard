from __future__ import annotations
import statistics, unittest
from scripts.validate_suite_b_input_sweep_bundle import POINTS, validate

def attempt(target: int, index: int, role: str) -> dict:
    first = target * 1_000_000 + index * 1_000
    return {"runIndex": index, "role": role, "outcome": "completed", "promptTokenCount": target, "outputTokenCount": 2, "thermalStateBefore": "nominal", "thermalStateAfter": "nominal", "metrics": {"ttftMilliseconds": first / 1_000_000, "prefillTokensPerSecond": 500.0, "peakMemoryMegabytes": 400 + target / 2}, "tokenEvents": [{"index": 0, "tokenID": 1, "elapsedNanoseconds": first}, {"index": 1, "tokenID": 2, "elapsedNanoseconds": first + 10_000_000}]}

def bundle() -> dict:
    points = []
    for target, (padding, digest) in POINTS.items():
        attempts = [attempt(target, 0, "warmup")] + [attempt(target, i, "measured") for i in range(1, 6)]
        measured = attempts[1:]
        points.append({"targetInputTokens": target, "fixtureSHA256": digest, "paddingRepetitions": padding, "successfulMeasuredRuns": 5, "medianPipelineTTFTMilliseconds": statistics.median(a["metrics"]["ttftMilliseconds"] for a in measured), "medianPrefillTokensPerSecond": 500.0, "medianPeakMemoryMegabytes": 400 + target / 2, "finalThermalState": "nominal", "attempts": attempts})
    return {"schemaVersion": "suite-b-input-sweep-bundle-0.1", "officialResultEligible": False, "workloadID": "b-pipe-002-input-length-sweep", "workloadVersion": "0.2.0-pilot", "pointOrder": list(POINTS), "outputTokenLimit": 32, "modelPreparation": {"eligibleForPerformanceMeasurement": True, "downloadOccurredDuringSession": False, "cacheStateBeforePreparation": "cached"}, "points": points}

class InputSweepValidatorTests(unittest.TestCase):
    def test_valid_bundle_recalculates(self): self.assertEqual(validate(bundle()), [])
    def test_wrong_input_count_fails(self):
        value = bundle(); value["points"][2]["attempts"][1]["promptTokenCount"] = 511
        self.assertTrue(any("input token mismatch" in e for e in validate(value)))
    def test_wrong_median_fails(self):
        value = bundle(); value["points"][0]["medianPipelineTTFTMilliseconds"] = 999
        self.assertTrue(any("medianPipelineTTFTMilliseconds mismatch" in e for e in validate(value)))

if __name__ == "__main__": unittest.main()
