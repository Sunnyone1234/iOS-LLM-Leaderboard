from __future__ import annotations
import json, statistics, unittest
from pathlib import Path
from scripts.validate_suite_b_context_assistance_bundle import evaluate_contract
from scripts.validate_suite_b_result_bundle import PLANS, THINKING_MODES, validate

PASSING = "The note is safe in the local vault. Network must be stable for 30 seconds; below 20 percent wait for power. Avoid deleting or reinstalling. ORCHID-47."
FAILING = "The note is safe locally. ORCHID-47."
ROOT = Path(__file__).resolve().parents[1]

def attempt(target: int | None, index: int, role: str, quality: bool) -> dict:
    first = 100_000_000 + index * 1_000_000
    text = PASSING if quality else FAILING
    contract = evaluate_contract(text) if quality else None
    return {"runIndex": index, "role": role, "outcome": "completed", "errorMessage": None, "promptTokenCount": target or 235, "outputTokenCount": 2, "stopReason": "outputTokenLimit", "visibleText": text, "answerContract": contract, "answerEligible": all(contract.values()) if contract is not None else None, "thermalStateBefore": "nominal", "thermalStateAfter": "nominal", "memorySamplingIntervalMilliseconds": 50, "metrics": {"ttftMilliseconds": first / 1_000_000, "userVisibleTTFTMilliseconds": first / 1_000_000 + 1, "requestCompletionMilliseconds": first / 1_000_000 + 10, "prefillTokensPerSecond": 500.0, "decodeTokensPerSecond": 95.0, "peakMemoryMegabytes": 700.0}, "tokenEvents": [{"index": 0, "tokenID": 1, "elapsedNanoseconds": first}, {"index": 1, "tokenID": 2, "elapsedNanoseconds": first + 10_000_000}]}

def bundle(workload_id: str, schema: str = "suite-b-result-bundle-0.1") -> dict:
    plan_id, version, category, output_limit, targets, digests = PLANS[workload_id]
    thinking, visible = THINKING_MODES[workload_id]
    sessions = []
    for position, target in enumerate(targets or [None]):
        quality = workload_id == "b-ux-002-context-assistance"
        attempts = [attempt(target, 0, "warmup", quality)] + [attempt(target, i, "measured", quality) for i in range(1, 6)]
        measured = attempts[1:]
        sessions.append({"id": "default" if target is None else f"point-{target}", "targetInputTokens": target, "fixtureSHA256": digests[position], "paddingRepetitions": None, "performanceEligible": True, "qualityEligible": True if quality else None, "timingEvidenceRetained": True, "summary": {"successfulMeasuredRuns": 5, "failedMeasuredRuns": 0, "answerContractPassingRuns": 5 if quality else None, "modelInputTokens": target or 235, "medianPipelineTTFTMilliseconds": statistics.median(a["metrics"]["ttftMilliseconds"] for a in measured), "medianUserVisibleTTFTMilliseconds": statistics.median(a["metrics"]["userVisibleTTFTMilliseconds"] for a in measured), "medianRequestCompletionMilliseconds": statistics.median(a["metrics"]["requestCompletionMilliseconds"] for a in measured), "medianPrefillTokensPerSecond": 500.0, "medianDecodeTokensPerSecond": 95.0, "medianPeakMemoryMegabytes": 700.0, "finalThermalState": "nominal"}, "attempts": attempts})
    return {"schemaVersion": schema, "resultID": "11111111-1111-4111-8111-111111111111", "createdAt": "2026-07-13T00:00:00Z", "officialResultEligible": False, "plan": {"id": plan_id, "version": version, "runnerKind": "test", "warmupRuns": 1, "measuredRuns": 5, "outputTokenLimit": output_limit, "requiredPowerSource": "unplugged", "minimumBatteryLevelPercent": 50}, "workload": {"id": workload_id, "version": version, "category": category, "fixtureSHA256": digests}, "measurementMode": {"userVisibleTTFTAvailable": visible}, "generationConfiguration": {"outputTokenLimit": output_limit, "thinkingMode": thinking}, "model": {"displayName": "Test Model", "baseModelID": "example/base", "artifactID": "example/artifact", "artifactRevision": "0123456789abcdef0123456789abcdef01234567", "modelFamily": "Test", "parameterSizeClass": "test", "quantization": "4-bit", "modelFormat": "test", "tokenizerIdentity": "example/tokenizer", "sourceURL": "https://example.com/model", "licenseIdentifier": "test", "licenseSourceURL": "https://example.com/license", "artifactRepositorySizeBytes": 1, "compatibilityConstraints": ["test-only"]}, "modelPreparation": {"eligibleForPerformanceMeasurement": True, "cacheStateBeforePreparation": "cached", "downloadOccurredDuringSession": False}, "device": {"batteryState": "unplugged", "batteryLevelPercent": 70}, "eligibility": {"officialLeaderboardEligible": False, "sessionValid": True, "reasonCodes": ["pilot_protocol_not_official"]}, "sessions": sessions}

