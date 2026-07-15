#!/usr/bin/env python3
"""Revalidate adopted Power 1.1 RC evidence under the final ranking policy."""

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

from scripts import validate_suite_b_power_1_1_rc1_result as rc1  # noqa: E402


SUITE = ROOT / "benchmarks" / "suite-b-on-device-performance"
MANIFEST_PATH = SUITE / "releases" / "suite-b-power-1.1.0.json"
POLICY_PATH = SUITE / "power-1.1-ranking-policy.json"
REPORT_SCHEMA_PATH = ROOT / "schemas/suite-b-power-validation-report-1.1.0.schema.json"
REASON_REGISTRY_PATH = SUITE / "power-1.1-final-validation-reasons.json"

REPORT_SCHEMA_VERSION = "suite-b-power-validation-report-1.1.0"
VALIDATOR_ID = "suite-b-power-validator"
VALIDATOR_VERSION = "1.1.0"
RANKING_POLICY_ID = "suite-b-power-ranking-policy"
RANKING_POLICY_VERSION = "1.1.0"


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def verify_final_assets() -> list[str]:
    errors = [f"RC asset validation failed: {error}" for error in rc1.verify_rc_assets()]
    try:
        manifest = json.loads(MANIFEST_PATH.read_text())
    except (OSError, json.JSONDecodeError) as error:
        return errors + [f"final release manifest unavailable: {error}"]
    if manifest.get("releaseID") != "suite-b-power" or manifest.get(
        "releaseVersion"
    ) != "1.1.0":
        errors.append("final release manifest identity mismatch")
    for asset in manifest.get("pinnedAssets", []):
        if not isinstance(asset, dict):
            errors.append("final release manifest has an invalid pinned asset")
            continue
        path_value = asset.get("path")
        digest = asset.get("sha256")
        if not isinstance(path_value, str) or not isinstance(digest, str):
            errors.append("final release manifest has an incomplete pinned asset")
            continue
        path = ROOT / path_value
        if not path.is_file():
            errors.append(f"missing final release asset: {path_value}")
        elif _sha256(path) != digest:
            errors.append(f"final release asset digest mismatch: {path_value}")
    try:
        policy = json.loads(POLICY_PATH.read_text())
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"final ranking policy unavailable: {error}")
    else:
        expected = {
            "policy_id": RANKING_POLICY_ID,
            "policy_version": RANKING_POLICY_VERSION,
            "status": "final",
            "ranking_authorized": True,
        }
        if any(policy.get(key) != value for key, value in expected.items()):
            errors.append("final ranking policy identity mismatch")
    return _unique(errors)


def _report_reason_codes(value: Any) -> set[str]:
    if isinstance(value, dict):
        found = {
            reason
            for reason in value.get("reasonCodes", [])
            if isinstance(reason, str)
        }
        return found.union(*(_report_reason_codes(child) for child in value.values()))
    if isinstance(value, list):
        return set().union(*(_report_reason_codes(child) for child in value))
    return set()


def validate_report_shape(report: Any) -> list[str]:
    try:
        schema = json.loads(REPORT_SCHEMA_PATH.read_text())
    except (OSError, json.JSONDecodeError) as error:
        return [f"final validation-report schema unavailable: {error}"]
    errors = rc1._validate_schema(report, schema, schema, {schema["$id"]: schema})
    try:
        registry = set(json.loads(REASON_REGISTRY_PATH.read_text())["reason_codes"])
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        errors.append(f"final validation-reason registry unavailable: {error}")
    else:
        unregistered = _report_reason_codes(report) - registry
        if unregistered:
            errors.append(
                "$.reasonCodes contains unregistered values: "
                + ", ".join(sorted(unregistered))
            )
    return _unique(errors)


def _eligibility(eligible: bool, reasons: list[str]) -> dict[str, Any]:
    return {"eligible": eligible, "reasonCodes": _unique(reasons)}


def validate(data: Any, result_sha256: str) -> dict[str, Any]:
    report = rc1.validate(data, result_sha256)
    report["schemaVersion"] = REPORT_SCHEMA_VERSION
    report["validator"] = {"id": VALIDATOR_ID, "version": VALIDATOR_VERSION}
    report["rankingPolicy"] = {
        "id": RANKING_POLICY_ID,
        "version": RANKING_POLICY_VERSION,
    }

    asset_errors = verify_final_assets()
    if asset_errors:
        reasons = report["protocolConformance"].get("reasonCodes", [])
        report["protocolConformance"] = {
            "valid": False,
            "reasonCodes": _unique(reasons + ["release_asset_mismatch"]),
        }
        report["metricEligibility"] = {}

    structural = report["structuralValidity"]["valid"]
    protocol = report["protocolConformance"]["valid"]
    execution = data.get("execution", {}) if isinstance(data, dict) else {}
    workload = rc1.WORKLOADS.get(execution.get("workloadID"))
    primary = (
        report["metricEligibility"].get(workload["primary_metric"], {})
        if workload
        else {}
    )
    performance_eligible = bool(
        structural and protocol and primary.get("eligible") is True
    )
    performance_reasons: list[str] = []
    if not structural:
        performance_reasons.extend(
            report["structuralValidity"].get("reasonCodes", [])
        )
    if not protocol:
        performance_reasons.extend(
            report["protocolConformance"].get("reasonCodes", [])
        )
    if not primary.get("eligible"):
        performance_reasons.append("primary_metric_ineligible")
    report["performanceRankingEligibility"] = _eligibility(
        performance_eligible, performance_reasons
    )

    behavior = report["behaviorConformance"]
    behavior_eligible = not behavior["applicable"] or behavior["status"] == "verified"
    recommendation_eligible = performance_eligible and behavior_eligible
    recommendation_reasons = list(performance_reasons)
    if not behavior_eligible:
        recommendation_reasons.append("behavior_verification_required")
    report["recommendationEligibility"] = _eligibility(
        recommendation_eligible, recommendation_reasons
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        raw = args.result.read_bytes()
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    report = validate(data, _sha256_bytes(raw))
    shape_errors = validate_report_shape(report)
    if shape_errors:
        print(
            "internal final validation-report error: " + "; ".join(shape_errors),
            file=sys.stderr,
        )
        return 2
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    try:
        if args.output:
            args.output.write_text(rendered)
        else:
            print(rendered, end="")
    except OSError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0 if (
        report["structuralValidity"]["valid"]
        and report["protocolConformance"]["valid"]
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
