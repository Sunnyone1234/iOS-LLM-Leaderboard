#!/usr/bin/env python3
"""Validate Power 1.1 results under the versioned compatible-runner policy."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import validate_suite_b_power_1_1_final_result as final  # noqa: E402
from scripts import validate_suite_b_power_1_1_rc1_result as rc1  # noqa: E402


SUITE = ROOT / "benchmarks" / "suite-b-on-device-performance"
POLICY_PATH = SUITE / "power-1.1-compatible-runners-1.1.1.json"
POLICY_SCHEMA_PATH = (
    ROOT / "schemas" / "suite-b-power-compatible-runners-1.1.1.schema.json"
)
RELEASE_MANIFEST_PATH = SUITE / "releases" / "suite-b-power-1.1.1.json"
SOURCE_RELEASE_MANIFEST_PATH = SUITE / "releases" / "suite-b-power-1.1.0.json"

REPORT_SCHEMA_VERSION = "suite-b-power-compatible-result-validation-1.1.1"
POLICY_ID = "suite-b-power-runner-compatibility"
POLICY_VERSION = "1.1.1"
POLICY_RELEASE_VERSION = "1.1.1"
EXECUTION_IDENTITY_FIELDS = (
    "runnerID",
    "runnerVersion",
    "appVersion",
    "appBuild",
    "appSourceCommit",
)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def _runner_identity(data: Any) -> dict[str, Any]:
    execution = data.get("execution", {}) if isinstance(data, dict) else {}
    runtime = data.get("runtime") if isinstance(data, dict) else None
    return {
        **{field: execution.get(field) for field in EXECUTION_IDENTITY_FIELDS},
        "runtime": runtime,
    }


def _approved_identity(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        **{field: entry.get(field) for field in EXECUTION_IDENTITY_FIELDS},
        "runtime": entry.get("runtime"),
    }


def verify_compatibility_assets() -> list[str]:
    errors: list[str] = []
    try:
        manifest = _load_json(RELEASE_MANIFEST_PATH)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        return [f"runner compatibility release manifest unavailable: {error}"]

    expected_manifest = {
        "releaseID": "suite-b-power",
        "releaseVersion": POLICY_RELEASE_VERSION,
        "status": "published",
    }
    if any(manifest.get(key) != value for key, value in expected_manifest.items()):
        errors.append("runner compatibility release manifest identity mismatch")
    adoption = manifest.get("contractAdoption", {})
    expected_adoption = {
        "sourceRelease": {"id": "suite-b-power", "version": "1.1.0"},
        "protocolSemanticsChanged": False,
        "resultSchemaChanged": False,
        "referenceAppChanged": False,
        "compatibleRunnerPolicyAdded": True,
        "newExecutionRequired": True,
        "rawEvidenceMutationAllowed": False,
    }
    if any(adoption.get(key) != value for key, value in expected_adoption.items()):
        errors.append("runner compatibility contract-adoption record mismatch")

    for asset in manifest.get("pinnedAssets", []):
        if not isinstance(asset, dict):
            errors.append("runner compatibility manifest has an invalid pinned asset")
            continue
        path_value = asset.get("path")
        digest = asset.get("sha256")
        if not isinstance(path_value, str) or not isinstance(digest, str):
            errors.append("runner compatibility manifest has an incomplete pinned asset")
            continue
        path = ROOT / path_value
        if not path.is_file():
            errors.append(f"missing runner compatibility asset: {path_value}")
        elif _sha256(path) != digest:
            errors.append(f"runner compatibility asset digest mismatch: {path_value}")

    try:
        policy = _load_json(POLICY_PATH)
        schema = _load_json(POLICY_SCHEMA_PATH)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        return _unique(errors + [f"runner compatibility policy unavailable: {error}"])
    errors.extend(
        f"runner compatibility policy: {error}"
        for error in rc1._validate_schema(
            policy, schema, schema, {schema["$id"]: schema}
        )
    )
    expected_policy = {
        "policyID": POLICY_ID,
        "policyVersion": POLICY_VERSION,
        "status": "published",
        "protocolSemanticsChanged": False,
        "resultSchemaChanged": False,
        "rawEvidenceMutationAllowed": False,
    }
    if any(policy.get(key) != value for key, value in expected_policy.items()):
        errors.append("runner compatibility policy identity mismatch")

    runners = policy.get("approvedRunners", [])
    if not isinstance(runners, list):
        runners = []
    approval_ids = [
        entry.get("approvalID") for entry in runners if isinstance(entry, dict)
    ]
    identities = [
        json.dumps(_approved_identity(entry), sort_keys=True)
        for entry in runners
        if isinstance(entry, dict)
    ]
    if len(approval_ids) != len(set(approval_ids)):
        errors.append("runner compatibility approval IDs must be unique")
    if len(identities) != len(set(identities)):
        errors.append("runner compatibility identities must be unique")
    references = [
        entry for entry in runners
        if isinstance(entry, dict) and entry.get("kind") == "reference"
    ]
    compatibles = [
        entry for entry in runners
        if isinstance(entry, dict) and entry.get("kind") == "compatible"
    ]
    if len(references) != 1 or not compatibles:
        errors.append(
            "runner compatibility policy requires one reference and at least one compatible runner"
        )

    try:
        source_manifest = _load_json(SOURCE_RELEASE_MANIFEST_PATH)
        source_reference = source_manifest["referenceApp"]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, ValueError) as error:
        errors.append(f"source release reference App unavailable: {error}")
    else:
        if references:
            expected_reference = {
                "runnerID": source_reference.get("id"),
                "runnerVersion": source_reference.get("version"),
                "appVersion": source_reference.get("version"),
                "appBuild": source_reference.get("build"),
                "appSourceCommit": source_reference.get("sourceCommit"),
            }
            actual_reference = {
                field: references[0].get(field)
                for field in EXECUTION_IDENTITY_FIELDS
            }
            if actual_reference != expected_reference:
                errors.append(
                    "runner compatibility policy does not preserve the frozen reference App"
                )
    return _unique(errors)


def _load_policy() -> dict[str, Any]:
    return _load_json(POLICY_PATH)


def _match_runner(
    data: Any, policy: dict[str, Any]
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    actual = _runner_identity(data)
    for entry in policy.get("approvedRunners", []):
        if isinstance(entry, dict) and _approved_identity(entry) == actual:
            return entry, actual
    return None, actual


def _project_reference_identity(
    data: Any, reference: dict[str, Any]
) -> Any:
    projected = copy.deepcopy(data)
    if not isinstance(projected, dict):
        return projected
    execution = projected.get("execution")
    if not isinstance(execution, dict):
        return projected
    for field in EXECUTION_IDENTITY_FIELDS:
        execution[field] = reference[field]
    return projected


def validate(data: Any, result_sha256: str) -> dict[str, Any]:
    asset_errors = verify_compatibility_assets()
    policy: dict[str, Any] = {}
    policy_error: str | None = None
    try:
        policy = _load_policy()
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        policy_error = str(error)
        asset_errors.append(f"runner compatibility policy unavailable: {error}")

    matched, actual = _match_runner(data, policy)
    runners = policy.get("approvedRunners", []) if isinstance(policy, dict) else []
    reference = next(
        (
            entry for entry in runners
            if isinstance(entry, dict) and entry.get("kind") == "reference"
        ),
        None,
    )
    runner_reasons: list[str] = []
    if asset_errors or policy_error:
        runner_reasons.append("release_asset_mismatch")
    if matched is None:
        runner_reasons.append("runner_incompatible")

    validation_input = data
    if not asset_errors and matched is not None and reference is not None:
        validation_input = _project_reference_identity(data, reference)
    power_report = final.validate(validation_input, result_sha256)
    shape_errors = final.validate_report_shape(power_report)
    errors = list(asset_errors)
    errors.extend(f"Power validation report: {error}" for error in shape_errors)
    compatible = not runner_reasons
    valid = bool(
        compatible
        and not errors
        and power_report.get("structuralValidity", {}).get("valid")
        and power_report.get("protocolConformance", {}).get("valid")
    )
    return {
        "schemaVersion": REPORT_SCHEMA_VERSION,
        "result": {
            "id": data.get("resultID") if isinstance(data, dict) else None,
            "sha256": result_sha256,
            "schemaVersion": (
                data.get("schemaVersion") if isinstance(data, dict) else None
            ),
        },
        "benchmarkPolicyRelease": {
            "id": "suite-b-power",
            "version": POLICY_RELEASE_VERSION,
            "sourceRelease": {"id": "suite-b-power", "version": "1.1.0"},
        },
        "compatibilityPolicy": {"id": POLICY_ID, "version": POLICY_VERSION},
        "runnerCompatibility": {
            "compatible": compatible,
            "approvalID": matched.get("approvalID") if matched else None,
            "matchType": matched.get("kind") if matched else None,
            "actualIdentity": actual,
            "reasonCodes": _unique(runner_reasons),
        },
        "powerResultValidation": power_report,
        "valid": valid,
        "errors": _unique(errors),
    }


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
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
