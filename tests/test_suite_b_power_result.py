from __future__ import annotations

import copy
import json
import statistics
import unittest
from pathlib import Path

from scripts.validate_suite_b_power_result import (
    ATTEMPT_REASON_CODES,
    validate,
    validate_report_shape,
    verify_release_assets,
)


ROOT = Path(__file__).resolve().parents[1]


def _attempt(index: int, workload_id: str, scale: float = 1.0) -> dict:
    first = int(100_000_000 * scale)
    second = first + int(20_000_000 * scale)
    third = second + int(20_000_000 * scale)
    generation_start = 20_000_000
    prompt_tokens = 235 if workload_id.startswith("b-pipe") else 70
    prompt_ns = int(500_000_000 * scale)
    memory = int(700 * 1_048_576 * scale)
    ux = workload_id.startswith("b-ux")
    trace = None
    first_renderable = None
    request_completion = None
    if ux:
        first_renderable = generation_start + first + 1_000_000
        request_completion = generation_start + third + 10_000_000
        trace = {
            "policyVersion": "first-renderable-decoded-prefix-v1",
            "clockOrigin": "adapter-request-accepted",
            "scope": "through-first-renderable-inclusive",
            "captureLimit": 32,
            "generationStartNanoseconds": generation_start,
            "outcome": "firstRenderableFound",
            "firstRenderableTokenIndex": 0,
            "entries": [
                {
                    "tokenIndex": 0,
                    "tokenID": 10,
                    "tokenReceivedNanoseconds": generation_start + first,
                    "decodedAtNanoseconds": first_renderable,
                    "decodedPrefix": "The note is safe",
                    "isRenderable": True,
                }
            ],
        }
    return {
        "runIndex": index,
        "role": "warmup" if index == 0 else "measured",
        "outcome": "completed",
        "reasonCodes": [],
        "stopReason": "endOfSequence",
        "generatedText": (
            "Your note is safe on this iPhone. It will sync when connectivity returns."
            if ux else None
        ),
        "promptTokenCount": prompt_tokens,
        "outputTokenCount": 3,
        "responseConformance": {
            "status": "pass" if ux else "notApplicable",
            "reasonCodes": [],
        },
        "timingEvidence": {
            "generationStartNanoseconds": generation_start,
            "promptEvaluationNanoseconds": prompt_ns,
            "requestCompletionNanoseconds": request_completion,
        },
        "tokenEvents": [
            {"index": 0, "tokenID": 10, "elapsedNanoseconds": first},
            {"index": 1, "tokenID": 11, "elapsedNanoseconds": second},
            {"index": 2, "tokenID": 12, "elapsedNanoseconds": third},
        ],
        "renderabilityTrace": trace,
        "memorySamples": [
            {"elapsedNanoseconds": 0, "physicalFootprintBytes": memory - 1_048_576},
            {"elapsedNanoseconds": third + 1, "physicalFootprintBytes": memory},
        ],
        "thermal": {"before": "nominal", "after": "nominal", "transitions": []},
        "derivedMetrics": {
            "pipelineTTFTMilliseconds": first / 1_000_000,
            "firstRenderableProxyTTFTMilliseconds": first_renderable / 1_000_000 if ux else None,
            "requestCompletionMilliseconds": request_completion / 1_000_000 if ux else None,
            "prefillTokensPerSecond": prompt_tokens * 1_000_000_000 / prompt_ns,
            "decodeTokensPerSecond": 2 * 1_000_000_000 / (third - first),
            "processPhysicalFootprintMiB": memory / 1_048_576,
        },
    }


