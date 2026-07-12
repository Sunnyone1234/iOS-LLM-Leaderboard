from __future__ import annotations

import copy
import hashlib
import json
import statistics
import tempfile
import unittest
import uuid
from pathlib import Path

from scripts.generate_suite_b_pilot import (
    CONTRACTS,
    MODEL_PROFILES,
    validate_and_normalize,
    write_outputs,
)


def make_attempt(
    workload_id: str,
    run_index: int,
    role: str,
) -> dict:
    is_ux = workload_id == "b-ux-001-short-interaction"
    output_count = 4 if is_ux else 256
    prompt_count = 70 if is_ux else 235
    first = 100_000_000 + run_index * 1_000_000
    interval = 10_000_000
    events = [
        {
            "index": index,
            "tokenID": index + 1,
            "elapsedNanoseconds": first + index * interval,
        }
        for index in range(output_count)
    ]
    decode = (output_count - 1) / (
        (events[-1]["elapsedNanoseconds"] - events[0]["elapsedNanoseconds"])
        / 1_000_000_000
    )
    metrics = {
        "ttftMilliseconds": first / 1_000_000,
        "userVisibleTTFTMilliseconds": first / 1_000_000 + 20 if is_ux else None,
        "requestCompletionMilliseconds": first / 1_000_000 + 200 if is_ux else None,
        "prefillTokensPerSecond": 500.0,
        "decodeTokensPerSecond": decode,
        "peakMemoryMegabytes": 700.0,
        "p50TokenIntervalMilliseconds": 10.0,
        "p95TokenIntervalMilliseconds": 10.0,
        "p99TokenIntervalMilliseconds": 10.0,
    }
    return {
        "runIndex": run_index,
        "role": role,
        "outcome": "completed",
        "errorMessage": None,
        "promptTokenCount": prompt_count,
        "outputTokenCount": output_count,
        "stopReason": "endOfSequence" if is_ux else "outputTokenLimit",
        "visibleText": "The note is safe locally and will sync when connectivity returns."
        if is_ux
        else None,
        "thermalStateBefore": "nominal",
        "thermalStateAfter": "nominal",
        "memorySamplingIntervalMilliseconds": 50,
        "metrics": metrics,
        "tokenEvents": events,
    }


