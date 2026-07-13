#!/usr/bin/env python3
"""Validate and recalculate B-UX-001 non-official pilot bundles."""

from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any


PROMPT_SHA256 = "69b3cd45fb67e1882dabdc082636298123e01081c097af65b3fd133b19ccbc84"


def number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def close(actual: Any, expected: float) -> bool:
    return number(actual) and math.isclose(float(actual), expected, rel_tol=1e-6, abs_tol=1e-6)


def validate(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schemaVersion") != "suite-b-ux-bundle-0.1":
        errors.append("schemaVersion must be suite-b-ux-bundle-0.1")
    if data.get("officialResultEligible") is not False:
        errors.append("officialResultEligible must be false")

    plan = data.get("plan", {})
    workload = data.get("workload", {})
    mode = data.get("measurementMode", {})
    generation = data.get("generationConfiguration", {})
    if plan.get("id") != "b-ux-001-validation" or plan.get("version") != "0.2.0-pilot":
        errors.append("unsupported B-UX-001 plan identity")
    if plan.get("promptSHA256") != PROMPT_SHA256:
        errors.append("plan prompt hash mismatch")
    if plan.get("warmupRuns") != 1 or plan.get("measuredRuns") != 5:
        errors.append("B-UX-001 requires 1 warm-up and 5 measured runs")
    if plan.get("outputTokenLimit") != 128:
        errors.append("B-UX-001 output limit must be 128")
    if workload.get("id") != "b-ux-001-short-interaction" or workload.get("category") != "user-experience":
        errors.append("unsupported workload identity")
    if workload.get("promptSHA256") != PROMPT_SHA256:
        errors.append("workload prompt hash mismatch")
    if mode.get("userVisibleTTFTAvailable") is not True:
        errors.append("user-visible TTFT must be available")
    if generation.get("thinkingMode") != "disabled-via-chat-template":
        errors.append("thinking mode must be disabled via chat template")
    if generation.get("samplingEnabled") is not False or generation.get("temperature") != 0:
        errors.append("B-UX-001 must use deterministic greedy generation")

    preparation = data.get("modelPreparation", {})
    if preparation.get("eligibleForPerformanceMeasurement") is not True:
        errors.append("model preparation must be eligible")
    if preparation.get("downloadOccurredDuringSession") is not False:
        errors.append("downloaded model cannot be measured in the same session")
    if preparation.get("cacheStateBeforePreparation") != "cached":
        errors.append("model cache must be verified before preparation")

    attempts = data.get("attempts")
    if not isinstance(attempts, list):
        return errors + ["attempts must be an array"]
    warmups = [a for a in attempts if isinstance(a, dict) and a.get("role") == "warmup"]
    measured = [a for a in attempts if isinstance(a, dict) and a.get("role") == "measured"]
    successful = [a for a in measured if a.get("outcome") == "completed"]
    if len(warmups) != 1 or len(measured) != 5:
        errors.append("bundle must retain 1 warm-up and 5 measured attempts")

    for index, attempt in enumerate(attempts):
        if not isinstance(attempt, dict):
            errors.append(f"attempts[{index}] must be an object")
            continue
        events = attempt.get("tokenEvents")
        metrics = attempt.get("metrics", {})
        if not isinstance(events, list):
            errors.append(f"attempts[{index}].tokenEvents must be an array")
            continue
        for event_index, event in enumerate(events):
            if event.get("index") != event_index:
                errors.append(f"attempts[{index}] token indices must be contiguous")
        if attempt.get("outcome") == "completed":
            if attempt.get("outputTokenCount") != len(events):
                errors.append(f"attempts[{index}] output count does not match raw events")
            if not isinstance(attempt.get("visibleText"), str) or not attempt["visibleText"].strip():
                errors.append(f"attempts[{index}] visibleText must be non-empty")
            if events:
                expected_pipeline = events[0]["elapsedNanoseconds"] / 1_000_000
                if not close(metrics.get("ttftMilliseconds"), expected_pipeline):
                    errors.append(f"attempts[{index}] Pipeline TTFT does not match raw events")
            visible = metrics.get("userVisibleTTFTMilliseconds")
            completion = metrics.get("requestCompletionMilliseconds")
            pipeline = metrics.get("ttftMilliseconds")
            if not number(visible) or not number(completion):
                errors.append(f"attempts[{index}] UX timing metrics are required")
            elif number(pipeline) and not (visible >= pipeline and completion >= visible):
                errors.append(f"attempts[{index}] UX timing boundaries are out of order")

    summary = data.get("summary", {})
    if summary.get("successfulMeasuredRuns") != len(successful):
        errors.append("summary successful count mismatch")
    fields = {
        "medianPipelineTTFTMilliseconds": "ttftMilliseconds",
        "medianUserVisibleTTFTMilliseconds": "userVisibleTTFTMilliseconds",
        "medianRequestCompletionMilliseconds": "requestCompletionMilliseconds",
    }
    for summary_key, metric_key in fields.items():
        values = [a.get("metrics", {}).get(metric_key) for a in successful]
        values = [value for value in values if number(value)]
        if values and not close(summary.get(summary_key), statistics.median(values)):
            errors.append(f"summary.{summary_key} does not match attempts")
    prompt_counts = {a.get("promptTokenCount") for a in successful}
    if len(prompt_counts) != 1 or summary.get("modelInputTokens") not in prompt_counts:
        errors.append("model input token count must be stable and match summary")
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_suite_b_ux_bundle.py <bundle.json>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    try:
        data = json.loads(path.read_text())
        errors = validate(data)
    except (OSError, json.JSONDecodeError) as error:
        errors = [str(error)]
    if errors:
        for error in errors:
            print(f"{path}: {error}", file=sys.stderr)
        return 1
    print(f"{path}: valid Suite B UX bundle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
