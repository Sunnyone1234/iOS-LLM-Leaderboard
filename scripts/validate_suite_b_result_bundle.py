#!/usr/bin/env python3
"""Validate and recalculate unified Suite B result bundles."""
from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any

from scripts.validate_suite_b_context_assistance_bundle import evaluate_contract

PLANS = {
    "b-pipe-001-sustained-generation": ("b-pipe-001-validation", "0.2.0-pilot", "pipeline", 512, [], ["b865ad1a1993bfd7bf097b85f7c5585e44f1384fa291b9c05426c6051caba996"]),
    "b-ux-001-short-interaction": ("b-ux-001-validation", "0.2.0-pilot", "user-experience", 128, [], ["69b3cd45fb67e1882dabdc082636298123e01081c097af65b3fd133b19ccbc84"]),
    "b-pipe-002-input-length-sweep": ("b-pipe-002-validation", "0.2.0-pilot", "pipeline", 32, [32, 128, 512, 2048], ["28959bfb753447f7094cca07ad6d09dd4dabee48748d9394830dd10afc12740f", "3d31c669aeab75ff7f93bd81ad5efa78a834dd72d70ffecb3fd9eb6653e07316", "a04dfc559c2b7e1eccc223a6771c3d75ba8718c500cf060bf2a0298689b17d1e", "9d93eb5d11a110ea9f5c71b9f866fe2fb87b726a6e92d9552dfc87f091f7e6a1"]),
    "b-ux-002-context-assistance": ("b-ux-002-validation", "0.2.0-pilot", "user-experience", 128, [1024, 2048], ["a31d6da2063892ab60e7b510e8b1721dbe0f71c7a1dc43f8a787336f20427987", "44db8ce745be99713867619d0e18d2c0ab62148149c5ed49089053e31e27cccc"]),
}
THINKING_MODES = {
    "b-pipe-001-sustained-generation": ("disabled-via-prompt-directive", False),
    "b-ux-001-short-interaction": ("disabled-via-chat-template", True),
    "b-pipe-002-input-length-sweep": ("disabled-via-chat-template", False),
    "b-ux-002-context-assistance": ("disabled-via-chat-template", True),
}


def number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def close(actual: Any, expected: float) -> bool:
    return number(actual) and math.isclose(float(actual), expected, rel_tol=1e-6, abs_tol=1e-6)


