#!/usr/bin/env python3
"""Validate draft Suite B v2 workload manifests and local fixture hashes."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ID_PATTERN = re.compile(r"^b-(ux|pipe)-[0-9]{3}-[a-z0-9-]+$")
STATUSES = {
    "design-draft",
    "validation-candidate",
    "pilot-validated",
    "pilot-mapped",
    "active",
    "deprecated",
}
CATEGORIES = {"user-experience", "pipeline"}


def validate(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = (
        "schema_version",
        "workload_id",
        "workload_version",
        "status",
        "category",
        "title",
        "scenario",
        "official_result_eligible",
        "input",
        "output",
        "measurement_mode",
        "metric_set",
        "primary_metrics",
    )
    for key in required:
        if key not in data:
            errors.append(f"missing required field: {key}")

    if data.get("schema_version") != "suite-b-workload-0.1":
        errors.append("schema_version must be suite-b-workload-0.1")
    workload_id = data.get("workload_id")
    if not isinstance(workload_id, str) or not ID_PATTERN.fullmatch(workload_id):
        errors.append("workload_id has an invalid format")
    if data.get("status") not in STATUSES:
        errors.append("status is unsupported")
    if data.get("category") not in CATEGORIES:
        errors.append("category is unsupported")
    if not isinstance(data.get("official_result_eligible"), bool):
        errors.append("official_result_eligible must be boolean")
    if data.get("status") != "active" and data.get("official_result_eligible") is True:
        errors.append("non-active workloads cannot be official-result eligible")
    if data.get("metric_set") != "suite-b-metrics-0.1":
        errors.append("metric_set must be suite-b-metrics-0.1")
    metrics = data.get("primary_metrics")
    if not isinstance(metrics, list) or not metrics or not all(
        isinstance(metric, str) and metric for metric in metrics
    ):
        errors.append("primary_metrics must be a non-empty string array")
    elif len(metrics) != len(set(metrics)):
        errors.append("primary_metrics must not contain duplicates")

    input_value = data.get("input")
    if not isinstance(input_value, dict):
        errors.append("input must be an object")
    else:
        if input_value.get("token_count_scope") != "post-chat-template-model-input":
            errors.append("input.token_count_scope is unsupported")
        fixture = input_value.get("fixture_path")
        digest = input_value.get("sha256")
        if fixture is None and digest is not None:
            errors.append("input.sha256 requires input.fixture_path")
        if fixture is not None:
            if not isinstance(fixture, str) or not fixture:
                errors.append("input.fixture_path must be a non-empty string or null")
            else:
                path = ROOT / fixture
                if not path.is_file():
                    errors.append(f"input fixture does not exist: {fixture}")
                elif not isinstance(digest, str) or len(digest) != 64:
                    errors.append("input.sha256 must be a 64-character digest")
                elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                    errors.append("input.sha256 does not match the fixture")
        question = input_value.get("question_path")
        question_digest = input_value.get("question_sha256")
        if question is not None:
            question_path = ROOT / question
            if not question_path.is_file():
                errors.append(f"input question does not exist: {question}")
            elif not isinstance(question_digest, str) or len(question_digest) != 64:
                errors.append("input.question_sha256 must be a 64-character digest")
            elif hashlib.sha256(question_path.read_bytes()).hexdigest() != question_digest:
                errors.append("input.question_sha256 does not match the question")

    output = data.get("output")
    if not isinstance(output, dict):
        errors.append("output must be an object")
    else:
        maximum = output.get("maximum_tokens")
        if not isinstance(maximum, int) or isinstance(maximum, bool) or maximum <= 0:
            errors.append("output.maximum_tokens must be a positive integer")

    return errors


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError("top-level JSON value must be an object")
    return data


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: validate_suite_b_workload.py <workload.json> [...]", file=sys.stderr)
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
            print(f"{path}: valid Suite B workload manifest")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