def make_bundle(
    workload_id: str,
    schema_version: str = "suite-b-result-bundle-0.2",
    artifact_id: str = "mlx-community/Qwen3-0.6B-4bit",
) -> dict:
    contract = CONTRACTS[workload_id]
    profile = MODEL_PROFILES[artifact_id]
    attempts = [make_attempt(workload_id, 0, "warmup")] + [
        make_attempt(workload_id, index, "measured") for index in range(1, 6)
    ]
    successful = attempts[1:]
    medians = {
        "medianPipelineTTFTMilliseconds": statistics.median(
            attempt["metrics"]["ttftMilliseconds"] for attempt in successful
        ),
        "medianUserVisibleTTFTMilliseconds": statistics.median(
            attempt["metrics"]["userVisibleTTFTMilliseconds"] for attempt in successful
        )
        if contract.user_visible_ttft
        else None,
        "medianRequestCompletionMilliseconds": statistics.median(
            attempt["metrics"]["requestCompletionMilliseconds"] for attempt in successful
        )
        if contract.user_visible_ttft
        else None,
        "medianPrefillTokensPerSecond": 500.0,
        "medianDecodeTokensPerSecond": 100.0,
        "medianPeakMemoryMegabytes": 700.0,
    }
    model = {
        "displayName": profile["displayName"],
        "baseModelID": profile["baseModelID"],
        "artifactID": artifact_id,
        "artifactRevision": profile["artifactRevision"],
        "quantization": profile["quantization"],
        "modelFormat": profile["modelFormat"],
        "artifactContentHash": None,
    }
    if schema_version == "suite-b-result-bundle-0.3":
        model.update(profile)
        model["artifactID"] = artifact_id
        model["compatibilityConstraints"] = [
            "runtime:MLX-Swift-LM-3.31.4",
            "backend:MLX/Metal",
            "architecture:qwen3-dense",
            "pilot-reference-device:iPhone15,3",
            "physical-run-required-before-publication",
        ]
        model["artifactContentHash"] = None
    runtime = {
        "name": "MLX Swift LM",
        "version": "3.31.4",
        "resolvedRevision": "bd4b7434e6bdb588c7ef55706ff8904cb7fd4c57",
        "backend": "MLX/Metal",
        "mlxSwiftVersion": "0.31.6",
        "mlxSwiftRevision": "0bb916c67f4b9e5c682cbe02a42c701c93ab5021",
        "downloaderPackage": "swift-huggingface 0.9.0",
        "tokenizerPackage": "swift-transformers 1.3.0",
    }
    device = {
        "displayName": "iPhone 14 Pro Max",
        "machineIdentifier": "iPhone15,3",
        "systemName": "iOS",
        "systemVersion": "26.5",
        "systemBuild": "23F79",
        "debuggerAttached": False,
        "buildConfiguration": "Release",
        "appVersion": "0.6.0"
        if schema_version == "suite-b-result-bundle-0.3"
        else "0.5.0",
        "appBuild": "8"
        if schema_version == "suite-b-result-bundle-0.3"
        else "7",
        "appSourceCommit": "abcdef0123456789abcdef0123456789abcdef01",
        "lowPowerModeEnabled": False,
        "batteryLevelPercent": 80.0,
        "batteryState": "unplugged",
    }
    preparation = {
        "artifactID": model["artifactID"],
        "artifactRevision": model["artifactRevision"],
        "cacheStateBeforePreparation": "cached",
        "downloadOccurredDuringSession": False,
        "preparationDurationMilliseconds": 10.0,
        "preparationCompleted": True,
        "modelLoadCompleted": True,
        "eligibleForPerformanceMeasurement": True,
        "reasonCodes": [],
        "cacheVerificationMethod": "huggingface_revision_manifest_cached_file_size_v1",
        "preparedAt": "2026-07-12T10:00:00Z",
    }
    generation = {
        "samplingEnabled": False,
        "temperature": 0.0,
        "topP": contract.top_p,
        "topK": contract.top_k,
        "seed": contract.seed,
        "repetitionPenalty": None,
        "thinkingMode": contract.thinking_mode,
        "chatTemplateIdentity": contract.chat_template_identity,
        "includeStopTokenInRawEvents": False,
        "outputTokenLimit": contract.output_token_limit,
        "contextPolicy": "new-context-for-each-generation",
        "modelLoadPolicy": "load-once-before-warmup",
        "kvCachePolicy": "new-cache-for-each-generation",
    }
    bundle = {
        "schemaVersion": schema_version,
        "resultID": str(uuid.uuid4()),
        "createdAt": "2026-07-12T10:10:00Z",
        "officialResultEligible": False,
        "plan": {
            "id": contract.plan_id,
            "version": "0.2.0-pilot",
            "runnerKind": contract.runner_kind,
            "warmupRuns": 1,
            "measuredRuns": 5,
            "outputTokenLimit": contract.output_token_limit,
            "requiredPowerSource": "unplugged",
            "minimumBatteryLevelPercent": 50.0,
        },
        "workload": {
            "id": workload_id,
            "version": "0.2.0-pilot",
            "category": contract.category,
            "fixtureSHA256": [contract.fixture_sha256],
        },
        "measurementMode": {
            "id": contract.measurement_mode_id,
            "timingBoundaryVersion": contract.timing_boundary_version,
            "pipelineTTFTStart": "after-chat-template-and-tokenization-immediately-before-generateTokensTask",
            "pipelineTTFTEnd": "first-raw-token-received-by-adapter",
            "userVisibleTTFTAvailable": contract.user_visible_ttft,
            "prefillSource": "mlx-generate-completion-info-prompt-time",
            "decodeFormula": "(raw_token_count-1)/(last_raw_token_time-first_raw_token_time)",
            "memoryMetric": "TASK_VM_INFO.phys_footprint",
            "memorySamplingIntervalMilliseconds": 50,
        },
        "generationConfiguration": generation,
        "model": model,
        "runtime": runtime,
        "device": device,
        "modelPreparation": preparation,
        "eligibility": {
            "sessionValid": True,
            "officialLeaderboardEligible": False,
            "reasonCodes": ["pilot_protocol_not_official"],
        },
        "sessions": [
            {
                "id": "default",
                "fixtureSHA256": contract.fixture_sha256,
                "performanceEligible": True,
                "timingEvidenceRetained": True,
                "summary": {
                    "successfulMeasuredRuns": 5,
                    "failedMeasuredRuns": 0,
                    "modelInputTokens": successful[0]["promptTokenCount"],
                    **medians,
                    "finalThermalState": "nominal",
                },
                "attempts": attempts,
            }
        ],
    }
    if workload_id == "b-pipe-001-sustained-generation":
        bundle["bundleSummary"] = {
            "firstMeasuredRunIndex": 1,
            "lastMeasuredRunIndex": 5,
            "decodePercentChange": 0.0,
            "ttftPercentChange": (105.0 / 101.0 - 1) * 100,
            "prefillPercentChange": 0.0,
        }
    return bundle