def valid_result(workload_id: str = "b-pipe-001-sustained-generation") -> dict:
    ux = workload_id.startswith("b-ux")
    attempts = [_attempt(0, workload_id)] + [
        _attempt(index, workload_id, 1 + (index - 1) * 0.01)
        for index in range(1, 6)
    ]
    measured = attempts[1:]

    def median(field: str) -> float:
        values = sorted(item["derivedMetrics"][field] for item in measured)
        return values[2]

    decode_first = measured[0]["derivedMetrics"]["decodeTokensPerSecond"]
    decode_last = measured[-1]["derivedMetrics"]["decodeTokensPerSecond"]
    return {
        "schemaVersion": "suite-b-power-result-1.0.0-rc.1",
        "resultID": "11111111-1111-4111-8111-111111111111",
        "createdAt": "2026-07-13T12:00:00Z",
        "benchmarkRelease": {
            "id": "suite-b-power",
            "version": "1.0.0-rc.1",
            "protocolID": "suite-b-power",
            "protocolVersion": "1.0.0-rc.1",
        },
        "officialResultEligible": False,
        "execution": {
            "sessionID": "22222222-2222-4222-8222-222222222222",
            "workloadID": workload_id,
            "workloadVersion": "1.0.0-rc.1",
            "workloadCategory": "user-experience" if ux else "pipeline",
            "fixtureSHA256": (
                "69b3cd45fb67e1882dabdc082636298123e01081c097af65b3fd133b19ccbc84"
                if ux else
                "b865ad1a1993bfd7bf097b85f7c5585e44f1384fa291b9c05426c6051caba996"
            ),
            "measurementModeID": "b-mode-warm-resident-ux-v1" if ux else "b-mode-sustained-no-rest-v1",
            "runnerID": "ios-reference-benchmark-app",
            "runnerVersion": "0.8.0",
            "appVersion": "0.8.0",
            "appBuild": "10",
            "appSourceCommit": "a" * 40,
        },
        "configuration": {
            "warmupAttempts": 1,
            "measuredAttempts": 5,
            "minimumMetricEligibleMeasuredAttempts": 3,
            "restIntervalSeconds": 0,
            "samplingEnabled": False,
            "temperature": 0,
            "topP": 1 if ux else None,
            "topK": 0 if ux else None,
            "seed": 0 if ux else None,
            "repetitionPenalty": None,
            "thinkingMode": "disabled-via-chat-template" if ux else "disabled-via-prompt-directive",
            "chatTemplateIdentity": (
                "artifact-tokenizer-config-enable-thinking-false"
                if ux else "artifact-tokenizer-config"
            ),
            "includeStopTokenInRawEvents": False,
            "outputTokenLimit": 128 if ux else 512,
            "modelLoadPolicy": "load-once-before-warmup",
            "contextPolicy": "fresh-conversation-per-attempt",
            "kvCachePolicy": "fresh-kv-cache-per-attempt",
            "automaticRetries": 0,
            "clock": "monotonic-nanoseconds",
            "memorySamplingIntervalMilliseconds": 50,
            "memoryMetric": "TASK_VM_INFO.phys_footprint",
            "thermalSource": "ProcessInfo.thermalState",
        },
        "model": {
            "displayName": "Synthetic Test Model",
            "baseModelID": "test/base",
            "artifactID": "test/artifact",
            "artifactRevision": "b" * 40,
            "artifactContentHash": None,
            "quantization": "test-only",
            "modelFormat": "test-only",
            "tokenizerIdentity": "test/tokenizer",
            "sourceURL": "https://example.invalid/model",
            "licenseIdentifier": "test-only",
            "licenseSourceURL": "https://example.invalid/license",
            "artifactRepositorySizeBytes": 1,
        },
        "runtime": {
            "name": "Synthetic Test Runtime",
            "version": "1.0",
            "resolvedRevision": "c" * 40,
            "backend": "test-only",
            "dependencyVersions": {"test": "1.0"},
        },
        "device": {
            "displayName": "Synthetic Test iPhone",
            "machineIdentifier": "iPhone15,3",
            "systemName": "iOS",
            "systemVersion": "test-only",
            "systemBuild": "test-only",
            "physicalMemoryBytes": 1,
        },
        "environment": {
            "buildConfiguration": "Release",
            "debuggerAttached": False,
            "lowPowerModeEnabled": False,
            "batteryState": "unplugged",
            "batteryLevelPercentAtStart": 80,
            "thermalStateAtSessionStart": "nominal",
            "thermalStateAtSessionEnd": "nominal",
        },
        "modelPreparation": {
            "artifactID": "test/artifact",
            "artifactRevision": "b" * 40,
            "cacheVerificationMethod": "synthetic-test-only",
            "downloadOccurredDuringSession": False,
            "preparationCompleted": True,
            "modelLoadCompleted": True,
            "eligibleForPerformanceMeasurement": True,
            "reasonCodes": [],
            "preparedAt": "2026-07-13T11:59:00Z",
        },
        "attempts": attempts,
        "summary": {
            "terminalCounts": {
                "completed": 5,
                "failed": 0,
                "cancelled": 0,
                "outOfMemory": 0,
                "notRun": 0,
                "earlyEOS": 5,
            },
            "metrics": {
                "medianPipelineTTFTMilliseconds": median("pipelineTTFTMilliseconds"),
                "medianFirstRenderableProxyTTFTMilliseconds": median("firstRenderableProxyTTFTMilliseconds") if ux else None,
                "medianRequestCompletionMilliseconds": median("requestCompletionMilliseconds") if ux else None,
                "medianPrefillTokensPerSecond": median("prefillTokensPerSecond"),
                "medianDecodeTokensPerSecond": median("decodeTokensPerSecond"),
                "medianProcessPhysicalFootprintMiB": median("processPhysicalFootprintMiB"),
                "decodeFirstToLastPercentChange": ((decode_last / decode_first) - 1) * 100 if not ux else None,
            },
        },
    }


