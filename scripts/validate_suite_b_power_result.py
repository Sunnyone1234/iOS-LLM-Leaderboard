#!/usr/bin/env python3
"""Validate and recalculate Suite B Power 1.0 release-candidate evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
RELEASE_PATH = (
    ROOT
    / "benchmarks/suite-b-on-device-performance/releases/suite-b-power-1.0.0-rc.1.json"
)
RESULT_SCHEMA_PATH = ROOT / "schemas/suite-b-power-result-1.0.0-rc.1.schema.json"
REPORT_SCHEMA_PATH = (
    ROOT / "schemas/suite-b-power-validation-report-1.0.0-rc.1.schema.json"
)
VALIDATOR_ID = "suite-b-power-validator"
VALIDATOR_VERSION = "1.0.0-rc.1"
RESULT_SCHEMA_VERSION = "suite-b-power-result-1.0.0-rc.1"
REPORT_SCHEMA_VERSION = "suite-b-power-validation-report-1.0.0-rc.1"

WORKLOADS = {
    "b-ux-001-short-interaction": {
        "version": "1.0.0-rc.1",
        "category": "user-experience",
        "fixture": "69b3cd45fb67e1882dabdc082636298123e01081c097af65b3fd133b19ccbc84",
        "mode": "b-mode-warm-resident-ux-v1",
        "output_limit": 128,
        "metrics": [
            "first_renderable_proxy_ttft_ms@1",
            "pipeline_ttft_ms@1",
            "request_completion_ms@1",
            "prefill_tokens_per_second@1",
            "decode_tokens_per_second@1",
            "process_physical_footprint_mib@1",
        ],
    },
    "b-pipe-001-sustained-generation": {
        "version": "1.0.0-rc.1",
        "category": "pipeline",
        "fixture": "b865ad1a1993bfd7bf097b85f7c5585e44f1384fa291b9c05426c6051caba996",
        "mode": "b-mode-sustained-no-rest-v1",
        "output_limit": 512,
        "metrics": [
            "pipeline_ttft_ms@1",
            "prefill_tokens_per_second@1",
            "decode_tokens_per_second@1",
            "process_physical_footprint_mib@1",
            "decode_first_to_last_percent_change@1",
        ],
    },
}

ATTEMPT_METRICS = {
    "pipeline_ttft_ms@1": "pipelineTTFTMilliseconds",
    "first_renderable_proxy_ttft_ms@1": "firstRenderableProxyTTFTMilliseconds",
    "request_completion_ms@1": "requestCompletionMilliseconds",
    "prefill_tokens_per_second@1": "prefillTokensPerSecond",
    "decode_tokens_per_second@1": "decodeTokensPerSecond",
    "process_physical_footprint_mib@1": "processPhysicalFootprintMiB",
}

SUMMARY_METRICS = {
    "pipeline_ttft_ms@1": "medianPipelineTTFTMilliseconds",
    "first_renderable_proxy_ttft_ms@1": "medianFirstRenderableProxyTTFTMilliseconds",
    "request_completion_ms@1": "medianRequestCompletionMilliseconds",
    "prefill_tokens_per_second@1": "medianPrefillTokensPerSecond",
    "decode_tokens_per_second@1": "medianDecodeTokensPerSecond",
    "process_physical_footprint_mib@1": "medianProcessPhysicalFootprintMiB",
    "decode_first_to_last_percent_change@1": "decodeFirstToLastPercentChange",
}

OUTCOMES = {"completed", "failed", "cancelled", "outOfMemory", "notRun"}
STOPS = {"endOfSequence", "outputTokenLimit"}
THERMAL = {"nominal", "fair", "serious", "critical", "unknown"}
ATTEMPT_REASON_CODES = {
    "failed": {
        "runtime_error", "adapter_error", "model_input_error",
        "evidence_capture_error", "process_terminated_unclassified",
    },
    "cancelled": {"user_cancelled", "system_cancelled"},
    "outOfMemory": {"runtime_out_of_memory", "os_memory_termination"},
    "notRun": {
        "thermal_state_critical_before_attempt", "prior_attempt_unrecoverable",
        "session_cancelled", "environment_admission_failed",
    },
}
def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_release_assets() -> list[str]:
    if not RELEASE_PATH.exists():
        return [f"missing release manifest: {RELEASE_PATH.relative_to(ROOT)}"]
    manifest = json.loads(RELEASE_PATH.read_text())
    errors: list[str] = []
    for asset in manifest.get("pinnedAssets", []):
        path = ROOT / asset.get("path", "")
        if not path.is_file():
            errors.append(f"missing pinned asset: {asset.get('path')}")
        elif _sha256(path) != asset.get("sha256"):
            errors.append(f"pinned asset digest mismatch: {asset.get('path')}")
    return errors


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _close(actual: Any, expected: float | None) -> bool:
    if expected is None:
        return actual is None
    if not _finite_number(actual):
        return False
    return math.isclose(float(actual), expected, rel_tol=1e-6, abs_tol=1e-9)


def _median(values: list[float]) -> float | None:
    return statistics.median(values) if len(values) >= 3 else None


def _version_at_least(actual: Any, minimum: str) -> bool:
    if not isinstance(actual, str):
        return False
    try:
        actual_parts = tuple(int(part) for part in actual.split("."))
        minimum_parts = tuple(int(part) for part in minimum.split("."))
    except ValueError:
        return False
    width = max(len(actual_parts), len(minimum_parts))
    return actual_parts + (0,) * (width - len(actual_parts)) >= minimum_parts + (0,) * (width - len(minimum_parts))


def _is_renderable(text: str) -> bool:
    def whitespace(value: int) -> bool:
        return (
            0x0009 <= value <= 0x000D
            or value in {0x0020, 0x0085, 0x00A0, 0x1680, 0x202F, 0x205F, 0x3000}
            or 0x2000 <= value <= 0x200A
            or 0x2028 <= value <= 0x2029
        )

    return any(not whitespace(ord(character)) for character in text)


def _response_conformant(text: Any) -> bool:
    if not isinstance(text, str):
        return False
    normalized = " ".join(unicodedata.normalize("NFKC", text).casefold().split())
    if not normalized:
        return False
    sentence_count = len([part for part in re.split(r"[.!?]+", normalized) if part.strip()])
    local_safety = "safe" in normalized and any(
        term in normalized for term in ("iphone", "device", "local")
    )
    sync_return = (
        "sync" in normalized
        and any(term in normalized for term in ("connect", "network", "online"))
        and any(term in normalized for term in ("return", "restore", "available", "back", "again"))
    )
    return sentence_count <= 2 and local_safety and sync_return


def _json_equal(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    return left == right


def _matches_type(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": _finite_number(value),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(expected, False)


def _resolve_ref(root: dict[str, Any], reference: str) -> dict[str, Any]:
    if not reference.startswith("#/"):
        raise ValueError(f"unsupported schema reference: {reference}")
    node: Any = root
    for part in reference[2:].split("/"):
        node = node[part.replace("~1", "/").replace("~0", "~")]
    return node


def _validate_schema(
    value: Any,
    schema: dict[str, Any],
    root: dict[str, Any],
    path: str = "$",
) -> list[str]:
    if "$ref" in schema:
        return _validate_schema(value, _resolve_ref(root, schema["$ref"]), root, path)
    errors: list[str] = []
    if "const" in schema and not _json_equal(value, schema["const"]):
        errors.append(f"{path} must equal the frozen constant")
    if "enum" in schema and not any(
        _json_equal(value, option) for option in schema["enum"]
    ):
        errors.append(f"{path} is outside the frozen enum")
    expected_type = schema.get("type")
    if expected_type is not None:
        choices = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(_matches_type(value, choice) for choice in choices):
            errors.append(f"{path} has the wrong JSON type")
            return errors
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for required in schema.get("required", []):
            if required not in value:
                errors.append(f"{path}.{required} is required")
        additional = schema.get("additionalProperties", True)
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in properties:
                errors.extend(_validate_schema(child, properties[key], root, child_path))
            elif additional is False:
                errors.append(f"{child_path} is not allowed")
            elif isinstance(additional, dict):
                errors.extend(_validate_schema(child, additional, root, child_path))
        if len(value) < schema.get("minProperties", 0):
            errors.append(f"{path} has too few properties")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{path} has too few items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path} has too many items")
        if schema.get("uniqueItems") and len(
            {json.dumps(item, sort_keys=True) for item in value}
        ) != len(value):
            errors.append(f"{path} must contain unique items")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, child in enumerate(value):
                errors.extend(
                    _validate_schema(child, item_schema, root, f"{path}[{index}]")
                )
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path} is too short")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            errors.append(f"{path} does not match the required pattern")
        if schema.get("format") == "date-time":
            try:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"{path} is not a date-time")
        if schema.get("format") == "uri" and not urlparse(value).scheme:
            errors.append(f"{path} is not a URI")
    if _finite_number(value):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path} is below the minimum")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path} is above the maximum")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            errors.append(f"{path} must be greater than the exclusive minimum")
    for child_schema in schema.get("allOf", []):
        errors.extend(_validate_schema(value, child_schema, root, path))
    condition = schema.get("if")
    if isinstance(condition, dict) and not _validate_schema(value, condition, root, path):
        then = schema.get("then")
        if isinstance(then, dict):
            errors.extend(_validate_schema(value, then, root, path))
    return errors


def _shape_errors(data: Any) -> list[str]:
    try:
        schema = json.loads(RESULT_SCHEMA_PATH.read_text())
    except (OSError, json.JSONDecodeError) as error:
        return [f"frozen result schema is unavailable: {error}"]
    return _validate_schema(data, schema, schema)


def validate_report_shape(report: Any) -> list[str]:
    try:
        schema = json.loads(REPORT_SCHEMA_PATH.read_text())
    except (OSError, json.JSONDecodeError) as error:
        return [f"frozen validation-report schema is unavailable: {error}"]
    return _validate_schema(report, schema, schema)


def _trace_value(attempt: dict[str, Any], errors: list[str], label: str) -> float | None:
    trace = attempt.get("renderabilityTrace")
    if not isinstance(trace, dict):
        return None
    expected_identity = (
        trace.get("policyVersion") == "first-renderable-decoded-prefix-v1"
        and trace.get("clockOrigin") == "adapter-request-accepted"
        and trace.get("scope") == "through-first-renderable-inclusive"
        and trace.get("captureLimit") == 32
    )
    entries = trace.get("entries")
    tokens = attempt.get("tokenEvents", [])
    generation_start = trace.get("generationStartNanoseconds")
    if generation_start != attempt.get("timingEvidence", {}).get("generationStartNanoseconds"):
        errors.append(f"{label}: trace generation origin mismatch")
        return None
    if not expected_identity or not isinstance(entries, list) or len(entries) > 32:
        errors.append(f"{label}: invalid first-renderable trace identity")
        return None
    found: tuple[int, int] | None = None
    for position, entry in enumerate(entries):
        if not isinstance(entry, dict) or position >= len(tokens):
            errors.append(f"{label}: trace entry has no matching token")
            return None
        token = tokens[position]
        if entry.get("tokenIndex") != position or entry.get("tokenID") != token.get("tokenID"):
            errors.append(f"{label}: trace/token identity mismatch")
            return None
        received = entry.get("tokenReceivedNanoseconds")
        decoded = entry.get("decodedAtNanoseconds")
        expected_received = generation_start + token.get("elapsedNanoseconds", -1) if isinstance(generation_start, int) else None
        if received != expected_received or not isinstance(decoded, int) or decoded < received:
            errors.append(f"{label}: trace clock relation is invalid")
            return None
        renderable = _is_renderable(entry.get("decodedPrefix", ""))
        if entry.get("isRenderable") is not renderable:
            errors.append(f"{label}: trace renderability decision is invalid")
            return None
        if renderable and found is None:
            found = (position, decoded)
            if position != len(entries) - 1:
                errors.append(f"{label}: trace continues after first renderable prefix")
                return None
    outcome = trace.get("outcome")
    index = trace.get("firstRenderableTokenIndex")
    if found:
        if outcome != "firstRenderableFound" or index != found[0]:
            errors.append(f"{label}: first-renderable outcome is contradictory")
            return None
        return found[1] / 1_000_000
    if outcome not in {"noRenderableContent", "captureLimitReached"} or index is not None:
        errors.append(f"{label}: non-renderable trace outcome is contradictory")
    return None


def _attempt_values(attempt: dict[str, Any], workload_id: str, errors: list[str], label: str) -> dict[str, float | None]:
    values = {metric: None for metric in ATTEMPT_METRICS}
    if attempt.get("outcome") != "completed":
        outcome = attempt.get("outcome")
        reasons = attempt.get("reasonCodes", [])
        if (
            attempt.get("stopReason") is not None
            or not reasons
            or any(reason not in ATTEMPT_REASON_CODES.get(outcome, set()) for reason in reasons)
        ):
            errors.append(f"{label}: non-completed outcome must have reasons and null stopReason")
        if any(value is not None for value in attempt.get("derivedMetrics", {}).values()):
            errors.append(f"{label}: non-completed attempt metrics must be null")
        if attempt.get("outcome") == "notRun" and any((attempt.get("tokenEvents"), attempt.get("memorySamples"))):
            errors.append(f"{label}: notRun attempt cannot contain measurement events")
        return values

    if attempt.get("stopReason") not in STOPS or attempt.get("reasonCodes"):
        errors.append(f"{label}: completed outcome has contradictory stop/reason evidence")
    tokens = attempt.get("tokenEvents", [])
    output_count = attempt.get("outputTokenCount")
    prompt_count = attempt.get("promptTokenCount")
    output_limit = WORKLOADS[workload_id]["output_limit"]
    if not isinstance(output_count, int) or output_count < 0 or output_count > output_limit:
        errors.append(f"{label}: output token count is outside the workload limit")
    if attempt.get("stopReason") == "outputTokenLimit" and output_count != output_limit:
        errors.append(f"{label}: outputTokenLimit stop requires the exact workload limit")
    if workload_id == "b-ux-001-short-interaction" and not (
        isinstance(prompt_count, int) and 64 <= prompt_count <= 256
    ):
        errors.append(f"{label}: Short Interaction prompt token count is outside 64...256")
    valid_tokens = isinstance(output_count, int) and output_count == len(tokens)
    previous = -1
    for position, token in enumerate(tokens):
        elapsed = token.get("elapsedNanoseconds") if isinstance(token, dict) else None
        if not isinstance(token, dict) or token.get("index") != position or not isinstance(token.get("tokenID"), int) or not isinstance(elapsed, int) or elapsed < previous:
            valid_tokens = False
            break
        previous = elapsed
    if not valid_tokens:
        errors.append(f"{label}: token evidence is invalid")
    response = attempt.get("responseConformance", {})
    if workload_id == "b-ux-001-short-interaction":
        computed_response = _response_conformant(attempt.get("generatedText"))
        expected_status = "pass" if computed_response else "fail"
        expected_reasons = [] if computed_response else ["response_conformance_failed"]
        if response.get("status") != expected_status or response.get("reasonCodes") != expected_reasons:
            errors.append(f"{label}: response conformance decision mismatch")
        response_ok = computed_response
    else:
        response_ok = True
        if response != {"status": "notApplicable", "reasonCodes": []}:
            errors.append(f"{label}: pipeline response conformance must be notApplicable")
    if workload_id == "b-ux-001-short-interaction" and not response_ok:
        return values
    if valid_tokens and tokens:
        values["pipeline_ttft_ms@1"] = tokens[0]["elapsedNanoseconds"] / 1_000_000
    timing = attempt.get("timingEvidence", {})
    prompt_ns = timing.get("promptEvaluationNanoseconds")
    if isinstance(prompt_count, int) and prompt_count > 0 and isinstance(prompt_ns, int) and prompt_ns > 0:
        values["prefill_tokens_per_second@1"] = prompt_count * 1_000_000_000 / prompt_ns
    if valid_tokens and len(tokens) >= 2:
        interval = tokens[-1]["elapsedNanoseconds"] - tokens[0]["elapsedNanoseconds"]
        if interval > 0:
            values["decode_tokens_per_second@1"] = (len(tokens) - 1) * 1_000_000_000 / interval
    samples = attempt.get("memorySamples", [])
    valid_samples = bool(samples)
    previous = -1
    footprints: list[int] = []
    for sample in samples:
        elapsed = sample.get("elapsedNanoseconds") if isinstance(sample, dict) else None
        footprint = sample.get("physicalFootprintBytes") if isinstance(sample, dict) else None
        if not isinstance(elapsed, int) or elapsed < previous or not isinstance(footprint, int) or footprint <= 0:
            valid_samples = False
            break
        previous = elapsed
        footprints.append(footprint)
    if valid_samples:
        values["process_physical_footprint_mib@1"] = max(footprints) / 1_048_576
    if workload_id == "b-ux-001-short-interaction":
        values["first_renderable_proxy_ttft_ms@1"] = _trace_value(attempt, errors, label)
        completion = timing.get("requestCompletionNanoseconds")
        if isinstance(completion, int) and completion > 0:
            last_token_request_time = timing.get("generationStartNanoseconds", 0) + (tokens[-1]["elapsedNanoseconds"] if tokens else 0)
            if completion < last_token_request_time:
                errors.append(f"{label}: request completion precedes the final token")
                return values
            values["request_completion_ms@1"] = completion / 1_000_000
    return values


def _decision(valid: bool, reasons: list[str]) -> dict[str, Any]:
    return {"valid": valid, "reasonCodes": list(dict.fromkeys(reasons))}


def _empty_report(data: Any, structural_errors: list[str]) -> dict[str, Any]:
    return {
        "schemaVersion": REPORT_SCHEMA_VERSION,
        "resultID": data.get("resultID") if isinstance(data, dict) and isinstance(data.get("resultID"), str) else None,
        "benchmarkRelease": {"id": "suite-b-power", "version": "1.0.0-rc.1"},
        "validator": {"id": VALIDATOR_ID, "version": VALIDATOR_VERSION},
        "overallStatus": "invalid",
        "structuralValidity": _decision(False, ["schema_invalid"]),
        "protocolConformance": _decision(False, ["schema_invalid"]),
        "metricEligibility": {},
        "evidenceLevel": {"level": "unreviewed", "reasonCodes": ["evidence_not_reviewed"]},
        "rankingEligibility": {"eligible": False, "reasonCodes": ["release_candidate_not_official", "ranking_not_authorized"]},
        "errors": structural_errors,
        "warnings": [],
    }


def _asset_failure_report(data: dict[str, Any], asset_errors: list[str]) -> dict[str, Any]:
    report = _empty_report(data, asset_errors)
    report["structuralValidity"] = _decision(True, [])
    report["protocolConformance"] = _decision(
        False, ["release_identity_mismatch"]
    )
    return report


def validate(data: Any) -> dict[str, Any]:
    structural_errors = _shape_errors(data)
    if structural_errors:
        return _empty_report(data, structural_errors)
    asset_errors = verify_release_assets()
    if asset_errors:
        return _asset_failure_report(data, asset_errors)

    errors: list[str] = []
    warnings: list[str] = []
    conformance_reasons: list[str] = []
    execution = data["execution"]
    workload_id = execution.get("workloadID")
    workload = WORKLOADS.get(workload_id)
    if workload is None:
        errors.append("unsupported workload identity")
        conformance_reasons.append("workload_identity_mismatch")
        return _empty_report(data, errors)
    expected_execution = {
        "workloadVersion": workload["version"],
        "workloadCategory": workload["category"],
        "fixtureSHA256": workload["fixture"],
        "measurementModeID": workload["mode"],
    }
    for field, expected in expected_execution.items():
        if execution.get(field) != expected:
            errors.append(f"execution.{field} does not match the release")
            conformance_reasons.append("workload_identity_mismatch" if field != "fixtureSHA256" else "fixture_hash_mismatch")
    if not _version_at_least(execution.get("runnerVersion"), "0.8.0"):
        errors.append("execution.runnerVersion is older than the release minimum")
        conformance_reasons.append("runner_incompatible")
    config = data["configuration"]
    expected_config = {
        "warmupAttempts": 1,
        "measuredAttempts": 5,
        "minimumMetricEligibleMeasuredAttempts": 3,
        "restIntervalSeconds": 0,
        "samplingEnabled": False,
        "temperature": 0,
        "includeStopTokenInRawEvents": False,
        "outputTokenLimit": workload["output_limit"],
        "modelLoadPolicy": "load-once-before-warmup",
        "contextPolicy": "fresh-conversation-per-attempt",
        "kvCachePolicy": "fresh-kv-cache-per-attempt",
        "automaticRetries": 0,
        "clock": "monotonic-nanoseconds",
        "memorySamplingIntervalMilliseconds": 50,
        "memoryMetric": "TASK_VM_INFO.phys_footprint",
        "thermalSource": "ProcessInfo.thermalState",
    }
    expected_config.update(
        {
            "topP": 1,
            "topK": 0,
            "seed": 0,
            "repetitionPenalty": None,
            "thinkingMode": "disabled-via-chat-template",
            "chatTemplateIdentity": "artifact-tokenizer-config-enable-thinking-false",
        }
        if workload_id == "b-ux-001-short-interaction"
        else {
            "topP": None,
            "topK": None,
            "seed": None,
            "repetitionPenalty": None,
            "thinkingMode": "disabled-via-prompt-directive",
            "chatTemplateIdentity": "artifact-tokenizer-config",
        }
    )
    for field, expected in expected_config.items():
        if config.get(field) != expected:
            errors.append(f"configuration.{field} does not match the protocol")
            conformance_reasons.append("release_identity_mismatch")
    environment = data["environment"]
    if not (
        environment.get("buildConfiguration") == "Release"
        and environment.get("debuggerAttached") is False
        and environment.get("lowPowerModeEnabled") is False
        and environment.get("batteryState") == "unplugged"
        and _finite_number(environment.get("batteryLevelPercentAtStart"))
        and environment["batteryLevelPercentAtStart"] >= 50
        and environment.get("thermalStateAtSessionStart") == "nominal"
    ):
        errors.append("environment admission requirements failed")
        conformance_reasons.append("environment_ineligible")
    preparation = data["modelPreparation"]
    if not (
        preparation.get("artifactID") == data["model"].get("artifactID")
        and preparation.get("artifactRevision") == data["model"].get("artifactRevision")
        and preparation.get("downloadOccurredDuringSession") is False
        and preparation.get("preparationCompleted") is True
        and preparation.get("modelLoadCompleted") is True
        and preparation.get("eligibleForPerformanceMeasurement") is True
    ):
        errors.append("model preparation does not satisfy the protocol")
        conformance_reasons.append("model_preparation_ineligible")

    attempt_values: list[dict[str, float | None]] = []
    attempts = data["attempts"]
    stopped_for_critical = False
    for position, attempt in enumerate(attempts):
        expected_role = "warmup" if position == 0 else "measured"
        if attempt.get("runIndex") != position or attempt.get("role") != expected_role:
            errors.append(f"attempts[{position}] has invalid index/role sequence")
            conformance_reasons.append("attempt_sequence_invalid")
        thermal = attempt.get("thermal", {})
        if thermal.get("before") not in THERMAL or thermal.get("after") not in THERMAL:
            errors.append(f"attempts[{position}] has invalid thermal evidence")
            conformance_reasons.append("thermal_evidence_unavailable")
        if thermal.get("before") == "critical" and attempt.get("outcome") != "notRun":
            errors.append(f"attempts[{position}] must be notRun after critical thermal state")
            conformance_reasons.append("contradictory_outcome_evidence")
        if thermal.get("before") == "critical":
            stopped_for_critical = True
            if "thermal_state_critical_before_attempt" not in attempt.get("reasonCodes", []):
                errors.append(f"attempts[{position}] is missing the critical-thermal notRun reason")
                conformance_reasons.append("contradictory_outcome_evidence")
        if stopped_for_critical and attempt.get("outcome") != "notRun":
            errors.append(f"attempts[{position}] started after the critical-thermal stop")
            conformance_reasons.append("contradictory_outcome_evidence")
        if stopped_for_critical and "thermal_state_critical_before_attempt" not in attempt.get("reasonCodes", []):
            errors.append(f"attempts[{position}] is missing the cascading critical-thermal reason")
            conformance_reasons.append("contradictory_outcome_evidence")
        values = _attempt_values(attempt, workload_id, errors, f"attempts[{position}]")
        attempt_values.append(values)
        for metric, field in ATTEMPT_METRICS.items():
            if not _close(attempt["derivedMetrics"].get(field), values[metric]):
                errors.append(f"attempts[{position}].derivedMetrics.{field} mismatch")
                conformance_reasons.append("aggregate_mismatch")

    measured_pairs = list(zip(attempts[1:], attempt_values[1:]))
    metric_decisions: dict[str, dict[str, Any]] = {}
    global_metric_reasons = list(
        dict.fromkeys(
            reason
            for reason in conformance_reasons
            if reason
            in {
                "release_identity_mismatch",
                "workload_identity_mismatch",
                "fixture_hash_mismatch",
                "runner_incompatible",
                "environment_ineligible",
                "model_preparation_ineligible",
            }
        )
    )
    for metric, field in SUMMARY_METRICS.items():
        if metric in workload["metrics"] and global_metric_reasons:
            expected = None
            count = 0
            reasons = global_metric_reasons
        elif metric == "decode_first_to_last_percent_change@1":
            if workload_id != "b-pipe-001-sustained-generation":
                expected = None
                count = 0
                reasons = ["metric_not_applicable"]
            else:
                first = attempt_values[1]["decode_tokens_per_second@1"]
                last = attempt_values[5]["decode_tokens_per_second@1"]
                expected = ((last / first) - 1) * 100 if first and last else None
                count = 2 if expected is not None else 0
                reasons = [] if expected is not None else ["insufficient_metric_eligible_attempts"]
        elif metric not in workload["metrics"]:
            expected = None
            count = 0
            reasons = ["metric_not_applicable"]
        else:
            values = [values[metric] for attempt, values in measured_pairs if attempt.get("outcome") == "completed" and values[metric] is not None]
            count = len(values)
            expected = _median(values)
            reasons = [] if expected is not None else ["insufficient_metric_eligible_attempts"]
        if metric in workload["metrics"]:
            metric_decisions[metric] = {
                "eligible": expected is not None,
                "eligibleMeasuredAttempts": count,
                "reasonCodes": reasons,
            }
        if not _close(data["summary"]["metrics"].get(field), expected):
            errors.append(f"summary.metrics.{field} mismatch")
            conformance_reasons.append("aggregate_mismatch")

    measured = attempts[1:]
    expected_counts = {outcome: sum(a.get("outcome") == outcome for a in measured) for outcome in OUTCOMES}
    expected_counts["earlyEOS"] = sum(a.get("outcome") == "completed" and a.get("stopReason") == "endOfSequence" for a in measured)
    if data["summary"].get("terminalCounts") != expected_counts:
        errors.append("summary.terminalCounts mismatch")
        conformance_reasons.append("aggregate_mismatch")
    if errors and not conformance_reasons:
        conformance_reasons.append("contradictory_outcome_evidence")
    for decision in metric_decisions.values():
        if not decision["eligible"]:
            warnings.append("one or more ranked metrics are ineligible")
            break
    warnings.extend([
        "evidence has not received independent review",
        "release candidate does not authorize leaderboard ranking",
    ])
    protocol_valid = not errors
    return {
        "schemaVersion": REPORT_SCHEMA_VERSION,
        "resultID": data["resultID"],
        "benchmarkRelease": {"id": "suite-b-power", "version": "1.0.0-rc.1"},
        "validator": {"id": VALIDATOR_ID, "version": VALIDATOR_VERSION},
        "overallStatus": "validWithWarnings" if protocol_valid else "invalid",
        "structuralValidity": _decision(True, []),
        "protocolConformance": _decision(protocol_valid, conformance_reasons),
        "metricEligibility": metric_decisions,
        "evidenceLevel": {"level": "unreviewed", "reasonCodes": ["evidence_not_reviewed"]},
        "rankingEligibility": {"eligible": False, "reasonCodes": ["release_candidate_not_official", "ranking_not_authorized"]},
        "errors": errors,
        "warnings": list(dict.fromkeys(warnings)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.result.read_text())
    except (OSError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    report = validate(data)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")
    return 0 if report["overallStatus"] != "invalid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
