#!/usr/bin/env python3
"""Validate and recalculate B-PIPE-002 pilot bundles."""
from __future__ import annotations
import json, math, statistics, sys
from pathlib import Path
from typing import Any

POINTS = {
    32: (8, "28959bfb753447f7094cca07ad6d09dd4dabee48748d9394830dd10afc12740f"),
    128: (104, "3d31c669aeab75ff7f93bd81ad5efa78a834dd72d70ffecb3fd9eb6653e07316"),
    512: (488, "a04dfc559c2b7e1eccc223a6771c3d75ba8718c500cf060bf2a0298689b17d1e"),
    2048: (2024, "9d93eb5d11a110ea9f5c71b9f866fe2fb87b726a6e92d9552dfc87f091f7e6a1"),
}
def number(v: Any) -> bool: return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
def close(a: Any, b: float) -> bool: return number(a) and math.isclose(float(a), b, rel_tol=1e-6, abs_tol=1e-6)

def validate(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schemaVersion") != "suite-b-input-sweep-bundle-0.1": errors.append("unsupported schemaVersion")
    if data.get("officialResultEligible") is not False: errors.append("officialResultEligible must be false")
    if data.get("workloadID") != "b-pipe-002-input-length-sweep" or data.get("workloadVersion") != "0.2.0-pilot": errors.append("unsupported workload identity")
    if data.get("pointOrder") != list(POINTS): errors.append("pointOrder must be 32, 128, 512, 2048")
    if data.get("outputTokenLimit") != 32: errors.append("outputTokenLimit must be 32")
    prep = data.get("modelPreparation", {})
    if prep.get("eligibleForPerformanceMeasurement") is not True or prep.get("downloadOccurredDuringSession") is not False or prep.get("cacheStateBeforePreparation") != "cached": errors.append("model preparation is ineligible")
    points = data.get("points")
    if not isinstance(points, list) or len(points) != 4: return errors + ["points must contain four entries"]
    for position, point in enumerate(points):
        target = point.get("targetInputTokens")
        if target not in POINTS or target != list(POINTS)[position]: errors.append(f"points[{position}] target/order mismatch"); continue
        padding, digest = POINTS[target]
        if point.get("paddingRepetitions") != padding or point.get("fixtureSHA256") != digest: errors.append(f"points[{position}] fixture identity mismatch")
        attempts = point.get("attempts")
        if not isinstance(attempts, list): errors.append(f"points[{position}].attempts must be an array"); continue
        warm = [a for a in attempts if a.get("role") == "warmup"]
        measured = [a for a in attempts if a.get("role") == "measured"]
        success = [a for a in measured if a.get("outcome") == "completed"]
        if len(warm) != 1 or len(measured) != 5: errors.append(f"points[{position}] must retain 1+5 attempts")
        if point.get("successfulMeasuredRuns") != len(success): errors.append(f"points[{position}] successful count mismatch")
        for ai, attempt in enumerate(attempts):
            events = attempt.get("tokenEvents", [])
            if attempt.get("outcome") == "completed" and attempt.get("promptTokenCount") != target: errors.append(f"points[{position}].attempts[{ai}] input token mismatch")
            if attempt.get("outcome") == "completed" and attempt.get("outputTokenCount") != len(events): errors.append(f"points[{position}].attempts[{ai}] output count mismatch")
            for ei, event in enumerate(events):
                if event.get("index") != ei: errors.append(f"points[{position}].attempts[{ai}] token index mismatch")
            if events:
                expected = events[0]["elapsedNanoseconds"] / 1_000_000
                if not close(attempt.get("metrics", {}).get("ttftMilliseconds"), expected): errors.append(f"points[{position}].attempts[{ai}] TTFT mismatch")
        mappings = {
            "medianPipelineTTFTMilliseconds": "ttftMilliseconds",
            "medianPrefillTokensPerSecond": "prefillTokensPerSecond",
            "medianPeakMemoryMegabytes": "peakMemoryMegabytes",
        }
        for output, metric in mappings.items():
            values = [a.get("metrics", {}).get(metric) for a in success if number(a.get("metrics", {}).get(metric))]
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
    print(f"{path}: valid Suite B input sweep bundle")
    return 0
if __name__ == "__main__": raise SystemExit(main())