def normalize(bundle: dict) -> tuple[dict | None, list[str]]:
    raw = json.dumps(bundle, sort_keys=True).encode()
    return validate_and_normalize(
        bundle,
        source_name="test-result.json",
        source_sha256=hashlib.sha256(raw).hexdigest(),
    )


class PilotValidationTests(unittest.TestCase):
    def test_both_pilot_workloads_normalize_as_eligible(self) -> None:
        for workload_id in CONTRACTS:
            with self.subTest(workload_id=workload_id):
                row, errors = normalize(make_bundle(workload_id))
                self.assertEqual(errors, [])
                self.assertIsNotNone(row)
                self.assertTrue(row["pilotEligibility"]["eligible"])
                if workload_id == "b-ux-001-short-interaction":
                    self.assertFalse(
                        row["metricInterpretation"]["screenVisibleLatencyMeasured"]
                    )
                    self.assertIn(
                    "First-renderable proxy TTFT",
                        row["metricInterpretation"]["label"],
                    )

    def test_raw_token_metrics_are_recalculated(self) -> None:
        bundle = make_bundle("b-pipe-001-sustained-generation")
        bundle["sessions"][0]["attempts"][2]["metrics"]["decodeTokensPerSecond"] = 999
        row, errors = normalize(bundle)
        self.assertIsNone(row)
        self.assertTrue(any("decodeTokensPerSecond" in error for error in errors))

    def test_bundle_03_accepts_exact_three_fixed_profiles(self) -> None:
        for artifact_id in MODEL_PROFILES:
            with self.subTest(artifact_id=artifact_id):
                bundle = make_bundle(
                    "b-pipe-001-sustained-generation",
                    schema_version="suite-b-result-bundle-0.3",
                    artifact_id=artifact_id,
                )
                row, errors = normalize(bundle)
                self.assertEqual(errors, [])
                self.assertTrue(row["pilotEligibility"]["eligible"])
                self.assertEqual(
                    row["configuration"]["model"]["artifactID"],
                    artifact_id,
                )

    def test_bundle_03_rejects_unlisted_or_mislabeled_profile(self) -> None:
        bundle = make_bundle(
            "b-ux-001-short-interaction",
            schema_version="suite-b-result-bundle-0.3",
        )
        bundle["model"]["artifactID"] = "mlx-community/not-a-pilot-profile"
        bundle["modelPreparation"]["artifactID"] = bundle["model"]["artifactID"]
        row, errors = normalize(bundle)
        self.assertIsNone(row)
        self.assertTrue(any("fixed Pilot v0.1 profile" in error for error in errors))

    def test_exported_summary_must_match_attempts(self) -> None:
        bundle = make_bundle("b-ux-001-short-interaction")
        bundle["sessions"][0]["summary"]["medianUserVisibleTTFTMilliseconds"] = 1
        row, errors = normalize(bundle)
        self.assertIsNone(row)
        self.assertTrue(any("medianUserVisibleTTFTMilliseconds" in error for error in errors))

    def test_only_two_workloads_are_supported(self) -> None:
        bundle = make_bundle("b-pipe-001-sustained-generation")
        bundle["workload"]["id"] = "b-pipe-002-input-length-sweep"
        row, errors = normalize(bundle)
        self.assertIsNone(row)
        self.assertIn("workload.id is not supported by Pilot v0.1", errors)

    def test_valid_but_ineligible_environment_is_not_ranked(self) -> None:
        bundle = make_bundle("b-ux-001-short-interaction")
        bundle["device"]["lowPowerModeEnabled"] = True
        bundle["eligibility"]["sessionValid"] = False
        row, errors = normalize(bundle)
        self.assertEqual(errors, [])
        self.assertFalse(row["pilotEligibility"]["eligible"])
        self.assertIn("session_environment_ineligible", row["pilotEligibility"]["reasonCodes"])

    def test_missing_runner_source_identity_is_a_warning(self) -> None:
        bundle = make_bundle("b-pipe-001-sustained-generation")
        bundle["device"]["appSourceCommit"] = None
        row, errors = normalize(bundle)
        self.assertEqual(errors, [])
        self.assertTrue(row["pilotEligibility"]["eligible"])
        self.assertIn("runner_source_identity_missing", row["pilotEligibility"]["warningCodes"])

    def test_short_b_pipe_output_is_a_warning_not_an_eligibility_gate(self) -> None:
        bundle = make_bundle("b-pipe-001-sustained-generation")
        for attempt in bundle["sessions"][0]["attempts"]:
            attempt["tokenEvents"] = attempt["tokenEvents"][:32]
            attempt["outputTokenCount"] = 32
        row, errors = normalize(bundle)
        self.assertEqual(errors, [])
        self.assertTrue(row["pilotEligibility"]["eligible"])
        self.assertIn(
            "output_below_256_tokens_not_an_eligibility_gate",
            row["pilotEligibility"]["warningCodes"],
        )

    def test_legacy_app_and_other_runtime_are_rejected(self) -> None:
        legacy = make_bundle("b-pipe-001-sustained-generation")
        legacy["device"]["appVersion"] = "0.4.0"
        legacy["device"]["appBuild"] = "6"
        row, errors = normalize(legacy)
        self.assertIsNone(row)
        self.assertTrue(any("device.appVersion" in error for error in errors))
        self.assertTrue(any("device.appBuild" in error for error in errors))

        other_runtime = make_bundle("b-pipe-001-sustained-generation")
        other_runtime["runtime"]["name"] = "Other Runtime"
        other_runtime["runtime"]["backend"] = "Other Backend"
        row, errors = normalize(other_runtime)
        self.assertIsNone(row)
        self.assertTrue(any("runtime.name" in error for error in errors))
        self.assertTrue(any("runtime.backend" in error for error in errors))

    def test_ux_proxy_must_have_possible_timing_order(self) -> None:
        bundle = make_bundle("b-ux-001-short-interaction")
        for attempt in bundle["sessions"][0]["attempts"]:
            attempt["metrics"]["userVisibleTTFTMilliseconds"] = 1.0
        bundle["sessions"][0]["summary"][
            "medianUserVisibleTTFTMilliseconds"
        ] = 1.0
        row, errors = normalize(bundle)
        self.assertIsNone(row)
        self.assertTrue(
            any("adapter proxy cannot precede Pipeline TTFT" in error for error in errors)
        )


