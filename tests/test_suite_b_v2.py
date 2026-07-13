from __future__ import annotations

import json
import hashlib
import unittest
from pathlib import Path

from scripts.validate_suite_b_bundle import validate
from scripts.validate_suite_b_workload import validate as validate_workload


ROOT = Path(__file__).resolve().parents[1]
WORKLOADS = ROOT / "benchmarks" / "suite-b-on-device-performance" / "workloads"


def attempt(run_index: int, role: str, scale: float = 1.0) -> dict:
    first = int(100_000_000 * scale)
    second = first + int(20_000_000 * scale)
    third = second + int(20_000_000 * scale)
    decode = 2 / ((third - first) / 1_000_000_000)
    return {
        "runIndex": run_index,
        "role": role,
        "outcome": "completed",
        "errorMessage": None,
        "promptTokenCount": 235,
        "outputTokenCount": 3,
        "stopReason": "endOfSequence",
        "thermalStateBefore": "nominal",
        "thermalStateAfter": "nominal",
        "memorySamplingIntervalMilliseconds": 50,
        "metrics": {
            "ttftMilliseconds": first / 1_000_000,
            "prefillTokensPerSecond": 470 / scale,
            "decodeTokensPerSecond": decode,
            "peakMemoryMegabytes": 720 * scale,
            "p50TokenIntervalMilliseconds": 20 * scale,
            "p95TokenIntervalMilliseconds": 20 * scale,
            "p99TokenIntervalMilliseconds": 20 * scale,
        },
        "tokenEvents": [
            {"index": 0, "tokenID": 10, "elapsedNanoseconds": first},
            {"index": 1, "tokenID": 11, "elapsedNanoseconds": second},
            {"index": 2, "tokenID": 12, "elapsedNanoseconds": third},
        ],
    }


