#!/usr/bin/env python3
"""Validate and recalculate non-official Suite B pilot result bundles."""

from __future__ import annotations

import json
import math
import statistics
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


SUPPORTED_SCHEMAS = {
    "suite-b-pilot-bundle-0.2",
    "suite-b-pilot-bundle-0.3",
    "suite-b-pilot-bundle-0.4",
    "suite-b-pilot-bundle-0.5",
    "suite-b-pilot-bundle-0.6",
}
THERMAL_STATES = {"nominal", "fair", "serious", "critical", "unknown"}


def is_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def close(actual: Any, expected: float, *, tolerance: float = 1e-6) -> bool:
    if not is_number(actual):
        return False
    return math.isclose(float(actual), expected, rel_tol=tolerance, abs_tol=tolerance)


def require_object(data: dict[str, Any], name: str, errors: list[str]) -> dict[str, Any]:
    value = data.get(name)
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return {}
    return value


def require_keys(
    value: dict[str, Any],
    name: str,
    keys: tuple[str, ...],
    errors: list[str],
) -> None:
    for key in keys:
        if key not in value:
            errors.append(f"{name}.{key} is required")


def validate_token_events(attempt: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    events = attempt.get("tokenEvents")
    if not isinstance(events, list):
        return [f"{label}.tokenEvents must be an array"]

    previous_elapsed = -1
    for expected_index, event in enumerate(events):
        if not isinstance(event, dict):
            errors.append(f"{label}.tokenEvents[{expected_index}] must be an object")
            continue
        if event.get("index") != expected_index:
            errors.append(
                f"{label}.tokenEvents[{expected_index}].index must equal {expected_index}"
            )
        elapsed = event.get("elapsedNanoseconds")
        if not isinstance(elapsed, int) or isinstance(elapsed, bool) or elapsed < 0:
            errors.append(
                f"{label}.tokenEvents[{expected_index}].elapsedNanoseconds "
                "must be a non-negative integer"
            )
        elif elapsed <= previous_elapsed:
            errors.append(f"{label}.tokenEvents timestamps must be strictly increasing")
        else:
            previous_elapsed = elapsed

    output_count = attempt.get("outputTokenCount")
    if attempt.get("outcome") == "completed" and output_count != len(events):
        errors.append(f"{label}.outputTokenCount must match tokenEvents length")

    metrics = attempt.get("metrics")
    if not isinstance(metrics, dict):
        errors.append(f"{label}.metrics must be an object")
        return errors

    if events:
        expected_ttft = events[0]["elapsedNanoseconds"] / 1_000_000
        if not close(metrics.get("ttftMilliseconds"), expected_ttft):
            errors.append(f"{label}.metrics.ttftMilliseconds does not match raw events")

    if len(events) > 1:
        duration = (
            events[-1]["elapsedNanoseconds"] - events[0]["elapsedNanoseconds"]
        ) / 1_000_000_000
        expected_decode = (len(events) - 1) / duration
        if not close(metrics.get("decodeTokensPerSecond"), expected_decode):
            errors.append(
                f"{label}.metrics.decodeTokensPerSecond does not match raw events"
            )

    return errors


def successful_measured(attempts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        attempt
        for attempt in attempts
        if attempt.get("role") == "measured" and attempt.get("outcome") == "completed"
    ]


def validate_summary(data: dict[str, Any], attempts: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    summary = require_object(data, "summary", errors)
    successful = successful_measured(attempts)
    measured = [attempt for attempt in attempts if attempt.get("role") == "measured"]

    if summary.get("successfulMeasuredRuns") != len(successful):
        errors.append("summary.successfulMeasuredRuns does not match attempts")
    if summary.get("failedMeasuredRuns") != len(measured) - len(successful):
        errors.append("summary.failedMeasuredRuns does not match attempts")

    fields = {
        "medianTTFTMilliseconds": "ttftMilliseconds",
        "medianPrefillTokensPerSecond": "prefillTokensPerSecond",
        "medianDecodeTokensPerSecond": "decodeTokensPerSecond",
        "medianPeakMemoryMegabytes": "peakMemoryMegabytes",
    }
    for summary_name, metric_name in fields.items():
        values = [
            attempt.get("metrics", {}).get(metric_name)
            for attempt in successful
            if is_number(attempt.get("metrics", {}).get(metric_name))
        ]
        expected = statistics.median(values) if values else None
        actual = summary.get(summary_name)
        if expected is None:
            if actual is not None:
                errors.append(f"summary.{summary_name} must be null")
        elif not close(actual, expected):
            errors.append(f"summary.{summary_name} does not match attempts")

    if attempts:
        expected_final = attempts[-1].get("thermalStateAfter")
        if summary.get("finalThermalState") != expected_final:
            errors.append("summary.finalThermalState does not match final attempt")

    degradation = summary.get("degradation")
    if not isinstance(degradation, dict):
        errors.append("summary.degradation must be an object")
    elif successful:
        first = successful[0]
        last = successful[-1]
        if degradation.get("firstMeasuredRunIndex") != first.get("runIndex"):
            errors.append("summary.degradation first run index does not match")
        if degradation.get("lastMeasuredRunIndex") != last.get("runIndex"):
            errors.append("summary.degradation last run index does not match")
        mappings = {
            "decodePercentChange": "decodeTokensPerSecond",
            "ttftPercentChange": "ttftMilliseconds",
            "prefillPercentChange": "prefillTokensPerSecond",
        }
        for output_name, metric_name in mappings.items():
            first_value = first.get("metrics", {}).get(metric_name)
            last_value = last.get("metrics", {}).get(metric_name)
            if is_number(first_value) and is_number(last_value) and first_value != 0:
                expected = (last_value / first_value - 1) * 100
                if not close(degradation.get(output_name), expected):
                    errors.append(f"summary.degradation.{output_name} does not match")

    return errors


def validate(data: dict[str, Any]) -> list[str]:
    if data.get("schemaVersion") == "suite-b-result-bundle-0.1":
        from scripts.validate_suite_b_result_bundle import validate as validate_unified
        return validate_unified(data)
    errors: list[str] = []
    schema = data.get("schemaVersion")
    if schema not in SUPPORTED_SCHEMAS:
        errors.append(f"unsupported schemaVersion: {schema!r}")
    if data.get("officialResultEligible") is not False:
        errors.append("pilot officialResultEligible must be false")

    plan = require_object(data, "plan", errors)
    expected_plan_id = (
        "b-pipe-001-validation"
        if schema == "suite-b-pilot-bundle-0.6"
        else "suite-b-pilot-001"
    )
    if plan.get("id") != expected_plan_id:
        errors.append(f"plan.id must be {expected_plan_id}")
    if plan.get("warmupRuns") != 1 or plan.get("measuredRuns") != 5:
        errors.append("pilot plan must declare 1 warm-up and 5 measured runs")
    prompt_hash = plan.get("promptSHA256")
    if not isinstance(prompt_hash, str) or len(prompt_hash) != 64:
        errors.append("plan.promptSHA256 must be a 64-character digest")

    for name in ("model", "runtime", "device"):
        require_object(data, name, errors)

    attempts_value = data.get("attempts")
    if not isinstance(attempts_value, list):
        return errors + ["attempts must be an array"]
    attempts = [value for value in attempts_value if isinstance(value, dict)]
    if len(attempts) != len(attempts_value):
        errors.append("every attempt must be an object")

    warmups = [attempt for attempt in attempts if attempt.get("role") == "warmup"]
    measured = [attempt for attempt in attempts if attempt.get("role") == "measured"]
    if len(warmups) != 1:
        errors.append("pilot bundle must retain exactly one warm-up attempt")
    if len(measured) != 5:
        errors.append("pilot bundle must retain exactly five measured attempts")

    for position, attempt in enumerate(attempts):
        label = f"attempts[{position}]"
        if attempt.get("outcome") not in {"completed", "failed", "notRun"}:
            errors.append(f"{label}.outcome is unsupported")
        for thermal_key in ("thermalStateBefore", "thermalStateAfter"):
            if attempt.get(thermal_key) not in THERMAL_STATES:
                errors.append(f"{label}.{thermal_key} is unsupported")
        errors.extend(validate_token_events(attempt, label))

    errors.extend(validate_summary(data, attempts))

    eligibility = data.get("eligibility")
    if schema in {
        "suite-b-pilot-bundle-0.3",
        "suite-b-pilot-bundle-0.4",
        "suite-b-pilot-bundle-0.5",
        "suite-b-pilot-bundle-0.6",
    }:
        if not isinstance(eligibility, dict):
            errors.append("0.3 bundles require eligibility decisions")
        else:
            official = eligibility.get("officialLeaderboard")
            if not isinstance(official, dict) or official.get("eligible") is not False:
                errors.append("pilot officialLeaderboard eligibility must be false")

    if schema in {"suite-b-pilot-bundle-0.4", "suite-b-pilot-bundle-0.5", "suite-b-pilot-bundle-0.6"}:
        require_keys(plan, "plan", ("v2ProfileMapping",), errors)
        workload = require_object(data, "workload", errors)
        measurement = require_object(data, "measurementMode", errors)
        generation = require_object(data, "generationConfiguration", errors)
        require_keys(
            workload,
            "workload",
            ("id", "version", "category", "promptSHA256"),
            errors,
        )
        require_keys(
            measurement,
            "measurementMode",
            (
                "id",
                "timingBoundaryVersion",
                "pipelineTTFTStart",
                "pipelineTTFTEnd",
                "userVisibleTTFTAvailable",
                "decodeFormula",
                "memoryMetric",
            ),
            errors,
        )
        require_keys(
            generation,
            "generationConfiguration",
            (
                "samplingEnabled",
                "temperature",
                "topP",
                "topK",
                "seed",
                "repetitionPenalty",
                "thinkingMode",
                "chatTemplateIdentity",
                "outputTokenLimit",
                "kvCachePolicy",
            ),
            errors,
        )
        model = data.get("model", {})
        runtime = data.get("runtime", {})
        if isinstance(model, dict):
            require_keys(
                model,
                "model",
                (
                    "baseModelID",
                    "artifactID",
                    "artifactRevision",
                    "quantization",
                    "modelFormat",
                    "artifactContentHash",
                ),
                errors,
            )
        if isinstance(runtime, dict):
            require_keys(
                runtime,
                "runtime",
                (
                    "name",
                    "version",
                    "resolvedRevision",
                    "backend",
                    "mlxSwiftVersion",
                    "mlxSwiftRevision",
                    "downloaderPackage",
                    "tokenizerPackage",
                ),
                errors,
            )
        device = data.get("device", {})
        if isinstance(device, dict):
            require_keys(
                device,
                "device",
                (
                    "appSourceCommit",
                    "lowPowerModeEnabled",
                    "batteryLevelPercent",
                    "batteryState",
                ),
                errors,
            )
            if not isinstance(device.get("lowPowerModeEnabled"), bool):
                errors.append("0.4 device.lowPowerModeEnabled must be boolean")
            if device.get("batteryState") not in {
                "unknown", "unplugged", "charging", "full"
            }:
                errors.append("0.4 device.batteryState is unsupported")

    if schema in {"suite-b-pilot-bundle-0.5", "suite-b-pilot-bundle-0.6"}:
        require_keys(
            measurement,
            "measurementMode",
            ("prefillSource", "memorySamplingIntervalMilliseconds"),
            errors,
        )
        require_keys(
            generation,
            "generationConfiguration",
            (
                "includeStopTokenInRawEvents",
                "contextPolicy",
                "modelLoadPolicy",
            ),
            errors,
        )
        expected_plan_version = "0.2.0-pilot" if schema.endswith("0.6") else "0.3.0"
        if plan.get("version") != expected_plan_version:
            errors.append(f"{schema} plan.version must be {expected_plan_version}")
        if plan.get("promptSHA256") != (
            "b865ad1a1993bfd7bf097b85f7c5585e44f1384fa291b9c05426c6051caba996"
        ):
            errors.append(f"{schema} plan.promptSHA256 does not match the frozen workload")
        if plan.get("outputTokenLimit") != 512:
            errors.append(f"{schema} plan.outputTokenLimit must be 512")
        expected_mapping = (
            "b-pipe-001-sustained-generation@0.2.0-pilot"
            if schema.endswith("0.6")
            else "b-pipe-001-sustained-generation@0.1.0-draft"
        )
        if plan.get("v2ProfileMapping") != expected_mapping:
            errors.append(f"{schema} plan.v2ProfileMapping is unsupported")

        workload = require_object(data, "workload", errors)
        expected_workload_id = "b-pipe-001-sustained-generation" if schema.endswith("0.6") else "suite-b-pilot-001-fixed-generation"
        expected_workload_version = "0.2.0-pilot" if schema.endswith("0.6") else "1.0"
        if workload.get("id") != expected_workload_id:
            errors.append(f"{schema} workload.id is unsupported")
        if workload.get("version") != expected_workload_version or workload.get("category") != "pipeline":
            errors.append(f"{schema} workload identity is unsupported")
        if workload.get("promptSHA256") != plan.get("promptSHA256"):
            errors.append("0.5 workload prompt hash must match plan")

        model = require_object(data, "model", errors)
        runtime = require_object(data, "runtime", errors)
        require_keys(model, "model", ("displayName",), errors)
        if model.get("artifactID") != "mlx-community/Qwen3-0.6B-4bit":
            errors.append("0.5 model.artifactID is unsupported")
        if model.get("artifactRevision") != (
            "73e3e38d981303bc594367cd910ea6eb48349da8"
        ):
            errors.append("0.5 model.artifactRevision is unsupported")
        expected_runtime = {
            "name": "MLX Swift LM",
            "version": "3.31.4",
            "resolvedRevision": "bd4b7434e6bdb588c7ef55706ff8904cb7fd4c57",
            "mlxSwiftVersion": "0.31.6",
            "mlxSwiftRevision": "0bb916c67f4b9e5c682cbe02a42c701c93ab5021",
        }
        for key, expected in expected_runtime.items():
            if runtime.get(key) != expected:
                errors.append(f"0.5 runtime.{key} does not match the Pilot plan")

        device = require_object(data, "device", errors)
        require_keys(
            device,
            "device",
            (
                "displayName",
                "machineIdentifier",
                "systemName",
                "systemVersion",
                "systemBuild",
                "debuggerAttached",
                "buildConfiguration",
                "appVersion",
                "appBuild",
            ),
            errors,
        )

        preparation = require_object(data, "modelPreparation", errors)
        require_keys(
            preparation,
            "modelPreparation",
            (
                "artifactID",
                "artifactRevision",
                "cacheStateBeforePreparation",
                "downloadOccurredDuringSession",
                "preparationDurationMilliseconds",
                "preparationCompleted",
                "modelLoadCompleted",
                "eligibleForPerformanceMeasurement",
                "reasonCodes",
                "cacheVerificationMethod",
                "preparedAt",
            ),
            errors,
        )
        if preparation.get("artifactID") != model.get("artifactID"):
            errors.append("modelPreparation.artifactID must match model")
        if preparation.get("artifactRevision") != model.get("artifactRevision"):
            errors.append("modelPreparation.artifactRevision must match model")
        cache_state = preparation.get("cacheStateBeforePreparation")
        if cache_state not in {"cached", "not_cached", "incomplete", "unknown"}:
            errors.append("modelPreparation.cacheStateBeforePreparation is unsupported")
        downloaded = preparation.get("downloadOccurredDuringSession")
        preparation_eligible = preparation.get("eligibleForPerformanceMeasurement")
        if not isinstance(downloaded, bool):
            errors.append("modelPreparation.downloadOccurredDuringSession must be boolean")
        if not isinstance(preparation_eligible, bool):
            errors.append("modelPreparation.eligibleForPerformanceMeasurement must be boolean")
        for key in ("preparationCompleted", "modelLoadCompleted"):
            if not isinstance(preparation.get(key), bool):
                errors.append(f"modelPreparation.{key} must be boolean")
        duration = preparation.get("preparationDurationMilliseconds")
        if not is_number(duration) or duration < 0:
            errors.append(
                "modelPreparation.preparationDurationMilliseconds must be non-negative"
            )
        reason_codes = preparation.get("reasonCodes")
        if not isinstance(reason_codes, list) or not all(
            isinstance(reason, str) and reason for reason in reason_codes
        ):
            errors.append("modelPreparation.reasonCodes must be a string array")
        elif len(reason_codes) != len(set(reason_codes)):
            errors.append("modelPreparation.reasonCodes must not contain duplicates")
        prepared_at = preparation.get("preparedAt")
        try:
            if not isinstance(prepared_at, str):
                raise ValueError
            datetime.fromisoformat(prepared_at.replace("Z", "+00:00"))
        except ValueError:
            errors.append("modelPreparation.preparedAt must be an ISO-8601 timestamp")
        if downloaded and preparation_eligible:
            errors.append("downloaded model cannot be eligible in the same App session")
        if cache_state == "unknown" and preparation_eligible:
            errors.append("unknown model cache state cannot be eligible")
        if preparation_eligible and (
            cache_state != "cached"
            or preparation.get("preparationCompleted") is not True
            or preparation.get("modelLoadCompleted") is not True
        ):
            errors.append("eligible model preparation must be cached and fully loaded")
        if preparation.get("cacheVerificationMethod") != (
            "huggingface_revision_manifest_cached_file_size_v1"
        ):
            errors.append("modelPreparation.cacheVerificationMethod is unsupported")

        session_validity = eligibility.get("sessionValidity", {})
        if preparation_eligible is False and isinstance(session_validity, dict) \
                and session_validity.get("eligible") is True:
            errors.append("ineligible model preparation cannot produce an eligible session")
        if downloaded and isinstance(session_validity, dict) \
                and session_validity.get("eligible") is True:
            errors.append("downloaded model cannot produce an eligible session")
        if cache_state == "unknown" and isinstance(session_validity, dict) \
                and session_validity.get("eligible") is True:
            errors.append("unknown cache state cannot produce an eligible session")

    return errors


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError("top-level JSON value must be an object")
    return data


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: validate_suite_b_bundle.py <bundle.json> [...]", file=sys.stderr)
        return 2

    failed = False
    for raw_path in sys.argv[1:]:
        path = Path(raw_path)
        try:
            errors = validate(load(path))
        except (OSError, json.JSONDecodeError, ValueError) as error:
            errors = [f"invalid JSON: {error}"]
        if errors:
            failed = True
            for error in errors:
                print(f"{path}: {error}", file=sys.stderr)
        else:
            print(f"{path}: valid Suite B pilot bundle")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