class PilotGenerationTests(unittest.TestCase):
    def test_empty_input_generates_explicit_empty_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_directory = root / "raw"
            output_directory = root / "output"
            input_directory.mkdir()
            counts = write_outputs(input_directory, output_directory)
            self.assertEqual(counts, (0, 0, 0))
            leaderboard = (output_directory / "LEADERBOARD.md").read_text()
            self.assertIn(
                "No eligible Pilot results are available",
                leaderboard,
            )
            self.assertIn("First-renderable proxy TTFT", leaderboard)
            self.assertIn(
                "No eligible Pilot results are available",
                (output_directory / "SHIP-EVIDENCE.md").read_text(),
            )

    def test_real_shape_generates_full_configuration_and_ship_facts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_directory = root / "raw"
            output_directory = root / "output"
            input_directory.mkdir()
            bundle = make_bundle("b-pipe-001-sustained-generation")
            (input_directory / "result.json").write_text(json.dumps(bundle))
            counts = write_outputs(input_directory, output_directory)
            self.assertEqual(counts, (1, 1, 0))
            leaderboard = (output_directory / "LEADERBOARD.md").read_text()
            ship = (output_directory / "SHIP-EVIDENCE.md").read_text()
            self.assertIn("mlx-community/Qwen3-0.6B-4bit", leaderboard)
            self.assertIn("MLX Swift LM", leaderboard)
            self.assertIn("iPhone15,3", leaderboard)
            self.assertIn("Completion / failure evidence", leaderboard)
            self.assertIn("Status vocabulary", ship)
            self.assertIn("Artifact size", ship)
            self.assertIn("Offline execution", ship)
            self.assertIn("Streaming", ship)
            self.assertIn("Minimum tested device", ship)
            self.assertIn(
                "Supported — per-token adapter events were retained",
                ship,
            )
            self.assertIn("Verified — tested on iPhone 14 Pro Max", ship)
            self.assertIn("Unknown — not recorded in result bundle", ship)
            normalized = json.loads(
                (output_directory / "normalized-results.json").read_text()
            )
            self.assertEqual(normalized["eligibleResultCount"], 1)

    def test_ship_groups_workloads_despite_run_specific_battery_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_directory = root / "raw"
            output_directory = root / "output"
            input_directory.mkdir()
            pipe = make_bundle("b-pipe-001-sustained-generation")
            ux = make_bundle("b-ux-001-short-interaction")
            ux["device"]["batteryLevelPercent"] = 79.0
            (input_directory / "pipe.json").write_text(json.dumps(pipe))
            (input_directory / "ux.json").write_text(json.dumps(ux))

            self.assertEqual(
                write_outputs(input_directory, output_directory),
                (2, 2, 0),
            )
            ship = (output_directory / "SHIP-EVIDENCE.md").read_text()
            self.assertEqual(
                ship.count("Verified — mlx-community/Qwen3-0.6B-4bit@"),
                1,
            )
            self.assertIn("b-pipe-001-sustained-generation", ship)
            self.assertIn("b-ux-001-short-interaction", ship)

    def test_bundle_03_ship_view_includes_source_size_and_license_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_directory = root / "raw"
            output_directory = root / "output"
            input_directory.mkdir()
            bundle = make_bundle(
                "b-pipe-001-sustained-generation",
                schema_version="suite-b-result-bundle-0.3",
                artifact_id="mlx-community/Qwen3-1.7B-4bit",
            )
            (input_directory / "result.json").write_text(json.dumps(bundle))

            self.assertEqual(
                write_outputs(input_directory, output_directory),
                (1, 1, 0),
            )
            ship = (output_directory / "SHIP-EVIDENCE.md").read_text()
            self.assertIn("979,502,864 bytes", ship)
            self.assertIn("Qwen3-1.7B-4bit/tree/3b1b176", ship)
            self.assertIn("apache-2.0 metadata", ship)
            self.assertIn("no legal conclusion", ship)
            self.assertNotIn("physical-run-required-before-publication", ship)
            self.assertIn("reference-runtime-only", ship)

    def test_ineligible_partial_evidence_remains_visible_but_unranked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_directory = root / "raw"
            output_directory = root / "output"
            input_directory.mkdir()
            bundle = make_bundle("b-ux-001-short-interaction")
            bundle["device"]["lowPowerModeEnabled"] = True
            bundle["eligibility"]["sessionValid"] = False
            (input_directory / "result.json").write_text(json.dumps(bundle))
            self.assertEqual(write_outputs(input_directory, output_directory), (1, 0, 0))
            leaderboard = (output_directory / "LEADERBOARD.md").read_text()
            self.assertIn("Non-ranked valid or partial Pilot evidence", leaderboard)
            self.assertIn("5 completed, 0 failed, 0 not run", leaderboard)
            self.assertIn("session_environment_ineligible", leaderboard)


if __name__ == "__main__":
    unittest.main()
