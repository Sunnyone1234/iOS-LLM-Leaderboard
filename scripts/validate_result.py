#!/usr/bin/env python3
"""Validate Benchmark Framework v1 result JSON files."""

from __future__ import annotations

import json
import math
import sys
from datetime import date
from pathlib import Path
from typing import Any


MISSING = object()

REQUIRED_PATHS = [
    "schema_version",
    "result_id",
    "task.task_id",
    "task.task_version",
    "task.suite",
    "model.model_name",
    "model.provider",
    "execution.date",
    "execution.evaluator",
    "evaluation.score",
    "evaluation.max_score",
    "evaluation.passed",
    "license_confirmation.contributor_agrees_to_repo_license",
]

SUITE_B_REQUIRED_PATHS = [
    "model.quantization",
    "runtime.runtime_name",
    "runtime.runtime_version",
    "runtime.backend",
    "runtime.model_format",
    "device.device_name",
    "device.os_name",
    "device.os_version",
    "suite_b_measurement.prompt_token_band",
    "suite_b_measurement.output_token_band",
    "suite_b_measurement.warmup_procedure",
    "suite_b_measurement.measurement_procedure",
    "suite_b_measurement.measured_run_count",
    "suite_b_measurement.aggregation_method",
    "suite_b_measurement.cold_or_warm_start_state",
    "suite_b_measurement.timing_boundaries",
    "suite_b_measurement.failed_or_interrupted_run_handling",
]

SUITE_B_PRIMARY_METRICS = [
    "ttft_ms",
    "prefill_tokens_per_second",
    "decode_tokens_per_second",
    "peak_memory_mb",
    "thermal_state",
]

ALLOWED_ACCESS_TYPES = {"api", "local", "xcode", "hosted", "unknown"}
ALLOWED_RUN_TYPES = {"manual", "scripted", "app-export", "ci", "unknown"}
ALLOWED_PROVENANCE_SOURCES = {
    "manual-submission",
    "benchmark-app",
    "maintainer-run",
    "ci",
    "imported",
    "demo-placeholder",
}
ALLOWED_THERMAL_STATES = {"nominal", "fair", "serious", "critical", "unknown"}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError("top-level JSON value must be an object")
    return data


def nested_value(data: dict[str, Any], path: str) -> Any:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return MISSING
        current = current[part]
    return current


def is_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def is_placeholder(data: dict[str, Any]) -> bool:
    return nested_value(data, "provenance.source") == "demo-placeholder"


def require_paths(
    data: dict[str, Any],
    paths: list[str],
    *,
    allow_null: bool,
) -> list[str]:
    errors: list[str] = []
    for path in paths:
        value = nested_value(data, path)
        if value is MISSING:
            errors.append(f"missing required field: {path}")
        elif value == "":
            errors.append(f"required field is empty: {path}")
        elif value is None and not allow_null:
            errors.append(f"required field is null: {path}")
    return errors


def validate_score(data: dict[str, Any], placeholder: bool) -> list[str]:
    errors: list[str] = []
    score = nested_value(data, "evaluation.score")
    max_score = nested_value(data, "evaluation.max_score")
    passed = nested_value(data, "evaluation.passed")

    if max_score is not MISSING and not is_number(max_score):
        errors.append("evaluation.max_score must be a finite number")
    elif is_number(max_score) and max_score <= 0:
        errors.append("evaluation.max_score must be greater than zero")

    if score is None and not placeholder:
        errors.append("evaluation.score may be null only for demo placeholders")
    elif score is not MISSING and score is not None and not is_number(score):
        errors.append("evaluation.score must be a finite number or null")
    elif is_number(score) and is_number(max_score) and not 0 <= score <= max_score:
        errors.append("evaluation.score must be between zero and evaluation.max_score")

    if passed is None and not placeholder:
        errors.append("evaluation.passed may be null only for demo placeholders")
    elif passed is not MISSING and passed is not None and not isinstance(passed, bool):
        errors.append("evaluation.passed must be true, false, or null")

    return errors