def valid_bundle() -> dict:
    attempts = [attempt(0, "warmup")] + [
        attempt(index, "measured", 1 + (index - 1) * 0.01)
        for index in range(1, 6)
    ]
    measured = attempts[1:]

    def median(metric: str) -> float:
        values = sorted(value["metrics"][metric] for value in measured)
        return values[len(values) // 2]

    first, last = measured[0], measured[-1]

    def change(metric: str) -> float:
        return (last["metrics"][metric] / first["metrics"][metric] - 1) * 100

    return {
        "schemaVersion": "suite-b-pilot-bundle-0.3",
        "resultID": "fixture-result-id",
        "createdAt": "2026-07-10T13:01:48Z",
        "officialResultEligible": False,
        "plan": {
            "id": "suite-b-pilot-001",
            "version": "0.1.0",
            "promptSHA256": "a" * 64,
            "warmupRuns": 1,
            "measuredRuns": 5,
            "outputTokenLimit": 512,
        },
        "model": {},
        "runtime": {},
        "device": {},
        "eligibility": {
            "officialLeaderboard": {
                "eligible": False,
                "reasonCodes": ["pilot_protocol_not_official"],
            }
        },
        "summary": {
            "successfulMeasuredRuns": 5,
            "failedMeasuredRuns": 0,
            "medianTTFTMilliseconds": median("ttftMilliseconds"),
            "medianPrefillTokensPerSecond": median("prefillTokensPerSecond"),
            "medianDecodeTokensPerSecond": median("decodeTokensPerSecond"),
            "medianPeakMemoryMegabytes": median("peakMemoryMegabytes"),
            "finalThermalState": "nominal",
            "degradation": {
                "firstMeasuredRunIndex": 1,
                "lastMeasuredRunIndex": 5,
                "decodePercentChange": change("decodeTokensPerSecond"),
                "ttftPercentChange": change("ttftMilliseconds"),
                "prefillPercentChange": change("prefillTokensPerSecond"),
            },
        },
        "attempts": attempts,
    }


def valid_0_5_bundle() -> dict:
    bundle = valid_bundle()
    prompt_hash = "b865ad1a1993bfd7bf097b85f7c5585e44f1384fa291b9c05426c6051caba996"
    bundle["schemaVersion"] = "suite-b-pilot-bundle-0.5"
    bundle["plan"]["version"] = "0.3.0"
    bundle["plan"]["promptSHA256"] = prompt_hash
    bundle["plan"]["v2ProfileMapping"] = (
        "b-pipe-001-sustained-generation@0.1.0-draft"
    )
    bundle["workload"] = {
        "id": "suite-b-pilot-001-fixed-generation",
        "version": "1.0",
        "category": "pipeline",
        "promptSHA256": prompt_hash,
    }
    bundle["measurementMode"] = {
        "id": "b-mode-sustained-no-rest-v1",
        "timingBoundaryVersion": "mlx-pilot-pipeline-boundaries-1",
        "pipelineTTFTStart": "prepared",
        "pipelineTTFTEnd": "raw-token",
        "userVisibleTTFTAvailable": False,
        "prefillSource": "mlx",
        "decodeFormula": "documented",
        "memoryMetric": "TASK_VM_INFO.phys_footprint",
        "memorySamplingIntervalMilliseconds": 50,
    }
    bundle["generationConfiguration"] = {
        "samplingEnabled": False,
        "temperature": 0,
        "topP": None,
        "topK": None,
        "seed": None,
        "repetitionPenalty": None,
        "thinkingMode": "disabled-via-prompt-directive",
        "chatTemplateIdentity": "artifact-tokenizer-config",
        "includeStopTokenInRawEvents": False,
        "outputTokenLimit": 512,
        "contextPolicy": "new-context-for-each-generation",
        "modelLoadPolicy": "load-once-before-warmup",
        "kvCachePolicy": "new-cache-for-each-generation",
    }
    bundle["model"] = {
        "displayName": "Qwen3 0.6B",
        "baseModelID": "Qwen/Qwen3-0.6B",
        "artifactID": "mlx-community/Qwen3-0.6B-4bit",
        "artifactRevision": "73e3e38d981303bc594367cd910ea6eb48349da8",
        "quantization": "4-bit",
        "modelFormat": "MLX Safetensors",
        "artifactContentHash": None,
    }
    bundle["runtime"] = {
        "name": "MLX Swift LM",
        "version": "3.31.4",
        "resolvedRevision": "bd4b7434e6bdb588c7ef55706ff8904cb7fd4c57",
        "backend": "MLX/Metal",
        "mlxSwiftVersion": "0.31.6",
        "mlxSwiftRevision": "0bb916c67f4b9e5c682cbe02a42c701c93ab5021",
        "downloaderPackage": "swift-huggingface 0.9.0",
        "tokenizerPackage": "swift-transformers 1.3.0",
    }
    bundle["device"] = {
        "displayName": "iPhone 14 Pro Max (iPhone15,3)",
        "machineIdentifier": "iPhone15,3",
        "systemName": "iOS",
        "systemVersion": "26.5",
        "systemBuild": "23F77",
        "debuggerAttached": False,
        "buildConfiguration": "Release",
        "appVersion": "0.3.0",
        "appBuild": "3",
        "appSourceCommit": None,
        "lowPowerModeEnabled": False,
        "batteryLevelPercent": 75,
        "batteryState": "unplugged",
    }
    bundle["modelPreparation"] = {
        "artifactID": "mlx-community/Qwen3-0.6B-4bit",
        "artifactRevision": "73e3e38d981303bc594367cd910ea6eb48349da8",
        "cacheStateBeforePreparation": "cached",
        "downloadOccurredDuringSession": False,
        "preparationDurationMilliseconds": 500,
        "preparationCompleted": True,
        "modelLoadCompleted": True,
        "eligibleForPerformanceMeasurement": True,
        "reasonCodes": [],
        "cacheVerificationMethod": (
            "huggingface_revision_manifest_cached_file_size_v1"
        ),
        "preparedAt": "2026-07-10T13:00:00Z",
    }
    return bundle


def valid_0_6_bundle() -> dict:
    bundle = valid_0_5_bundle()
    bundle["schemaVersion"] = "suite-b-pilot-bundle-0.6"
    bundle["plan"].update({
        "id": "b-pipe-001-validation",
        "version": "0.2.0-pilot",
        "v2ProfileMapping": "b-pipe-001-sustained-generation@0.2.0-pilot",
    })
    bundle["workload"].update({
        "id": "b-pipe-001-sustained-generation",
        "version": "0.2.0-pilot",
    })
    return bundle


class WorkloadManifestTests(unittest.TestCase):
    def test_four_draft_workloads_have_distinct_ids(self) -> None:
        manifests = [json.loads(path.read_text()) for path in sorted(WORKLOADS.glob("*.json"))]
        self.assertEqual(len(manifests), 4)
        self.assertEqual(len({item["workload_id"] for item in manifests}), 4)
        self.assertEqual(
            {item["category"] for item in manifests},
            {"user-experience", "pipeline"},
        )
        self.assertTrue(all(not item["official_result_eligible"] for item in manifests))
        self.assertTrue(all(validate_workload(item) == [] for item in manifests))

    def test_sustained_generation_is_frozen_pipeline_workload(self) -> None:
        manifest = json.loads(
            (WORKLOADS / "b-pipe-001-sustained-generation.json").read_text()
        )
        self.assertEqual(manifest["legacy_pilot_mapping"], "suite-b-pilot-001")
        self.assertEqual(manifest["workload_version"], "0.2.0-pilot")
        self.assertEqual(manifest["status"], "pilot-validated")
        self.assertEqual(manifest["category"], "pipeline")
        self.assertEqual(manifest["procedure"]["warmup_runs"], 1)
        self.assertEqual(manifest["procedure"]["measured_runs"], 5)
        self.assertEqual(manifest["generation"]["kv_cache_policy"], "new-cache-for-each-generation")

    def test_short_interaction_candidate_has_frozen_fixture_and_policy(self) -> None:
        workload_path = WORKLOADS / "b-ux-001-short-interaction.json"
        workload = json.loads(workload_path.read_text())
        fixture_path = ROOT / workload["input"]["fixture_path"]

        self.assertEqual(workload["status"], "pilot-validated")
        self.assertEqual(workload["output"]["maximum_tokens"], 128)
        self.assertFalse(workload["generation"]["sampling"])
        self.assertEqual(workload["generation"]["temperature"], 0)
        self.assertFalse(
            workload["generation"]["chat_template_context"]["enable_thinking"]
        )
        self.assertEqual(
            workload["visible_content_policy"]["unobservable_behavior"],
            "report user_visible_ttft_ms as null and mark measurement boundary unverified",
        )
        self.assertEqual(
            hashlib.sha256(fixture_path.read_bytes()).hexdigest(),
            workload["input"]["sha256"],
        )

    def test_input_sweep_requires_exact_pre_generation_calibration(self) -> None:
        workload = json.loads(
            (WORKLOADS / "b-pipe-002-input-length-sweep.json").read_text()
        )
        self.assertEqual(workload["status"], "pilot-validated")
        self.assertEqual(
            workload["input"]["target_model_input_tokens"]["values"],
            [32, 128, 512, 2048],
        )
        self.assertIn(
            "exactly equal",
            workload["fixture_calibration"]["acceptance"],
        )
        self.assertEqual(
            workload["fixture_calibration"]["failure_behavior"],
            "block measurement; do not use nearest length",
        )
        self.assertFalse(
            workload["ordering_policy"]["generation_before_calibration"]
        )
        calibration = workload["fixture_calibration"]
        for point in calibration["reference_profile"]["points"]:
            prompt = calibration["base_text"] + calibration["padding_unit"] * point[
                "padding_repetitions"
            ]
            self.assertEqual(
                hashlib.sha256(prompt.encode()).hexdigest(),
                point["prompt_sha256"],
            )

    def test_context_assistance_pilot_freezes_sources_and_answer_contract(self) -> None:
        workload = json.loads(
            (WORKLOADS / "b-ux-002-context-assistance.json").read_text()
        )
        self.assertEqual(workload["status"], "pilot-validated")
        self.assertEqual(workload["workload_version"], "0.2.0-pilot")
        for path_key, hash_key in (
            ("fixture_path", "sha256"),
            ("question_path", "question_sha256"),
        ):
            path = ROOT / workload["input"][path_key]
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(),
                workload["input"][hash_key],
            )
        self.assertEqual(
            [variant["target_model_input_tokens"] for variant in workload["variants"]],
            [1024, 2048],
        )
        contract = workload["minimum_answer_contract"]
        self.assertEqual(contract["required_reference_code"], "ORCHID-47")
        self.assertEqual(len(contract["required_facts"]), 4)
        self.assertFalse(workload["generation"]["sampling"])
        document = (ROOT / workload["input"]["fixture_path"]).read_text()
        question = (ROOT / workload["input"]["question_path"]).read_text()
        for variant in workload["context_extension"]["reference_profile"]["variants"]:
            prompt = document + "\nBackground records appendix:" \
                + " x" * variant["padding_repetitions"] \
                + "\n\nQuestion:\n" + question
            self.assertEqual(
                hashlib.sha256(prompt.encode()).hexdigest(),
                variant["prompt_sha256"],
            )


