#!/usr/bin/env python3
"""Validate and publish the narrow internal Suite B Pilot v0.1 data views.

This intentionally supports only App-generated ``suite-b-result-bundle-0.2``
files for B-UX-001 and B-PIPE-001. It is not an official result validator and
does not implement submission, trust, or governance state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "results" / "suite-b-pilot-v0.1"
DEFAULT_INPUT = DEFAULT_ROOT / "raw"
PIPELINE_VERSION = "suite-b-pilot-data-pipeline-0.1"
RESULT_SCHEMAS = {
    "suite-b-result-bundle-0.2": ("0.5.0", "7"),
    "suite-b-result-bundle-0.3": ("0.6.0", "8"),
}
THERMAL_STATES = {"nominal", "fair", "serious", "critical", "unknown"}
DEVICE_PATTERN = re.compile(r"^iPhone[0-9]+,[0-9]+$")
REFERENCE_RUNTIME = {
    "name": "MLX Swift LM",
    "version": "3.31.4",
    "resolvedRevision": "bd4b7434e6bdb588c7ef55706ff8904cb7fd4c57",
    "backend": "MLX/Metal",
    "mlxSwiftVersion": "0.31.6",
    "mlxSwiftRevision": "0bb916c67f4b9e5c682cbe02a42c701c93ab5021",
    "downloaderPackage": "swift-huggingface 0.9.0",
    "tokenizerPackage": "swift-transformers 1.3.0",
}
MODEL_PROFILES = {
    "mlx-community/Qwen3-0.6B-4bit": {
        "displayName": "Qwen3 0.6B",
        "baseModelID": "Qwen/Qwen3-0.6B",
        "artifactRevision": "73e3e38d981303bc594367cd910ea6eb48349da8",
        "modelFamily": "Qwen3 dense",
        "parameterSizeClass": "small-0.6b",
        "quantization": "4-bit",
        "modelFormat": "MLX Safetensors",
        "tokenizerIdentity": "mlx-community/Qwen3-0.6B-4bit@73e3e38d981303bc594367cd910ea6eb48349da8/tokenizer_config.json",
        "sourceURL": "https://huggingface.co/mlx-community/Qwen3-0.6B-4bit/tree/73e3e38d981303bc594367cd910ea6eb48349da8",
        "licenseIdentifier": "apache-2.0",
        "licenseSourceURL": "https://huggingface.co/Qwen/Qwen3-0.6B/blob/c1899de289a04d12100db370d81485cdf75e47ca/LICENSE",
        "artifactRepositorySizeBytes": 682_323_786,
    },
    "mlx-community/Qwen3-1.7B-4bit": {
        "displayName": "Qwen3 1.7B",
        "baseModelID": "Qwen/Qwen3-1.7B",
        "artifactRevision": "3b1b1768f8f8cf8351c712464f906e86c2b8269e",
        "modelFamily": "Qwen3 dense",
        "parameterSizeClass": "medium-1.7b",
        "quantization": "4-bit",
        "modelFormat": "MLX Safetensors",
        "tokenizerIdentity": "mlx-community/Qwen3-1.7B-4bit@3b1b1768f8f8cf8351c712464f906e86c2b8269e/tokenizer_config.json",
        "sourceURL": "https://huggingface.co/mlx-community/Qwen3-1.7B-4bit/tree/3b1b1768f8f8cf8351c712464f906e86c2b8269e",
        "licenseIdentifier": "apache-2.0",
        "licenseSourceURL": "https://huggingface.co/Qwen/Qwen3-1.7B/blob/70d244cc86ccca08cf5af4e1e306ecf908b1ad5e/LICENSE",
        "artifactRepositorySizeBytes": 979_502_864,
    },
    "mlx-community/Qwen3-4B-3bit": {
        "displayName": "Qwen3 4B",
        "baseModelID": "Qwen/Qwen3-4B",
        "artifactRevision": "c4e8054c71facfa84f781cdb7c1ffab3f09f89bf",
        "modelFamily": "Qwen3 dense",
        "parameterSizeClass": "large-4b",
        "quantization": "3-bit",
        "modelFormat": "MLX Safetensors",
        "tokenizerIdentity": "mlx-community/Qwen3-4B-3bit@c4e8054c71facfa84f781cdb7c1ffab3f09f89bf/tokenizer_config.json",
        "sourceURL": "https://huggingface.co/mlx-community/Qwen3-4B-3bit/tree/c4e8054c71facfa84f781cdb7c1ffab3f09f89bf",
        "licenseIdentifier": "apache-2.0",
        "licenseSourceURL": "https://huggingface.co/Qwen/Qwen3-4B/blob/1cfa9a7208912126459214e8b04321603b3df60c/LICENSE",
        "artifactRepositorySizeBytes": 1_771_660_929,
    },
}
METRICS = (
    "ttftMilliseconds",
    "userVisibleTTFTMilliseconds",
    "requestCompletionMilliseconds",
    "prefillTokensPerSecond",
    "decodeTokensPerSecond",
    "peakMemoryMegabytes",
    "p50TokenIntervalMilliseconds",
    "p95TokenIntervalMilliseconds",
    "p99TokenIntervalMilliseconds",
)
SUMMARY_METRICS = {
    "medianPipelineTTFTMilliseconds": "ttftMilliseconds",
    "medianUserVisibleTTFTMilliseconds": "userVisibleTTFTMilliseconds",
    "medianRequestCompletionMilliseconds": "requestCompletionMilliseconds",
    "medianPrefillTokensPerSecond": "prefillTokensPerSecond",
    "medianDecodeTokensPerSecond": "decodeTokensPerSecond",
    "medianPeakMemoryMegabytes": "peakMemoryMegabytes",
}


@dataclass(frozen=True)
class PilotContract:
    workload_id: str
    title: str
    plan_id: str
    category: str
    runner_kind: str
    fixture_sha256: str
    output_token_limit: int
    thinking_mode: str
    measurement_mode_id: str
    timing_boundary_version: str
    user_visible_ttft: bool
    top_p: float | None
    top_k: int | None
    seed: int | None
    chat_template_identity: str
    primary_summary_field: str
    primary_label: str
    primary_higher_is_better: bool
    prompt_token_minimum: int
    prompt_token_maximum: int
    output_token_warning_minimum: int | None = None


CONTRACTS = {
    "b-ux-001-short-interaction": PilotContract(
        workload_id="b-ux-001-short-interaction",
        title="B-UX-001 Short Interaction",
        plan_id="b-ux-001-validation",
        category="user-experience",
        runner_kind="single-session",
        fixture_sha256="69b3cd45fb67e1882dabdc082636298123e01081c097af65b3fd133b19ccbc84",
        output_token_limit=128,
        thinking_mode="disabled-via-chat-template",
        measurement_mode_id="b-mode-warm-resident-ux-v1",
        timing_boundary_version="mlx-ux-visible-boundaries-1",
        user_visible_ttft=True,
        top_p=1.0,
        top_k=0,
        seed=0,
        chat_template_identity="artifact-tokenizer-config-enable-thinking-false",
        primary_summary_field="medianUserVisibleTTFTMilliseconds",
        primary_label="Median First-renderable proxy TTFT (ms)",
        primary_higher_is_better=False,
        prompt_token_minimum=64,
        prompt_token_maximum=256,
    ),
    "b-pipe-001-sustained-generation": PilotContract(
        workload_id="b-pipe-001-sustained-generation",
        title="B-PIPE-001 Sustained Generation",
        plan_id="b-pipe-001-validation",
        category="pipeline",
        runner_kind="single-session",
        fixture_sha256="b865ad1a1993bfd7bf097b85f7c5585e44f1384fa291b9c05426c6051caba996",
        output_token_limit=512,
        thinking_mode="disabled-via-prompt-directive",
        measurement_mode_id="b-mode-sustained-no-rest-v1",
        timing_boundary_version="mlx-pilot-pipeline-boundaries-1",
        user_visible_ttft=False,
        top_p=None,
        top_k=None,
        seed=None,
        chat_template_identity="artifact-tokenizer-config",
        primary_summary_field="medianDecodeTokensPerSecond",
        primary_label="Median decode (tokens/s)",
        primary_higher_is_better=True,
        prompt_token_minimum=128,
        prompt_token_maximum=512,
        output_token_warning_minimum=256,
    ),
}


def is_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def close(actual: Any, expected: float, tolerance: float = 1e-6) -> bool:
    return is_number(actual) and math.isclose(
        float(actual), expected, rel_tol=tolerance, abs_tol=tolerance
    )


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = fraction * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def median_metric(attempts: list[dict[str, Any]], name: str) -> float | None:
    values = [
        float(attempt["metrics"][name])
        for attempt in attempts
        if is_number(attempt.get("metrics", {}).get(name))
    ]
    return statistics.median(values) if values else None


def percent_change(first: Any, last: Any) -> float | None:
    if not is_number(first) or not is_number(last) or first == 0:
        return None
    return (float(last) / float(first) - 1) * 100


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def require_object(parent: dict[str, Any], key: str, errors: list[str]) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        errors.append(f"{key} must be an object")
        return {}
    return value


def require_strings(value: dict[str, Any], fields: Iterable[str], label: str, errors: list[str]) -> None:
    for field in fields:
        if not isinstance(value.get(field), str) or not value[field].strip():
            errors.append(f"{label}.{field} must be a non-empty string")


def expect(value: dict[str, Any], field: str, expected: Any, label: str, errors: list[str]) -> None:
    actual = value.get(field)
    matches = close(actual, float(expected)) if is_number(expected) else actual == expected
    if not matches:
        errors.append(f"{label}.{field} must be {expected!r}")


def parse_timestamp(value: Any, label: str, errors: list[str]) -> None:
    try:
        if not isinstance(value, str):
            raise ValueError
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{label} must be an ISO-8601 timestamp")


def verify_optional_number(actual: Any, expected: float | None, label: str, errors: list[str]) -> None:
    if expected is None:
        if actual is not None:
            errors.append(f"{label} must be null or absent")
    elif not close(actual, expected):
        errors.append(f"{label} does not match recalculated evidence")


def validate_attempt(
    attempt: dict[str, Any], position: int, errors: list[str]
) -> dict[str, Any]:
    label = f"sessions[0].attempts[{position}]"
    expected_role = "warmup" if position == 0 else "measured"
    if attempt.get("runIndex") != position:
        errors.append(f"{label}.runIndex must equal {position}")
    if attempt.get("role") != expected_role:
        errors.append(f"{label}.role must be {expected_role}")
    if attempt.get("outcome") not in {"completed", "failed", "notRun"}:
        errors.append(f"{label}.outcome is unsupported")
    for field in ("thermalStateBefore", "thermalStateAfter"):
        if attempt.get(field) not in THERMAL_STATES:
            errors.append(f"{label}.{field} is unsupported")
    if attempt.get("memorySamplingIntervalMilliseconds") != 50:
        errors.append(f"{label}.memorySamplingIntervalMilliseconds must be 50")

    metrics = attempt.get("metrics")
    if not isinstance(metrics, dict):
        errors.append(f"{label}.metrics must be an object")
        metrics = {}
    for metric in METRICS:
        observed = metrics.get(metric)
        if observed is not None and (not is_number(observed) or observed < 0):
            errors.append(f"{label}.metrics.{metric} must be non-negative or null")

    events = attempt.get("tokenEvents")
    if not isinstance(events, list):
        errors.append(f"{label}.tokenEvents must be an array")
        events = []
    previous = -1
    for event_position, event in enumerate(events):
        event_label = f"{label}.tokenEvents[{event_position}]"
        if not isinstance(event, dict):
            errors.append(f"{event_label} must be an object")
            continue
        if event.get("index") != event_position:
            errors.append(f"{event_label}.index must equal {event_position}")
        elapsed = event.get("elapsedNanoseconds")
        if not isinstance(event.get("tokenID"), int) or isinstance(event.get("tokenID"), bool):
            errors.append(f"{event_label}.tokenID must be an integer")
        if not isinstance(elapsed, int) or isinstance(elapsed, bool) or elapsed < 0:
            errors.append(f"{event_label}.elapsedNanoseconds must be a non-negative integer")
        elif elapsed <= previous:
            errors.append(f"{label}.token event timestamps must be strictly increasing")
        else:
            previous = elapsed

    completed = attempt.get("outcome") == "completed"
    if completed:
        prompt_count = attempt.get("promptTokenCount")
        output_count = attempt.get("outputTokenCount")
        if not isinstance(prompt_count, int) or isinstance(prompt_count, bool) or prompt_count <= 0:
            errors.append(f"{label}.promptTokenCount must be a positive integer")
        if not isinstance(output_count, int) or isinstance(output_count, bool) or output_count <= 0:
            errors.append(f"{label}.outputTokenCount must be a positive integer")
        elif output_count != len(events):
            errors.append(f"{label}.outputTokenCount must equal tokenEvents length")
        if attempt.get("stopReason") not in {
            "endOfSequence", "outputTokenLimit", "cancelled"
        }:
            errors.append(f"{label}.stopReason is unsupported for a completed attempt")

    valid_event_times = bool(events) and all(
        isinstance(event, dict)
        and isinstance(event.get("elapsedNanoseconds"), int)
        and not isinstance(event.get("elapsedNanoseconds"), bool)
        for event in events
    )
    expected_ttft = (
        events[0]["elapsedNanoseconds"] / 1_000_000 if valid_event_times else None
    )
    expected_decode = None
    intervals: list[float] = []
    if len(events) > 1 and valid_event_times:
        intervals = [
            (events[index]["elapsedNanoseconds"] - events[index - 1]["elapsedNanoseconds"])
            / 1_000_000
            for index in range(1, len(events))
        ]
        duration = (events[-1]["elapsedNanoseconds"] - events[0]["elapsedNanoseconds"]) / 1_000_000_000
        if duration > 0:
            expected_decode = (len(events) - 1) / duration

    verify_optional_number(metrics.get("ttftMilliseconds"), expected_ttft, f"{label}.metrics.ttftMilliseconds", errors)
    verify_optional_number(metrics.get("decodeTokensPerSecond"), expected_decode, f"{label}.metrics.decodeTokensPerSecond", errors)
    for field, fraction in (
        ("p50TokenIntervalMilliseconds", 0.50),
        ("p95TokenIntervalMilliseconds", 0.95),
        ("p99TokenIntervalMilliseconds", 0.99),
    ):
        verify_optional_number(metrics.get(field), percentile(intervals, fraction), f"{label}.metrics.{field}", errors)
    return attempt


def validate_and_normalize(
    data: dict[str, Any], *, source_name: str, source_sha256: str
) -> tuple[dict[str, Any] | None, list[str]]:
    """Return a normalized Pilot row or validation errors."""

    errors: list[str] = []
    schema_version = data.get("schemaVersion")
    if schema_version not in RESULT_SCHEMAS:
        return None, [
            "schemaVersion must be suite-b-result-bundle-0.2 or "
            "suite-b-result-bundle-0.3"
        ]
    result_id = data.get("resultID")
    try:
        uuid.UUID(str(result_id))
    except (ValueError, AttributeError):
        errors.append("resultID must be a UUID")
    parse_timestamp(data.get("createdAt"), "createdAt", errors)
    if data.get("officialResultEligible") is not False:
        errors.append("officialResultEligible must be false for Pilot evidence")

    workload = require_object(data, "workload", errors)
    contract = CONTRACTS.get(workload.get("id"))
    if contract is None:
        return None, errors + ["workload.id is not supported by Pilot v0.1"]
    plan = require_object(data, "plan", errors)
    measurement = require_object(data, "measurementMode", errors)
    generation = require_object(data, "generationConfiguration", errors)
    model = require_object(data, "model", errors)
    runtime = require_object(data, "runtime", errors)
    device = require_object(data, "device", errors)
    preparation = require_object(data, "modelPreparation", errors)
    source_eligibility = require_object(data, "eligibility", errors)

    for field, expected in (
        ("id", contract.plan_id), ("version", "0.2.0-pilot"),
        ("runnerKind", contract.runner_kind), ("warmupRuns", 1),
        ("measuredRuns", 5), ("outputTokenLimit", contract.output_token_limit),
        ("requiredPowerSource", "unplugged"), ("minimumBatteryLevelPercent", 50),
    ):
        expect(plan, field, expected, "plan", errors)
    for field, expected in (
        ("id", contract.workload_id), ("version", "0.2.0-pilot"),
        ("category", contract.category), ("fixtureSHA256", [contract.fixture_sha256]),
    ):
        expect(workload, field, expected, "workload", errors)
    for field, expected in (
        ("id", contract.measurement_mode_id),
        ("timingBoundaryVersion", contract.timing_boundary_version),
        ("userVisibleTTFTAvailable", contract.user_visible_ttft),
        ("memorySamplingIntervalMilliseconds", 50),
    ):
        expect(measurement, field, expected, "measurementMode", errors)
    require_strings(
        measurement,
        ("pipelineTTFTStart", "pipelineTTFTEnd", "prefillSource", "decodeFormula", "memoryMetric"),
        "measurementMode",
        errors,
    )
    for field, expected in (
        ("samplingEnabled", False), ("temperature", 0),
        ("topP", contract.top_p), ("topK", contract.top_k), ("seed", contract.seed),
        ("repetitionPenalty", None), ("thinkingMode", contract.thinking_mode),
        ("chatTemplateIdentity", contract.chat_template_identity),
        ("includeStopTokenInRawEvents", False),
        ("outputTokenLimit", contract.output_token_limit),
        ("contextPolicy", "new-context-for-each-generation"),
        ("modelLoadPolicy", "load-once-before-warmup"),
        ("kvCachePolicy", "new-cache-for-each-generation"),
    ):
        expect(generation, field, expected, "generationConfiguration", errors)

    require_strings(
        model,
        ("displayName", "baseModelID", "artifactID", "artifactRevision", "quantization", "modelFormat"),
        "model",
        errors,
    )
    profile = MODEL_PROFILES.get(model.get("artifactID"))
    if profile is None:
        errors.append("model.artifactID is not a fixed Pilot v0.1 profile")
    else:
        for field in (
            "displayName", "baseModelID", "artifactRevision", "quantization",
            "modelFormat",
        ):
            expect(model, field, profile[field], "model", errors)
        if schema_version == "suite-b-result-bundle-0.2" and model.get(
            "artifactID"
        ) != "mlx-community/Qwen3-0.6B-4bit":
            errors.append("result bundle 0.2 supports only the Stage 1 small profile")
        if schema_version == "suite-b-result-bundle-0.3":
            require_strings(
                model,
                (
                    "modelFamily", "parameterSizeClass", "tokenizerIdentity",
                    "sourceURL", "licenseIdentifier", "licenseSourceURL",
                ),
                "model",
                errors,
            )
            for field in (
                "modelFamily", "parameterSizeClass", "tokenizerIdentity",
                "sourceURL", "licenseIdentifier", "licenseSourceURL",
                "artifactRepositorySizeBytes",
            ):
                expect(model, field, profile[field], "model", errors)
            constraints = model.get("compatibilityConstraints")
            if not isinstance(constraints, list) or not constraints or not all(
                isinstance(value, str) and value for value in constraints
            ):
                errors.append(
                    "model.compatibilityConstraints must be a non-empty string array"
                )
    if model.get("artifactContentHash") is not None and not isinstance(model.get("artifactContentHash"), str):
        errors.append("model.artifactContentHash must be a string or null")
    require_strings(
        runtime,
        ("name", "version", "resolvedRevision", "backend", "mlxSwiftVersion", "mlxSwiftRevision", "downloaderPackage", "tokenizerPackage"),
        "runtime",
        errors,
    )
    for field, expected in REFERENCE_RUNTIME.items():
        expect(runtime, field, expected, "runtime", errors)
    require_strings(
        device,
        ("displayName", "machineIdentifier", "systemName", "systemVersion", "systemBuild", "buildConfiguration", "appVersion", "appBuild"),
        "device",
        errors,
    )
    expected_app_version, expected_app_build = RESULT_SCHEMAS[schema_version]
    expect(device, "appVersion", expected_app_version, "device", errors)
    expect(device, "appBuild", expected_app_build, "device", errors)
    if not DEVICE_PATTERN.fullmatch(str(device.get("machineIdentifier", ""))):
        errors.append("device.machineIdentifier must identify a physical iPhone")
    for field in ("debuggerAttached", "lowPowerModeEnabled"):
        if not isinstance(device.get(field), bool):
            errors.append(f"device.{field} must be boolean")
    battery_level = device.get("batteryLevelPercent")
    if battery_level is not None and (not is_number(battery_level) or not 0 <= battery_level <= 100):
        errors.append("device.batteryLevelPercent must be between 0 and 100 or null")
    if device.get("batteryState") not in {"unknown", "unplugged", "charging", "full"}:
        errors.append("device.batteryState is unsupported")
    if device.get("appSourceCommit") is not None and not isinstance(device.get("appSourceCommit"), str):
        errors.append("device.appSourceCommit must be a string or null")

    require_strings(
        preparation,
        ("artifactID", "artifactRevision", "cacheStateBeforePreparation", "cacheVerificationMethod"),
        "modelPreparation",
        errors,
    )
    if preparation.get("artifactID") != model.get("artifactID"):
        errors.append("modelPreparation.artifactID must match model.artifactID")
    if preparation.get("artifactRevision") != model.get("artifactRevision"):
        errors.append("modelPreparation.artifactRevision must match model.artifactRevision")
    for field in (
        "downloadOccurredDuringSession", "preparationCompleted", "modelLoadCompleted",
        "eligibleForPerformanceMeasurement",
    ):
        if not isinstance(preparation.get(field), bool):
            errors.append(f"modelPreparation.{field} must be boolean")
    parse_timestamp(preparation.get("preparedAt"), "modelPreparation.preparedAt", errors)
    preparation_duration = preparation.get("preparationDurationMilliseconds")
    if not is_number(preparation_duration) or preparation_duration < 0:
        errors.append("modelPreparation.preparationDurationMilliseconds must be non-negative")
    if not isinstance(preparation.get("reasonCodes"), list) or not all(
        isinstance(reason, str) for reason in preparation.get("reasonCodes", [])
    ):
        errors.append("modelPreparation.reasonCodes must be a string array")

    sessions = data.get("sessions")
    if not isinstance(sessions, list) or len(sessions) != 1 or not isinstance(sessions[0], dict):
        return None, errors + ["sessions must contain exactly one object"]
    session = sessions[0]
    if session.get("id") != "default":
        errors.append("sessions[0].id must be default")
    if session.get("targetInputTokens") is not None:
        errors.append("sessions[0].targetInputTokens must be null or absent")
    if session.get("paddingRepetitions") is not None:
        errors.append("sessions[0].paddingRepetitions must be null or absent")
    if session.get("fixtureSHA256") != contract.fixture_sha256:
        errors.append("sessions[0].fixtureSHA256 does not match the Pilot fixture")
    if session.get("timingEvidenceRetained") is not True:
        errors.append("sessions[0].timingEvidenceRetained must be true")
    if session.get("qualityEligible") is not None:
        errors.append("sessions[0].qualityEligible must be null or absent")

    attempts_value = session.get("attempts")
    if not isinstance(attempts_value, list) or len(attempts_value) != 6:
        return None, errors + ["sessions[0].attempts must contain exactly 1 warm-up and 5 measured attempts"]
    attempts: list[dict[str, Any]] = []
    for position, attempt in enumerate(attempts_value):
        if not isinstance(attempt, dict):
            errors.append(f"sessions[0].attempts[{position}] must be an object")
            continue
        attempts.append(validate_attempt(attempt, position, errors))
    if len(attempts) != 6:
        return None, errors

    measured = attempts[1:]
    successful = [attempt for attempt in measured if attempt.get("outcome") == "completed"]
    for position, attempt in enumerate(successful):
        metrics = attempt.get("metrics", {})
        proxy = metrics.get("userVisibleTTFTMilliseconds")
        completion = metrics.get("requestCompletionMilliseconds")
        pipeline = metrics.get("ttftMilliseconds")
        label = f"successful measured attempt {position + 1}"
        if contract.user_visible_ttft:
            if not is_number(proxy):
                errors.append(f"{label} must retain the First-renderable proxy TTFT")
            if not is_number(completion):
                errors.append(f"{label} must retain request completion timing")
            if is_number(proxy) and is_number(pipeline) and proxy < pipeline:
                errors.append(f"{label} adapter proxy cannot precede Pipeline TTFT")
            if is_number(completion) and is_number(proxy) and completion < proxy:
                errors.append(f"{label} request completion cannot precede the adapter proxy")
        elif proxy is not None or completion is not None:
            errors.append(
                f"{label} cannot report user-experience timing for a pipeline-only workload"
            )
    summary = session.get("summary")
    if not isinstance(summary, dict):
        return None, errors + ["sessions[0].summary must be an object"]
    if summary.get("successfulMeasuredRuns") != len(successful):
        errors.append("sessions[0].summary.successfulMeasuredRuns does not match attempts")
    if summary.get("failedMeasuredRuns") != 5 - len(successful):
        errors.append("sessions[0].summary.failedMeasuredRuns does not match attempts")
    expected_performance = len(successful) >= 3
    if session.get("performanceEligible") is not expected_performance:
        errors.append("sessions[0].performanceEligible does not match attempts")
    model_input_tokens = successful[0].get("promptTokenCount") if successful else None
    if summary.get("modelInputTokens") != model_input_tokens:
        errors.append("sessions[0].summary.modelInputTokens does not match the first successful measured attempt")
    recalculated: dict[str, Any] = {
        "successfulMeasuredRuns": len(successful),
        "failedMeasuredRuns": 5 - len(successful),
        "modelInputTokens": model_input_tokens,
    }
    for summary_field, metric_field in SUMMARY_METRICS.items():
        expected = median_metric(successful, metric_field)
        recalculated[summary_field] = expected
        verify_optional_number(summary.get(summary_field), expected, f"sessions[0].summary.{summary_field}", errors)
    expected_final_thermal = attempts[-1].get("thermalStateAfter")
    recalculated["finalThermalState"] = expected_final_thermal
    if summary.get("finalThermalState") != expected_final_thermal:
        errors.append("sessions[0].summary.finalThermalState does not match the last attempt")

    first = successful[0] if successful else None
    last = successful[-1] if successful else None
    recalculated_degradation = {
        "firstMeasuredRunIndex": first.get("runIndex") if first else None,
        "lastMeasuredRunIndex": last.get("runIndex") if last else None,
        "decodePercentChange": percent_change(
            first.get("metrics", {}).get("decodeTokensPerSecond") if first else None,
            last.get("metrics", {}).get("decodeTokensPerSecond") if last else None,
        ),
        "ttftPercentChange": percent_change(
            first.get("metrics", {}).get("ttftMilliseconds") if first else None,
            last.get("metrics", {}).get("ttftMilliseconds") if last else None,
        ),
        "prefillPercentChange": percent_change(
            first.get("metrics", {}).get("prefillTokensPerSecond") if first else None,
            last.get("metrics", {}).get("prefillTokensPerSecond") if last else None,
        ),
    }
    bundle_summary = data.get("bundleSummary")
    if contract.workload_id == "b-pipe-001-sustained-generation":
        if not isinstance(bundle_summary, dict):
            errors.append("bundleSummary is required for B-PIPE-001")
        else:
            for field, expected in recalculated_degradation.items():
                if is_number(expected):
                    verify_optional_number(bundle_summary.get(field), expected, f"bundleSummary.{field}", errors)
                elif bundle_summary.get(field) != expected:
                    errors.append(f"bundleSummary.{field} does not match recalculated evidence")

    expected_session_valid = bool(
        preparation.get("eligibleForPerformanceMeasurement") is True
        and preparation.get("cacheStateBeforePreparation") == "cached"
        and preparation.get("downloadOccurredDuringSession") is False
        and preparation.get("preparationCompleted") is True
        and preparation.get("modelLoadCompleted") is True
        and device.get("debuggerAttached") is False
        and device.get("buildConfiguration") == "Release"
        and device.get("lowPowerModeEnabled") is False
        and device.get("batteryState") == "unplugged"
        and is_number(battery_level)
        and battery_level >= 50
    )
    if source_eligibility.get("sessionValid") is not expected_session_valid:
        errors.append("eligibility.sessionValid does not match environment and preparation evidence")
    if source_eligibility.get("officialLeaderboardEligible") is not False:
        errors.append("eligibility.officialLeaderboardEligible must be false")
    if not isinstance(source_eligibility.get("reasonCodes"), list):
        errors.append("eligibility.reasonCodes must be an array")

    if errors:
        return None, errors

    pilot_reasons: list[str] = []
    pilot_warnings: list[str] = []
    if not expected_session_valid:
        pilot_reasons.append("session_environment_ineligible")
    if not isinstance(device.get("appSourceCommit"), str) or not device["appSourceCommit"].strip():
        pilot_warnings.append("runner_source_identity_missing")
    if attempts[0].get("thermalStateBefore") != "nominal":
        pilot_reasons.append("initial_thermal_state_not_nominal")
    if not expected_performance:
        pilot_reasons.append("insufficient_successful_measured_runs")
    if any(attempt.get("outcome") == "notRun" for attempt in measured):
        pilot_reasons.append("planned_attempt_not_run")
    if any(attempt.get("stopReason") == "cancelled" for attempt in successful):
        pilot_reasons.append("cancelled_attempt_in_summary")
    prompt_counts = [attempt.get("promptTokenCount") for attempt in successful]
    if any(
        not isinstance(count, int)
        or not contract.prompt_token_minimum <= count <= contract.prompt_token_maximum
        for count in prompt_counts
    ):
        pilot_reasons.append("prompt_token_count_outside_pilot_band")
    if contract.output_token_warning_minimum is not None and any(
        not isinstance(attempt.get("outputTokenCount"), int)
        or attempt["outputTokenCount"] < contract.output_token_warning_minimum
        for attempt in successful
    ):
        pilot_warnings.append("output_below_256_tokens_not_an_eligibility_gate")
    primary_values = [
        attempt.get("metrics", {}).get(
            SUMMARY_METRICS[contract.primary_summary_field]
        )
        for attempt in successful
    ]
    if sum(is_number(value) for value in primary_values) < 3:
        pilot_reasons.append("insufficient_primary_metric_observations")
    if contract.user_visible_ttft and any(
        not isinstance(attempt.get("visibleText"), str) or not attempt["visibleText"].strip()
        for attempt in successful
    ):
        pilot_reasons.append("visible_output_missing")

    configuration = {
        "plan": plan,
        "measurementMode": measurement,
        "generationConfiguration": generation,
        "model": model,
        "runtime": runtime,
        "device": device,
    }
    comparison_identity = {
        "workload": workload,
        "plan": plan,
        "measurementMode": measurement,
        "generationConfiguration": generation,
        "device": {
            "machineIdentifier": device["machineIdentifier"],
            "systemVersion": device["systemVersion"],
            "systemBuild": device["systemBuild"],
        },
    }
    ship_identity = {
        "model": model,
        "runtime": runtime,
        "device": {
            "machineIdentifier": device["machineIdentifier"],
            "systemVersion": device["systemVersion"],
            "systemBuild": device["systemBuild"],
            "buildConfiguration": device["buildConfiguration"],
            "appVersion": device["appVersion"],
            "appBuild": device["appBuild"],
            "appSourceCommit": device.get("appSourceCommit"),
        },
    }
    outcomes = {name: sum(attempt.get("outcome") == name for attempt in measured) for name in ("completed", "failed", "notRun")}
    normalized = {
        "pipelineVersion": PIPELINE_VERSION,
        "source": {"path": source_name, "sha256": source_sha256},
        "resultID": result_id,
        "createdAt": data["createdAt"],
        "workload": workload,
        "configurationID": canonical_hash(configuration),
        "shipConfigurationID": canonical_hash(ship_identity),
        "comparisonGroupID": canonical_hash(comparison_identity),
        "configuration": configuration,
        "modelPreparation": preparation,
        "pilotEligibility": {
            "eligible": not pilot_reasons,
            "reasonCodes": sorted(set(pilot_reasons)),
            "warningCodes": sorted(set(pilot_warnings)),
            "scope": "internal-pilot-v0.1-only",
        },
        "metricInterpretation": {
            "primarySummaryField": contract.primary_summary_field,
            "label": contract.primary_label,
            "screenVisibleLatencyMeasured": False
            if contract.user_visible_ttft
            else None,
        },
        "summary": recalculated,
        "degradation": recalculated_degradation,
        "attemptEvidence": {
            "warmupRuns": 1,
            "measuredRuns": 5,
            "outcomes": outcomes,
            "allAttemptsRetained": True,
        },
        "limitations": [
            "non-official-pilot-evidence",
            "b-ux-001-adapter-first-renderable-proxy-not-screen-visible-ttft"
            if contract.user_visible_ttft
            else "five-runs-are-not-a-general-thermal-stability-claim",
            "b-ux-001-response-quality-not-evaluated"
            if contract.user_visible_ttft
            else "b-pipe-001-output-length-has-no-pilot-eligibility-minimum",
            "b-ux-001-adapter-proxy-not-independently-recalculable-from-token-events"
            if contract.user_visible_ttft
            else "reference-runtime-only",
        ],
    }
    return normalized, []


def process_files(paths: Iterable[Path]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    normalized: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen_result_ids: set[str] = set()
    for path in sorted(paths):
        try:
            raw = path.read_bytes()
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise ValueError("top-level JSON value must be an object")
            row, errors = validate_and_normalize(
                value,
                source_name=path.name,
                source_sha256=hashlib.sha256(raw).hexdigest(),
            )
        except (OSError, json.JSONDecodeError, ValueError) as error:
            row, errors = None, [str(error)]
        if row is not None and row["resultID"] in seen_result_ids:
            row, errors = None, ["duplicate resultID in Pilot input"]
        if row is None:
            rejected.append({"path": path.name, "errors": errors})
        else:
            seen_result_ids.add(row["resultID"])
            normalized.append(row)
    return normalized, rejected


def markdown_escape(value: Any) -> str:
    if value is None:
        return "Not recorded"
    return str(value).replace("|", "\\|").replace("\n", " ")


def short_revision(value: Any) -> str:
    text = str(value or "Not recorded")
    return text[:12] if len(text) > 12 else text


def format_measurement(value: Any, unit: str) -> str:
    return f"{float(value):.2f} {unit}" if is_number(value) else "Not recorded"


def attempt_status(row: dict[str, Any]) -> str:
    outcomes = row["attemptEvidence"]["outcomes"]
    state = "Complete" if outcomes["completed"] == 5 else "Partial"
    return (
        f"{state}: {outcomes['completed']} completed, {outcomes['failed']} failed, "
        f"{outcomes['notRun']} not run (plus 1 retained warm-up)"
    )


def configuration_label(row: dict[str, Any]) -> str:
    config = row["configuration"]
    model = config["model"]
    runtime = config["runtime"]
    device = config["device"]
    return (
        f"{model['artifactID']}@{short_revision(model['artifactRevision'])}; "
        f"{model['quantization']}; {runtime['name']}@{runtime['version']}; "
        f"{device['machineIdentifier']} / {device['systemVersion']} ({device['systemBuild']})"
    )


def render_leaderboard(rows: list[dict[str, Any]]) -> str:
    eligible = [row for row in rows if row["pilotEligibility"]["eligible"]]
    ineligible = [row for row in rows if not row["pilotEligibility"]["eligible"]]
    lines = [
        "# Suite B Internal Pilot v0.1 Leaderboard",
        "",
        "Non-official Pilot evidence only. Rows compare full App-recorded configurations, and rankings are separated by workload, device/OS, plan, measurement boundary, and generation configuration.",
        "",
        "B-UX-001's historical `medianUserVisibleTTFTMilliseconds` field is labeled First-renderable proxy TTFT; it is measured inside the adapter and is not screen-visible latency. The bundle also has no automated response-quality decision. B-PIPE-001's five measured runs are not a general thermal-stability claim.",
        "",
    ]
    if not eligible:
        lines.extend([
            "No eligible Pilot results are available. The input directory contains no valid, eligible, real App-generated result bundles.",
            "",
        ])
    else:
        for workload_id, contract in CONTRACTS.items():
            workload_rows = [row for row in eligible if row["workload"]["id"] == workload_id]
            if not workload_rows:
                continue
            lines.extend([f"## {contract.title}", ""])
            groups: dict[str, list[dict[str, Any]]] = {}
            for row in workload_rows:
                groups.setdefault(row["comparisonGroupID"], []).append(row)
            for group_id, group in sorted(groups.items()):
                sample = group[0]["configuration"]
                device = sample["device"]
                mode = sample["measurementMode"]
                lines.extend([
                    f"### Comparison group `{group_id[:12]}`",
                    "",
                    f"Device: {device['displayName']} (`{device['machineIdentifier']}`), {device['systemName']} {device['systemVersion']} ({device['systemBuild']}). Measurement: `{mode['id']}` / `{mode['timingBoundaryVersion']}`.",
                    "",
                    f"Ranking metric: {contract.primary_label}.",
                    "",
                    "| Rank | Full configuration | Primary | Other measured facts | Completion / failure evidence | Warnings | Result |",
                    "| ---: | --- | ---: | --- | --- | --- | --- |",
                ])
                ordered = sorted(
                    group,
                    key=lambda row: row["summary"][contract.primary_summary_field]
                    * (-1 if contract.primary_higher_is_better else 1),
                )
                for rank, row in enumerate(ordered, start=1):
                    summary = row["summary"]
                    config = row["configuration"]
                    full_config = (
                        configuration_label(row)
                        + f"; {config['model']['modelFormat']}; {config['runtime']['backend']}; "
                        + f"App {config['device']['appVersion']} build {config['device']['appBuild']} "
                        + f"({short_revision(config['device'].get('appSourceCommit'))}); "
                        + f"{config['plan']['id']}@{config['plan']['version']} / {config['measurementMode']['id']}"
                    )
                    facts = "; ".join((
                        "Pipeline TTFT " + format_measurement(summary.get("medianPipelineTTFTMilliseconds"), "ms"),
                        "prefill " + format_measurement(summary.get("medianPrefillTokensPerSecond"), "tok/s"),
                        "decode " + format_measurement(summary.get("medianDecodeTokensPerSecond"), "tok/s"),
                        "peak footprint " + format_measurement(summary.get("medianPeakMemoryMegabytes"), "MiB"),
                        "final thermal " + str(summary.get("finalThermalState")),
                    ))
                    warnings = ", ".join(row["pilotEligibility"]["warningCodes"]) or "None"
                    lines.append(
                        f"| {rank} | {markdown_escape(full_config)} | {summary[contract.primary_summary_field]:.2f} | {markdown_escape(facts)} | {markdown_escape(attempt_status(row))} | {markdown_escape(warnings)} | `{row['resultID']}` |"
                    )
                lines.append("")

    if ineligible:
        lines.extend([
            "## Non-ranked valid or partial Pilot evidence",
            "",
            "These App bundles passed the narrow structural and recalculation checks but did not satisfy Pilot comparison eligibility. They remain visible so failures and partial runs are not silently discarded.",
            "",
            "| Workload | Full configuration | Completion / failure evidence | Available summary | Ineligibility reasons | Warnings | Result |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ])
        for row in ineligible:
            summary = row["summary"]
            facts = "; ".join((
                "adapter proxy " + format_measurement(summary.get("medianUserVisibleTTFTMilliseconds"), "ms"),
                "Pipeline TTFT " + format_measurement(summary.get("medianPipelineTTFTMilliseconds"), "ms"),
                "decode " + format_measurement(summary.get("medianDecodeTokensPerSecond"), "tok/s"),
                "peak footprint " + format_measurement(summary.get("medianPeakMemoryMegabytes"), "MiB"),
            ))
            lines.append(
                "| {workload} | {config} | {attempts} | {facts} | {reasons} | {warnings} | `{result}` |".format(
                    workload=markdown_escape(row["workload"]["id"]),
                    config=markdown_escape(configuration_label(row)),
                    attempts=markdown_escape(attempt_status(row)),
                    facts=markdown_escape(facts),
                    reasons=markdown_escape(", ".join(row["pilotEligibility"]["reasonCodes"])),
                    warnings=markdown_escape(", ".join(row["pilotEligibility"]["warningCodes"]) or "None"),
                    result=row["resultID"],
                )
            )
        lines.append("")
    return "\n".join(lines)


def render_ship_evidence(rows: list[dict[str, Any]]) -> str:
    eligible = [row for row in rows if row["pilotEligibility"]["eligible"]]
    lines = [
        "# Suite B Internal Pilot v0.1 Ship Evidence",
        "",
        "This matrix reports only facts present in eligible App result bundles and fixed source-backed Pilot profiles. It is not a Ship score and does not infer App Store approval or distribution readiness.",
        "",
        "Status vocabulary: **Verified** means directly recorded and consistency-checked; **Supported** means demonstrated by the eligible Pilot run; **Unsupported** requires explicit negative evidence; **Unknown** means the bundle contains no evidence; **Warning** marks a narrow or non-generalizable claim.",
        "",
    ]
    if not eligible:
        lines.extend([
            "No eligible Pilot results are available. The input directory contains no valid, eligible, real App-generated result bundles.",
            "",
        ])
        return "\n".join(lines)

    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in eligible:
        grouped.setdefault(row["shipConfigurationID"], []).append(row)
    lines.extend([
        "| Configuration | Model source | Local inference / preparation | Artifact size | Offline execution | Streaming | Peak memory | Minimum tested device | License | Limitations |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ])
    for _, group in sorted(grouped.items()):
        row = group[0]
        config = row["configuration"]
        model = config["model"]
        runtime = config["runtime"]
        device = config["device"]
        preparation = row["modelPreparation"]
        workloads = sorted({item["workload"]["id"] for item in group})
        memory = [
            f"{item['workload']['id']}: {format_measurement(item['summary'].get('medianPeakMemoryMegabytes'), 'MiB')}"
            for item in group
        ]
        # Compatibility constraints describe the conditions under which the
        # profile may run. An eligible physical-device result demonstrates
        # those conditions; it must not relabel them as unresolved warnings.
        limitations = sorted(
            {limit for item in group for limit in item["limitations"]}
        )
        configuration = (
            f"Verified — {model['artifactID']}@{short_revision(model['artifactRevision'])} "
            f"({model['quantization']}; {model['modelFormat']}); {runtime['name']}@{runtime['version']} "
            f"({runtime['backend']}; {short_revision(runtime['resolvedRevision'])}); "
            f"{device['machineIdentifier']} / {device['systemVersion']} ({device['systemBuild']}); "
            f"App {device['appVersion']} build {device['appBuild']} ({short_revision(device.get('appSourceCommit'))})"
        )
        workload_evidence = "; ".join(
            f"{item['workload']['id']}: "
            f"{item['attemptEvidence']['outcomes']['completed']}/5 completed, "
            f"{item['attemptEvidence']['outcomes']['failed']} failed, "
            f"{item['attemptEvidence']['outcomes']['notRun']} not run"
            for item in group
        )
        preparation_fact = (
            f"Supported — local inference produced retained evidence; {workload_evidence}; "
            f"cache={preparation['cacheStateBeforePreparation']}; "
            f"verification={preparation['cacheVerificationMethod']}; downloaded during session="
            f"{str(preparation['downloadOccurredDuringSession']).lower()}; load completed="
            f"{str(preparation['modelLoadCompleted']).lower()}"
        )
        memory_fact = (
            "Verified — " + "; ".join(memory)
            if any(is_number(item["summary"].get("medianPeakMemoryMegabytes")) for item in group)
            else "Unknown — no peak-memory observation in bundle"
        )
        source_fact = (
            f"Verified — {model['sourceURL']}"
            if isinstance(model.get("sourceURL"), str)
            else "Unknown — not recorded in result bundle"
        )
        artifact_size = model.get("artifactRepositorySizeBytes")
        size_fact = (
            f"Verified — {artifact_size:,} bytes from pinned Hugging Face repository metadata"
            if isinstance(artifact_size, int)
            else "Unknown — not recorded in result bundle"
        )
        license_fact = (
            f"Verified — {model['licenseIdentifier']} metadata; source {model['licenseSourceURL']}; no legal conclusion"
            if isinstance(model.get("licenseIdentifier"), str)
            and isinstance(model.get("licenseSourceURL"), str)
            else "Unknown — not recorded in result bundle"
        )
        lines.append(
            f"| {markdown_escape(configuration)} | {markdown_escape(source_fact)} | {markdown_escape(preparation_fact)} | {markdown_escape(size_fact)} | Unknown — measured-phase network state is not recorded | Supported — per-token adapter events were retained for completed attempts | {markdown_escape(memory_fact)} | Verified — tested on {markdown_escape(device['displayName'])} (`{markdown_escape(device['machineIdentifier'])}`); minimum supported device is not established | {markdown_escape(license_fact)} | Warning — {markdown_escape(', '.join(limitations))} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_outputs(input_directory: Path, output_directory: Path) -> tuple[int, int, int]:
    paths = sorted(input_directory.glob("*.json")) if input_directory.is_dir() else []
    rows, rejected = process_files(paths)
    eligible = [row for row in rows if row["pilotEligibility"]["eligible"]]
    ineligible = [row for row in rows if not row["pilotEligibility"]["eligible"]]
    output_directory.mkdir(parents=True, exist_ok=True)
    normalized_document = {
        "pipelineVersion": PIPELINE_VERSION,
        "normalizedResultCount": len(rows),
        "eligibleResultCount": len(eligible),
        "ineligibleResultCount": len(ineligible),
        "results": rows,
    }
    report = {
        "pipelineVersion": PIPELINE_VERSION,
        "inputFileCount": len(paths),
        "normalizedResultCount": len(rows),
        "eligibleResultCount": len(eligible),
        "ineligibleResultCount": len(ineligible),
        "rejectedResultCount": len(rejected),
        "ineligible": [
            {
                "resultID": row["resultID"],
                "source": row["source"]["path"],
                "reasonCodes": row["pilotEligibility"]["reasonCodes"],
            }
            for row in ineligible
        ],
        "rejected": rejected,
    }
    (output_directory / "normalized-results.json").write_text(
        json.dumps(normalized_document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_directory / "pipeline-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_directory / "LEADERBOARD.md").write_text(
        render_leaderboard(rows), encoding="utf-8"
    )
    (output_directory / "SHIP-EVIDENCE.md").write_text(
        render_ship_evidence(rows), encoding="utf-8"
    )
    return len(rows), len(eligible), len(rejected)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    normalized, eligible, rejected = write_outputs(args.input, args.output)
    print(
        f"Pilot v0.1: {normalized} normalized, {eligible} eligible, {rejected} rejected"
    )
    return 1 if rejected else 0


if __name__ == "__main__":
    raise SystemExit(main())
