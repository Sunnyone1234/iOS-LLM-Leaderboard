#!/usr/bin/env python3
"""Generate suite-separated Markdown views from Framework v1 result JSON."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    from validate_result import validate
except ModuleNotFoundError:
    from scripts.validate_result import validate


ROOT = Path(__file__).resolve().parents[1]
RAW_RESULTS = ROOT / "results" / "raw"
OUTPUT = ROOT / "results" / "LEADERBOARD.md"

SUITE_ORDER = [
    "Suite A: Swift Code Generation",
    "Suite B: On-device Performance",
    "Suite C: Xcode Integration",
    "Suite D: App Feature Intelligence",
    "Suite E: Runtime Evaluation",
]

MEASUREMENT_SUITES = {
    "Suite B: On-device Performance",
    "Suite E: Runtime Evaluation",
}


def nested_value(data: dict[str, Any], path: str, default: Any = None) -> Any:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def is_publishable(data: dict[str, Any]) -> bool:
    return nested_value(data, "provenance.source") != "demo-placeholder"


def load_results() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for path in sorted(RAW_RESULTS.glob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            print(f"skipping {path}: {error}", file=sys.stderr)
            continue

        if not isinstance(data, dict):
            print(f"skipping {path}: top-level value is not an object", file=sys.stderr)
            continue

        errors = validate(data)
        if errors:
            print(
                f"skipping {path}: result does not pass Framework v1 validation",
                file=sys.stderr,
            )
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
            continue

        if not is_publishable(data):
            continue

        data["_source"] = path.relative_to(ROOT).as_posix()
        results.append(data)
    return results


def format_score(item: dict[str, Any]) -> str:
    score = nested_value(item, "evaluation.score")
    max_score = nested_value(item, "evaluation.max_score")
    if isinstance(score, (int, float)) and isinstance(max_score, (int, float)):
        return f"{score:.2f} / {max_score:g}"
    return ""


def format_metrics(item: dict[str, Any]) -> str:
    metrics = item.get("metrics")
    if not isinstance(metrics, dict):
        return ""

    parts: list[str] = []
    metric_formats = [
        ("ttft_ms", "TTFT", "ms"),
        ("prefill_tokens_per_second", "Prefill", "tok/s"),
        ("decode_tokens_per_second", "Decode", "tok/s"),
        ("peak_memory_mb", "Peak memory", "MB"),
    ]
    for key, label, unit in metric_formats:
        value = metrics.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            parts.append(f"{label}: {value:.2f} {unit}")

    thermal_state = metrics.get("thermal_state")
    if isinstance(thermal_state, str) and thermal_state:
        parts.append(f"Thermal: {thermal_state}")

    return "; ".join(parts)


def escaped(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace(
        "\n", " "
    )


def suite_sort_key(suite: str) -> tuple[int, str]:
    try:
        return (SUITE_ORDER.index(suite), suite)
    except ValueError:
        return (len(SUITE_ORDER), suite)


def render_scored_suite(
    suite: str,
    items: list[dict[str, Any]],
) -> list[str]:
    ranked = sorted(
        items,
        key=lambda item: nested_value(item, "evaluation.score", float("-inf")),
        reverse=True,
    )
    lines = [
        f"## {suite}",
        "",
        "| Rank | Model | Provider | Task | Score | Evaluator | Date | Source |",
        "| ---: | --- | --- | --- | ---: | --- | --- | --- |",
    ]
    for index, item in enumerate(ranked, start=1):
        lines.append(
            "| {rank} | {model} | {provider} | {task} | {score} | "
            "{evaluator} | {date} | {source} |".format(
                rank=index,
                model=escaped(nested_value(item, "model.model_name")),
                provider=escaped(nested_value(item, "model.provider")),
                task=escaped(nested_value(item, "task.task_id")),
                score=escaped(format_score(item)),
                evaluator=escaped(nested_value(item, "execution.evaluator")),
                date=escaped(nested_value(item, "execution.date")),
                source=escaped(nested_value(item, "provenance.source")),
            )
        )
    lines.append("")
    return lines


def render_measurement_suite(
    suite: str,
    items: list[dict[str, Any]],
) -> list[str]:
    ordered = sorted(
        items,
        key=lambda item: (
            escaped(nested_value(item, "task.task_id")),
            escaped(nested_value(item, "model.model_name")),
            escaped(nested_value(item, "device.device_name")),
        ),
    )
    lines = [
        f"## {suite}",
        "",
        "Measurement rows are not ranked by the evaluation score. Compatible "
        "metric-specific ranking rules are still required.",
        "",
        "| Model | Device | Runtime | Task | Measurements | Evidence source |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in ordered:
        lines.append(
            "| {model} | {device} | {runtime} | {task} | {metrics} | {source} |".format(
                model=escaped(nested_value(item, "model.model_name")),
                device=escaped(nested_value(item, "device.device_name")),
                runtime=escaped(nested_value(item, "runtime.runtime_name")),
                task=escaped(nested_value(item, "task.task_id")),
                metrics=escaped(format_metrics(item)),
                source=escaped(nested_value(item, "provenance.source")),
            )
        )
    lines.append("")
    return lines


def render(results: list[dict[str, Any]]) -> str:
    eligible = [item for item in results if is_publishable(item)]
    lines = [
        "# Leaderboard",
        "",
        "This file is generated from validated, non-placeholder Framework v1 "
        "JSON files in results/raw/.",
        "",
        "Suites remain separate. Measurement completeness scores are not used "
        "as device-performance rankings.",
        "",
    ]

    if not eligible:
        lines.extend(
            [
                "No eligible non-placeholder results have been submitted yet.",
                "",
            ]
        )
        return "\n".join(lines)

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in eligible:
        suite = nested_value(item, "task.suite", "Unknown Suite")
        grouped[str(suite)].append(item)

    for suite in sorted(grouped, key=suite_sort_key):
        if suite in MEASUREMENT_SUITES:
            lines.extend(render_measurement_suite(suite, grouped[suite]))
        else:
            lines.extend(render_scored_suite(suite, grouped[suite]))

    return "\n".join(lines)


def main() -> int:
    OUTPUT.write_text(render(load_results()), encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