class UnifiedSuiteBBundleTests(unittest.TestCase):
    def test_all_four_workloads_share_one_valid_envelope(self):
        for workload_id in PLANS:
            with self.subTest(workload_id=workload_id): self.assertEqual(validate(bundle(workload_id)), [])
    def test_point_identity_is_enforced(self):
        value = bundle("b-pipe-002-input-length-sweep"); value["sessions"][2]["targetInputTokens"] = 511
        self.assertTrue(any("point identity mismatch" in error for error in validate(value)))
    def test_context_quality_is_recomputed(self):
        value = bundle("b-ux-002-context-assistance"); value["sessions"][0]["attempts"][1]["visibleText"] = FAILING
        self.assertTrue(any("answer contract mismatch" in error for error in validate(value)))
    def test_legacy_schema_is_not_misclassified_as_unified(self):
        value = bundle("b-pipe-001-sustained-generation"); value["schemaVersion"] = "suite-b-pilot-bundle-0.6"
        self.assertIn("unsupported schemaVersion", validate(value))

    def test_0_2_requires_unplugged_and_minimum_battery(self):
        self.assertEqual(validate(bundle("b-pipe-001-sustained-generation", "suite-b-result-bundle-0.2")), [])

    def test_0_2_rejects_charging_as_valid(self):
        value = bundle("b-pipe-001-sustained-generation", "suite-b-result-bundle-0.2")
        value["device"]["batteryState"] = "charging"
        self.assertIn("ineligible power state cannot produce a valid session", validate(value))

    def test_0_2_requires_low_battery_reason(self):
        value = bundle("b-pipe-001-sustained-generation", "suite-b-result-bundle-0.2")
        value["device"]["batteryLevelPercent"] = 49
        value["eligibility"]["sessionValid"] = False
        self.assertIn("missing power reason code: battery_level_below_minimum", validate(value))

    def test_0_2_allows_other_conditions_to_invalidate_session(self):
        value = bundle("b-pipe-001-sustained-generation", "suite-b-result-bundle-0.2")
        value["eligibility"]["sessionValid"] = False
        value["eligibility"]["reasonCodes"] = ["session_environment_ineligible", "pilot_protocol_not_official"]
        self.assertEqual(validate(value), [])

    def test_0_3_requires_additive_model_identity(self):
        value = bundle(
            "b-pipe-001-sustained-generation",
            "suite-b-result-bundle-0.3",
        )
        del value["model"]["licenseSourceURL"]
        self.assertIn(
            "model.licenseSourceURL must be a non-empty string",
            validate(value),
        )

    def test_all_retained_app_0_6_exports_pass_unified_validation(self):
        raw = ROOT / "results" / "suite-b-pilot-v0.1" / "raw"
        paths = sorted(raw.glob("*.json"))
        self.assertEqual(len(paths), 6)
        for path in paths:
            with self.subTest(path=path.name):
                value = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(
                    value["schemaVersion"],
                    "suite-b-result-bundle-0.3",
                )
                self.assertEqual(validate(value), [])

    def test_0_3_public_schema_is_present_and_identifies_historical_export(self):
        schema = json.loads(
            (
                ROOT
                / "schemas"
                / "suite-b-result-bundle-0.3.schema.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            schema["properties"]["schemaVersion"]["const"],
            "suite-b-result-bundle-0.3",
        )
        self.assertEqual(
            schema["properties"]["officialResultEligible"]["const"],
            False,
        )

if __name__ == "__main__": unittest.main()
