#!/usr/bin/env python3
"""Validate and recalculate B-UX-002 non-official pilot bundles."""
from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any

DOCUMENT_SHA256 = "e13b4b66f137ac415bf525898f0b111d5d493d47a0a227164bba6e08f38674b4"
QUESTION_SHA256 = "86aecb086f2f2d9097b9464825249359bf08d6dc413c059756d2f850ba05f84b"
POINTS = {
    1024: (751, "a31d6da2063892ab60e7b510e8b1721dbe0f71c7a1dc43f8a787336f20427987"),
    2048: (1775, "44db8ce745be99713867619d0e18d2c0ab62148149c5ed49089053e31e27cccc"),
}


def number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def close(actual: Any, expected: float) -> bool:
    return number(actual) and math.isclose(float(actual), expected, rel_tol=1e-6, abs_tol=1e-6)


def evaluate_contract(text: Any) -> dict[str, bool]:
    value = text.lower() if isinstance(text, str) else ""
    return {
        "hasReferenceCode": "orchid-47" in value,
        "hasLocalSafetyFact": "safe" in value and any(term in value for term in ("local", "vault", "iphone")),
        "hasStableNetworkFact": "30" in value and any(term in value for term in ("stable", "seconds")),
        "hasBatteryPowerFact": any(term in value for term in ("20", "15")) and any(term in value for term in ("power", "charg")),
        "hasAvoidanceFact": any(term in value for term in ("do not", "don't", "avoid", "shouldn't")) and any(term in value for term in ("delete", "reinstall", "sign out")),
    }


def validate(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schemaVersion") != "suite-b-context-assistance-bundle-0.1": errors.append("unsupported schemaVersion")
    if data.get("officialResultEligible") is not False: errors.append("officialResultEligible must be false")
    if data.get("workloadID") != "b-ux-002-context-assistance" or data.get("workloadVersion") != "0.2.0-pilot": errors.append("unsupported workload identity")
    if data.get("documentSHA256") != DOCUMENT_SHA256 or data.get("questionSHA256") != QUESTION_SHA256: errors.append("document or question identity mismatch")
    if data.get("pointOrder") != list(POINTS): errors.append("pointOrder must be 1024, 2048")
    if data.get("outputTokenLimit") != 128: errors.append("outputTokenLimit must be 128")
    prep = data.get("modelPreparation", {})
    if prep.get("eligibleForPerformanceMeasurement") is not True or prep.get("downloadOccurredDuringSession") is not False or prep.get("cacheStateBeforePreparation") != "cached": errors.append("model preparation is ineligible")
    points = data.get("points")
    if not isinstance(points, list) or len(points) != 2: return errors + ["points must contain two entries"]
    for position, point in enumerate(points):
        target = point.get("targetInputTokens")
        if target not in POINTS or target != list(POINTS)[position]: errors.append(f"points[{position}] target/order mismatch"); continue
        padding, digest = POINTS[target]
        if point.get("paddingRepetitions") != padding or point.get("fixtureSHA256") != digest: errors.append(f"points[{position}] fixture identity mismatch")
        if point.get("timingEvidenceRetained") is not True: errors.append(f"points[{position}] timing evidence must be retained")
        attempts = point.get("attempts")
        if not isinstance(attempts, list): errors.append(f"points[{position}].attempts must be an array"); continue
        warmups = [attempt for attempt in attempts if attempt.get("role") == "warmup"]
        measured = [attempt for attempt in attempts if attempt.get("role") == "measured"]
        successful = [attempt for attempt in measured if attempt.get("outcome") == "completed"]
        if len(warmups) != 1 or len(measured) != 5: errors.append(f"points[{position}] must retain 1+5 attempts")
        if point.get("successfulMeasuredRuns") != len(successful): errors.append(f"points[{position}] successful count mismatch")
        passing = 0
        for attempt_index, attempt in enumerate(attempts):
            events = attempt.get("tokenEvents", [])
            if attempt.get("outcome") == "completed":
                if attempt.get("promptTokenCount") != target: errors.append(f"points[{position}].attempts[{attempt_index}] input token mismatch")
                if attempt.get("outputTokenCount") != len(events): errors.append(f"points[{position}].attempts[{attempt_index}] output count mismatch")
                expected_contract = evaluate_contract(attempt.get("visibleText"))
                if attempt.get("answerContract") != expected_contract: errors.append(f"points[{position}].attempts[{attempt_index}] answer contract mismatch")
                expected_eligible = all(expected_contract.values())
                if attempt.get("answerEligible") is not expected_eligible: errors.append(f"points[{position}].attempts[{attempt_index}] answer eligibility mismatch")
                if attempt.get("role") == "measured" and expected_eligible: passing += 1
            for event_index, event in enumerate(events):
                if event.get("index") != event_index: errors.append(f"points[{position}].attempts[{attempt_index}] token index mismatch")
            if events:
                expected_ttft = events[0]["elapsedNanoseconds"] / 1_000_000
                if not close(attempt.get("metrics", {}).get("ttftMilliseconds"), expected_ttft): errors.append(f"points[{position}].attempts[{attempt_index}] Pipeline TTFT mismatch")
        if point.get("answerContractPassingRuns") != passing: errors.append(f"points[{position}] answer contract count mismatch")
        eligible = len(successful) == 5 and passing == 5
        if point.get("uxPerformanceEligible") is not eligible: errors.append(f"points[{position}] UX eligibility mismatch")
        mappings = {
            "medianPipelineTTFTMilliseconds": "ttftMilliseconds",
            "medianUserVisibleTTFTMilliseconds": "userVisibleTTFTMilliseconds",
            "medianRequestCompletionMilliseconds": "requestCompletionMilliseconds",
            "medianPeakMemoryMegabytes": "peakMemoryMegabytes",
        }
        for output, metric in mappings.items():
            values = [a.get("metrics", {}).get(metric) for a in successful if number(a.get("metrics", {}).get(metric))]
            if not values or not close(point.get(output), statistics.median(values)): errors.append(f"points[{position}].{output} mismatch")
    return errors


def main() -> int:
    if len(sys.argv) != 2: return 2
    path = Path(sys.argv[1])
    try: errors = validate(json.loads(path.read_text()))
    except (OSError, json.JSONDecodeError) as error: errors = [str(error)]
    if errors:
        for error in errors: print(f"{path}: {error}", file=sys.stderr)
        return 1
    print(f"{path}: valid Suite B context assistance bundle")
    return 0


if __name__ == "__main__": raise SystemExit(main())