def refresh_summary(result: dict) -> None:
    measured = result["attempts"][1:]
    completed = [attempt for attempt in measured if attempt["outcome"] == "completed"]
    fields = [
        "pipelineTTFTMilliseconds",
        "firstRenderableProxyTTFTMilliseconds",
        "requestCompletionMilliseconds",
        "prefillTokensPerSecond",
        "decodeTokensPerSecond",
        "processPhysicalFootprintMiB",
    ]
    summary_fields = [
        "medianPipelineTTFTMilliseconds",
        "medianFirstRenderableProxyTTFTMilliseconds",
        "medianRequestCompletionMilliseconds",
        "medianPrefillTokensPerSecond",
        "medianDecodeTokensPerSecond",
        "medianProcessPhysicalFootprintMiB",
    ]
    for attempt_field, summary_field in zip(fields, summary_fields):
        values = [
            attempt["derivedMetrics"][attempt_field]
            for attempt in completed
            if attempt["derivedMetrics"][attempt_field] is not None
        ]
        result["summary"]["metrics"][summary_field] = (
            statistics.median(values) if len(values) >= 3 else None
        )
    first = result["attempts"][1]["derivedMetrics"]["decodeTokensPerSecond"]
    last = result["attempts"][5]["derivedMetrics"]["decodeTokensPerSecond"]
    result["summary"]["metrics"]["decodeFirstToLastPercentChange"] = (
        ((last / first) - 1) * 100
        if result["execution"]["workloadID"].startswith("b-pipe") and first and last
        else None
    )
    result["summary"]["terminalCounts"] = {
        outcome: sum(attempt["outcome"] == outcome for attempt in measured)
        for outcome in ("completed", "failed", "cancelled", "outOfMemory", "notRun")
    }
    result["summary"]["terminalCounts"]["earlyEOS"] = sum(
        attempt["outcome"] == "completed" and attempt["stopReason"] == "endOfSequence"
        for attempt in measured
    )


