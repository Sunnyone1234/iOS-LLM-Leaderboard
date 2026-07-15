#!/usr/bin/env python3
"""Verify one final Power 1.1 result/report pair and publication boundary."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import validate_suite_b_power_1_1_final_result as final  # noqa: E402


CONSUMER_SCHEMA_VERSION = "suite-b-power-report-consumer-1.1.0"


def verify_pair(
    result_bytes: bytes,
    result: Any,
    report: Any,
) -> list[str]:
    errors = final.validate_report_shape(report)
    if not isinstance(result, dict) or not isinstance(report, dict):
        return list(dict.fromkeys(errors + ["result and report must be JSON objects"]))

    digest = hashlib.sha256(result_bytes).hexdigest()
    reference = report.get("result")
    if not isinstance(reference, dict):
        errors.append("validation report has no result reference")
    else:
        if reference.get("sha256") != digest:
            errors.append("validation report does not bind the exact result bytes")
        if reference.get("id") != result.get("resultID"):
            errors.append("validation report result ID does not match the result")
        if reference.get("schemaVersion") != result.get("schemaVersion"):
            errors.append("validation report result schema does not match the result")

    recomputed = final.validate(result, digest)
    if report != recomputed:
        errors.append("validation report is stale or differs from deterministic validation")
    return list(dict.fromkeys(errors))


def _release_flags() -> dict[str, bool]:
    try:
        manifest = json.loads(final.MANIFEST_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return {
            "officialResultEligible": False,
            "rankingAuthorized": False,
            "publicationAuthorized": False,
            "tagAuthorized": False,
        }
    return {
        key: manifest.get(key) is True
        for key in (
            "officialResultEligible",
            "rankingAuthorized",
            "publicationAuthorized",
            "tagAuthorized",
        )
    }


def consumption_record(result: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    flags = _release_flags()
    active = all(flags.values())
    return {
        "schemaVersion": CONSUMER_SCHEMA_VERSION,
        "result": {
            "id": result["resultID"],
            "sha256": report["result"]["sha256"],
        },
        "acceptedForFinalReview": (
            report["structuralValidity"]["valid"]
            and report["protocolConformance"]["valid"]
        ),
        "measuredPerformanceRankingEligible": report[
            "performanceRankingEligibility"
        ]["eligible"],
        "recommendationEligible": report["recommendationEligibility"]["eligible"],
        "officialResultEligible": flags["officialResultEligible"],
        "rankingAuthorized": flags["rankingAuthorized"],
        "publicationAuthorized": flags["publicationAuthorized"],
        "tagAuthorized": flags["tagAuthorized"],
        "activePublicRelease": active,
        "reason": (
            "Power 1.1 publication is explicitly authorized."
            if active
            else "Power 1.1 is a final review candidate pending explicit maintainer authorization."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        result_bytes = args.result.read_bytes()
        result = json.loads(result_bytes)
        report = json.loads(args.report.read_bytes())
    except (OSError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    errors = verify_pair(result_bytes, result, report)
    if errors:
        print("error: " + "; ".join(errors), file=sys.stderr)
        return 1

    record = consumption_record(result, report)
    rendered = json.dumps(record, indent=2, sort_keys=True) + "\n"
    try:
        if args.output:
            args.output.write_text(rendered)
        else:
            print(rendered, end="")
    except OSError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0 if record["acceptedForFinalReview"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