def validate(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schemaVersion") != "suite-b-result-bundle-0.1": errors.append("unsupported schemaVersion")
    if data.get("officialResultEligible") is not False: errors.append("officialResultEligible must be false")
    workload = data.get("workload", {})
    workload_id = workload.get("id")
    if workload_id not in PLANS: return errors + ["unsupported workload identity"]
    plan_id, version, category, output_limit, targets, digests = PLANS[workload_id]
    plan = data.get("plan", {})
    if plan.get("id") != plan_id or plan.get("version") != version: errors.append("plan identity mismatch")
    if plan.get("warmupRuns") != 1 or plan.get("measuredRuns") != 5 or plan.get("outputTokenLimit") != output_limit: errors.append("plan procedure mismatch")
    if workload.get("version") != version or workload.get("category") != category or workload.get("fixtureSHA256") != digests: errors.append("workload identity mismatch")
    generation = data.get("generationConfiguration", {})
    expected_thinking, expected_visible = THINKING_MODES[workload_id]
    if generation.get("outputTokenLimit") != output_limit or generation.get("thinkingMode") != expected_thinking: errors.append("generation configuration mismatch")
    if data.get("measurementMode", {}).get("userVisibleTTFTAvailable") is not expected_visible: errors.append("measurement boundary mismatch")
    if data.get("officialResultEligible") is not data.get("eligibility", {}).get("officialLeaderboardEligible"): errors.append("official eligibility mismatch")
    prep = data.get("modelPreparation", {})
    if prep.get("eligibleForPerformanceMeasurement") is not True or prep.get("cacheStateBeforePreparation") != "cached" or prep.get("downloadOccurredDuringSession") is not False: errors.append("model preparation is ineligible")
    sessions = data.get("sessions")
    expected_count = len(targets) if targets else 1
    if not isinstance(sessions, list) or len(sessions) != expected_count: return errors + ["session count mismatch"]
    for position, session in enumerate(sessions):
        target = targets[position] if targets else None
        digest = digests[position] if targets else digests[0]
        label = f"sessions[{position}]"
        if session.get("targetInputTokens") != target or session.get("fixtureSHA256") != digest: errors.append(f"{label} point identity mismatch")
        if session.get("timingEvidenceRetained") is not True: errors.append(f"{label} timing evidence must be retained")
        attempts = session.get("attempts")
        if not isinstance(attempts, list): errors.append(f"{label}.attempts must be an array"); continue
        warmups = [a for a in attempts if a.get("role") == "warmup"]
        measured = [a for a in attempts if a.get("role") == "measured"]
        successful = [a for a in measured if a.get("outcome") == "completed"]
        if len(warmups) != 1 or len(measured) != 5: errors.append(f"{label} must retain 1+5 attempts")
        passing = 0
        for attempt_index, attempt in enumerate(attempts):
            events = attempt.get("tokenEvents", [])
            if attempt.get("outcome") == "completed":
                if target is not None and attempt.get("promptTokenCount") != target: errors.append(f"{label}.attempts[{attempt_index}] input token mismatch")
                if attempt.get("outputTokenCount") != len(events): errors.append(f"{label}.attempts[{attempt_index}] output count mismatch")
                if workload_id == "b-ux-002-context-assistance":
                    contract = evaluate_contract(attempt.get("visibleText"))
                    if attempt.get("answerContract") != contract: errors.append(f"{label}.attempts[{attempt_index}] answer contract mismatch")
                    eligible = all(contract.values())
                    if attempt.get("answerEligible") is not eligible: errors.append(f"{label}.attempts[{attempt_index}] answer eligibility mismatch")
                    if attempt.get("role") == "measured" and eligible: passing += 1
                elif attempt.get("answerContract") is not None or attempt.get("answerEligible") is not None:
                    errors.append(f"{label}.attempts[{attempt_index}] unexpected quality evidence")
            for event_index, event in enumerate(events):
                if event.get("index") != event_index: errors.append(f"{label}.attempts[{attempt_index}] token index mismatch")
            if events and not close(attempt.get("metrics", {}).get("ttftMilliseconds"), events[0]["elapsedNanoseconds"] / 1_000_000): errors.append(f"{label}.attempts[{attempt_index}] Pipeline TTFT mismatch")
        summary = session.get("summary", {})
        if summary.get("successfulMeasuredRuns") != len(successful) or summary.get("failedMeasuredRuns") != 5 - len(successful): errors.append(f"{label} run counts mismatch")
        quality = passing == 5 if workload_id == "b-ux-002-context-assistance" else None
        if session.get("qualityEligible") is not quality: errors.append(f"{label} quality eligibility mismatch")
        expected_performance = len(successful) >= 3 and (quality if quality is not None else True)
        if session.get("performanceEligible") is not expected_performance: errors.append(f"{label} performance eligibility mismatch")
        if workload_id == "b-ux-002-context-assistance" and summary.get("answerContractPassingRuns") != passing: errors.append(f"{label} answer contract count mismatch")
        mappings = {
            "medianPipelineTTFTMilliseconds": "ttftMilliseconds",
            "medianUserVisibleTTFTMilliseconds": "userVisibleTTFTMilliseconds",
            "medianRequestCompletionMilliseconds": "requestCompletionMilliseconds",
            "medianPrefillTokensPerSecond": "prefillTokensPerSecond",
            "medianDecodeTokensPerSecond": "decodeTokensPerSecond",
            "medianPeakMemoryMegabytes": "peakMemoryMegabytes",
        }
        for output, metric in mappings.items():
            values = [a.get("metrics", {}).get(metric) for a in successful if number(a.get("metrics", {}).get(metric))]
            expected = statistics.median(values) if values else None
            if expected is None:
                if summary.get(output) is not None: errors.append(f"{label}.{output} must be null")
            elif not close(summary.get(output), expected): errors.append(f"{label}.{output} mismatch")
    return errors


def main() -> int:
    if len(sys.argv) != 2: return 2
    path = Path(sys.argv[1])
    try: errors = validate(json.loads(path.read_text()))
    except (OSError, json.JSONDecodeError) as error: errors = [str(error)]
    if errors:
        for error in errors: print(f"{path}: {error}", file=sys.stderr)
        return 1
    print(f"{path}: valid unified Suite B result bundle")
    return 0


if __name__ == "__main__": raise SystemExit(main())