class PowerResultFreezeTests(unittest.TestCase):
    def test_release_manifest_assets_are_immutable(self) -> None:
        self.assertEqual(verify_release_assets(), [])

    def test_release_manifest_pins_exact_scope_and_future_runner_gate(self) -> None:
        manifest = json.loads(
            (
                ROOT
                / "benchmarks/suite-b-on-device-performance/releases/suite-b-power-1.0.0-rc.1.json"
            ).read_text()
        )
        self.assertEqual(manifest["releaseVersion"], "1.0.0-rc.1")
        self.assertEqual(manifest["status"], "schema-validator-frozen")
        self.assertFalse(manifest["officialResultEligible"])
        self.assertFalse(manifest["rankingAuthorized"])
        self.assertEqual(
            [workload["id"] for workload in manifest["workloads"]],
            ["b-ux-001-short-interaction", "b-pipe-001-sustained-generation"],
        )
        self.assertEqual(manifest["referenceRunner"]["minimumVersion"], "0.8.0")
        self.assertEqual(manifest["referenceRunner"]["implementationStatus"], "pending-f4")

    def test_attempt_reason_registry_matches_validator_taxonomy(self) -> None:
        registry = json.loads(
            (
                ROOT
                / "benchmarks/suite-b-on-device-performance/power-1.0-validation-reasons.json"
            ).read_text()
        )
        self.assertEqual(
            {
                outcome: set(reasons)
                for outcome, reasons in registry["attempt_reason_codes"].items()
            },
            ATTEMPT_REASON_CODES,
        )

    def test_pipeline_evidence_is_recalculated_but_never_rank_authorized(self) -> None:
        report = validate(valid_result())
        self.assertEqual(validate_report_shape(report), [])
        self.assertEqual(report["overallStatus"], "validWithWarnings")
        self.assertTrue(report["structuralValidity"]["valid"])
        self.assertTrue(report["protocolConformance"]["valid"])
        self.assertTrue(report["metricEligibility"]["decode_tokens_per_second@1"]["eligible"])
        self.assertFalse(report["rankingEligibility"]["eligible"])
        self.assertEqual(report["evidenceLevel"]["level"], "unreviewed")

    def test_short_interaction_proxy_is_recalculated_from_trace(self) -> None:
        result = valid_result("b-ux-001-short-interaction")
        self.assertTrue(validate(result)["protocolConformance"]["valid"])
        result["attempts"][1]["renderabilityTrace"]["entries"][0]["decodedAtNanoseconds"] += 1_000_000
        self.assertEqual(validate(result)["overallStatus"], "invalid")

    def test_short_interaction_response_gate_is_recomputed_from_text(self) -> None:
        result = valid_result("b-ux-001-short-interaction")
        result["attempts"][1]["generatedText"] = "Done."
        report = validate(result)
        self.assertEqual(report["overallStatus"], "invalid")
        self.assertTrue(any("response conformance" in error for error in report["errors"]))

    def test_tampered_raw_token_evidence_invalidates_derived_metrics(self) -> None:
        result = valid_result()
        result["attempts"][2]["tokenEvents"][2]["elapsedNanoseconds"] += 10_000_000
        report = validate(result)
        self.assertEqual(report["overallStatus"], "invalid")
        self.assertTrue(any("derivedMetrics" in error for error in report["errors"]))

    def test_failed_attempt_is_retained_but_excluded_per_metric(self) -> None:
        result = valid_result()
        failed = result["attempts"][1]
        failed.update({
            "outcome": "failed",
            "reasonCodes": ["runtime_error"],
            "stopReason": None,
            "generatedText": None,
            "promptTokenCount": None,
            "outputTokenCount": None,
            "responseConformance": {"status": "notEvaluated", "reasonCodes": []},
            "timingEvidence": {
                "generationStartNanoseconds": None,
                "promptEvaluationNanoseconds": None,
                "requestCompletionNanoseconds": None,
            },
            "tokenEvents": [],
            "renderabilityTrace": None,
            "memorySamples": [],
            "derivedMetrics": {key: None for key in failed["derivedMetrics"]},
        })
        refresh_summary(result)
        report = validate(result)
        self.assertEqual(report["overallStatus"], "validWithWarnings")
        self.assertEqual(
            report["metricEligibility"]["decode_tokens_per_second@1"]["eligibleMeasuredAttempts"],
            4,
        )
        self.assertFalse(
            report["metricEligibility"]["decode_first_to_last_percent_change@1"]["eligible"]
        )

    def test_outcome_reason_codes_cannot_cross_taxonomy(self) -> None:
        result = valid_result()
        failed = result["attempts"][1]
        failed["outcome"] = "outOfMemory"
        failed["reasonCodes"] = ["runtime_error"]
        failed["stopReason"] = None
        failed["derivedMetrics"] = {key: None for key in failed["derivedMetrics"]}
        report = validate(result)
        self.assertEqual(report["overallStatus"], "invalid")
        self.assertTrue(any("non-completed outcome" in error for error in report["errors"]))

    def test_historical_foundation_schema_is_not_silently_promoted(self) -> None:
        result = valid_result()
        result["schemaVersion"] = "suite-b-result-bundle-0.4"
        report = validate(result)
        self.assertEqual(report["overallStatus"], "invalid")
        self.assertFalse(report["structuralValidity"]["valid"])

    def test_reference_runner_minimum_is_enforced(self) -> None:
        result = valid_result()
        result["execution"]["runnerVersion"] = "0.7.0"
        report = validate(result)
        self.assertEqual(report["overallStatus"], "invalid")
        self.assertIn("runner_incompatible", report["protocolConformance"]["reasonCodes"])

    def test_environment_failure_is_structural_but_not_protocol_valid(self) -> None:
        result = valid_result()
        result["environment"]["batteryLevelPercentAtStart"] = 20
        report = validate(result)
        self.assertTrue(report["structuralValidity"]["valid"])
        self.assertFalse(report["protocolConformance"]["valid"])
        self.assertIn("environment_ineligible", report["protocolConformance"]["reasonCodes"])
        self.assertFalse(
            report["metricEligibility"]["decode_tokens_per_second@1"]["eligible"]
        )
        self.assertIn(
            "environment_ineligible",
            report["metricEligibility"]["decode_tokens_per_second@1"]["reasonCodes"],
        )

    def test_public_schema_freezes_raw_recalculation_evidence_and_taxonomy(self) -> None:
        schema = json.loads(
            (ROOT / "schemas/suite-b-power-result-1.0.0-rc.1.schema.json").read_text()
        )
        attempt = schema["$defs"]["attempt"]
        self.assertIn("memorySamples", attempt["required"])
        self.assertIn("timingEvidence", attempt["required"])
        self.assertEqual(
            attempt["properties"]["outcome"]["enum"],
            ["completed", "failed", "cancelled", "outOfMemory", "notRun"],
        )

    def test_public_schema_constraints_are_executed_by_the_validator(self) -> None:
        result = valid_result()
        del result["model"]["displayName"]
        report = validate(result)
        self.assertEqual(report["overallStatus"], "invalid")
        self.assertFalse(report["structuralValidity"]["valid"])
        self.assertTrue(any("displayName is required" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