class PilotBundleValidatorTests(unittest.TestCase):
    def test_valid_bundle_recalculates_cleanly(self) -> None:
        self.assertEqual(validate(valid_bundle()), [])

    def test_current_0_4_identity_and_power_fields_are_required(self) -> None:
        bundle = valid_bundle()
        bundle["schemaVersion"] = "suite-b-pilot-bundle-0.4"
        bundle["plan"]["v2ProfileMapping"] = (
            "b-pipe-001-sustained-generation@0.1.0-draft"
        )
        bundle["workload"] = {
            "id": "pilot",
            "version": "1.0",
            "category": "pipeline",
            "promptSHA256": "a" * 64,
        }
        bundle["measurementMode"] = {
            "id": "mode",
            "timingBoundaryVersion": "1",
            "pipelineTTFTStart": "prepared",
            "pipelineTTFTEnd": "raw-token",
            "userVisibleTTFTAvailable": False,
            "decodeFormula": "documented",
            "memoryMetric": "physical-footprint",
        }
        bundle["generationConfiguration"] = {
            "samplingEnabled": False,
            "temperature": 0,
            "topP": None,
            "topK": None,
            "seed": None,
            "repetitionPenalty": None,
            "thinkingMode": "model-default",
            "chatTemplateIdentity": "artifact",
            "outputTokenLimit": 512,
            "kvCachePolicy": "new",
        }
        bundle["model"] = {
            "baseModelID": "base",
            "artifactID": "artifact",
            "artifactRevision": "a" * 40,
            "quantization": "4-bit",
            "modelFormat": "MLX",
            "artifactContentHash": None,
        }
        bundle["runtime"] = {
            "name": "MLX Swift LM",
            "version": "3.31.4",
            "resolvedRevision": "b" * 40,
            "backend": "MLX/Metal",
            "mlxSwiftVersion": "0.31.6",
            "mlxSwiftRevision": "c" * 40,
            "downloaderPackage": "swift-huggingface 0.9.0",
            "tokenizerPackage": "swift-transformers 1.3.0",
        }
        bundle["device"] = {
            "appSourceCommit": None,
            "lowPowerModeEnabled": False,
            "batteryLevelPercent": 75,
            "batteryState": "unplugged",
        }
        self.assertEqual(validate(bundle), [])

        del bundle["generationConfiguration"]
        self.assertIn(
            "generationConfiguration must be an object",
            validate(bundle),
        )

    def test_0_5_model_preparation_is_validated(self) -> None:
        bundle = valid_0_5_bundle()
        self.assertEqual(validate(bundle), [])

        bundle["modelPreparation"]["artifactRevision"] = "b" * 40
        self.assertIn(
            "modelPreparation.artifactRevision must match model",
            validate(bundle),
        )

    def test_0_5_download_cannot_be_marked_eligible(self) -> None:
        bundle = valid_0_5_bundle()
        bundle["modelPreparation"]["cacheStateBeforePreparation"] = "not_cached"
        bundle["modelPreparation"]["downloadOccurredDuringSession"] = True
        self.assertIn(
            "downloaded model cannot be eligible in the same App session",
            validate(bundle),
        )

    def test_0_5_unknown_cache_cannot_be_marked_eligible(self) -> None:
        bundle = valid_0_5_bundle()
        bundle["modelPreparation"]["cacheStateBeforePreparation"] = "unknown"
        self.assertIn(
            "unknown model cache state cannot be eligible",
            validate(bundle),
        )

    def test_0_6_uses_frozen_b_pipe_001_identity(self) -> None:
        self.assertEqual(validate(valid_0_6_bundle()), [])

    def test_0_6_rejects_legacy_workload_identity(self) -> None:
        bundle = valid_0_6_bundle()
        bundle["workload"]["id"] = "suite-b-pilot-001-fixed-generation"
        self.assertTrue(
            any("workload.id is unsupported" in error for error in validate(bundle))
        )

    def test_0_5_legacy_bundle_remains_supported(self) -> None:
        self.assertEqual(validate(valid_0_5_bundle()), [])

    def test_official_flag_is_rejected(self) -> None:
        bundle = valid_bundle()
        bundle["officialResultEligible"] = True
        self.assertIn("pilot officialResultEligible must be false", validate(bundle))

    def test_non_contiguous_token_index_is_rejected(self) -> None:
        bundle = valid_bundle()
        bundle["attempts"][1]["tokenEvents"][1]["index"] = 9
        self.assertTrue(
            any("index must equal 1" in error for error in validate(bundle))
        )

    def test_summary_must_match_raw_attempts(self) -> None:
        bundle = valid_bundle()
        bundle["summary"]["medianDecodeTokensPerSecond"] = 999
        self.assertIn(
            "summary.medianDecodeTokensPerSecond does not match attempts",
            validate(bundle),
        )


if __name__ == "__main__":
    unittest.main()