def validate_metrics(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    metrics = data.get("metrics")
    if metrics is None:
        return errors
    if not isinstance(metrics, dict):
        return ["metrics must be an object or null"]

    for name, value in metrics.items():
        if name == "thermal_state":
            if value is not None and (
                not isinstance(value, str) or value not in ALLOWED_THERMAL_STATES
            ):
                errors.append(
                    "metrics.thermal_state must be nominal, fair, serious, "
                    "critical, unknown, or null"
                )
        elif value is not None and not is_number(value):
            errors.append(f"metrics.{name} must be a finite number or null")
    return errors


def validate_suite_b(data: dict[str, Any], placeholder: bool) -> list[str]:
    if nested_value(data, "task.suite") != "Suite B: On-device Performance":
        return []

    errors = require_paths(
        data,
        SUITE_B_REQUIRED_PATHS,
        allow_null=placeholder,
    )
    if placeholder:
        return errors

    measured_run_count = nested_value(
        data, "suite_b_measurement.measured_run_count"
    )
    if (
        measured_run_count is not MISSING
        and (
            not isinstance(measured_run_count, int)
            or isinstance(measured_run_count, bool)
            or measured_run_count <= 0
        )
    ):
        errors.append(
            "suite_b_measurement.measured_run_count must be a positive integer"
        )

    metrics = data.get("metrics")
    if not isinstance(metrics, dict) or not any(
        metrics.get(name) is not None for name in SUITE_B_PRIMARY_METRICS
    ):
        errors.append("Suite B results must include at least one primary metric")

    return errors


def validate(data: dict[str, Any]) -> list[str]:
    placeholder = is_placeholder(data)
    errors = require_paths(data, REQUIRED_PATHS, allow_null=placeholder)

    errors.extend(validate_score(data, placeholder))
    errors.extend(validate_metrics(data))
    errors.extend(validate_suite_b(data, placeholder))

    raw_date = nested_value(data, "execution.date")
    if isinstance(raw_date, str):
        try:
            date.fromisoformat(raw_date)
        except ValueError:
            errors.append("execution.date must use YYYY-MM-DD format")

    access_type = nested_value(data, "model.access_type")
    if (
        access_type is not MISSING
        and access_type is not None
        and access_type not in ALLOWED_ACCESS_TYPES
    ):
        errors.append(
            "model.access_type must be api, local, xcode, hosted, or unknown"
        )

    run_type = nested_value(data, "execution.run_type")
    if (
        run_type is not MISSING
        and run_type is not None
        and run_type not in ALLOWED_RUN_TYPES
    ):
        errors.append(
            "execution.run_type must be manual, scripted, app-export, ci, or unknown"
        )

    source = nested_value(data, "provenance.source")
    if (
        source is not MISSING
        and source is not None
        and source not in ALLOWED_PROVENANCE_SOURCES
    ):
        errors.append("provenance.source is not a supported Framework v1 value")

    license_confirmation = nested_value(
        data, "license_confirmation.contributor_agrees_to_repo_license"
    )
    if license_confirmation is not MISSING and license_confirmation is not True:
        errors.append(
            "license_confirmation.contributor_agrees_to_repo_license must be true"
        )

    return errors


def validate_path(path: Path) -> list[str]:
    try:
        return validate(load_json(path))
    except (OSError, json.JSONDecodeError, ValueError) as error:
        return [f"invalid JSON: {error}"]


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "usage: validate_result.py <result.json> [result.json ...]",
            file=sys.stderr,
        )
        return 2

    failed = False
    for raw_path in sys.argv[1:]:
        path = Path(raw_path)
        errors = validate_path(path)
        if errors:
            failed = True
            for error in errors:
                print(f"{path}: {error}", file=sys.stderr)
        else:
            print(f"{path}: valid")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
