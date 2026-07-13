#!/usr/bin/env python3
"""Validate immutable Suite B Power 1.0 RC.1 submission packages."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts.validate_suite_b_power_result import _validate_schema
    from scripts.validate_suite_b_power_result import validate as validate_power_result
except ModuleNotFoundError:
    from validate_suite_b_power_result import _validate_schema
    from validate_suite_b_power_result import validate as validate_power_result


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/suite-b-power-submission-1.0.0-rc.1.schema.json"
VALIDATOR_ID = "suite-b-power-submission-validator"
VALIDATOR_VERSION = "1.0.0-rc.1"
ALLOWED_PACKAGE_FILES = {"submission.json", "result.json"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def comparison_identity(result: dict[str, Any]) -> dict[str, Any]:
    execution = result.get("execution", {})
    model = result.get("model", {})
    return {
        "benchmarkRelease": result.get("benchmarkRelease"),
        "workload": {
            "id": execution.get("workloadID"),
            "version": execution.get("workloadVersion"),
            "measurementModeID": execution.get("measurementModeID"),
            "fixtureSHA256": execution.get("fixtureSHA256"),
        },
        "configuration": result.get("configuration"),
        "model": {
            "artifactID": model.get("artifactID"),
            "artifactRevision": model.get("artifactRevision"),
            "artifactContentHash": model.get("artifactContentHash"),
            "quantization": model.get("quantization"),
            "modelFormat": model.get("modelFormat"),
            "tokenizerIdentity": model.get("tokenizerIdentity"),
        },
        "runtime": result.get("runtime"),
        "device": result.get("device"),
    }


def _empty_report(package: Path) -> dict[str, Any]:
    return {
        "schemaVersion": "suite-b-power-submission-validation-report-1.0.0-rc.1",
        "package": package.as_posix(),
        "submissionID": None,
        "resultID": None,
        "benchmarkRelease": {"id": "suite-b-power", "version": "1.0.0-rc.1"},
        "validator": {"id": VALIDATOR_ID, "version": VALIDATOR_VERSION},
        "overallStatus": "invalid",
        "packageIntegrity": {"valid": False, "reasonCodes": []},
        "contributorDeclarations": {"valid": False, "reasonCodes": []},
        "powerResultValidation": None,
        "assignedEvidenceLevel": "unreviewed",
        "rankingEligibility": {
            "eligible": False,
            "reasonCodes": [
                "release_candidate_not_official",
                "ranking_not_authorized",
            ],
        },
        "errors": [],
        "warnings": [],
    }


def validate_package(package: Path) -> dict[str, Any]:
    package = Path(package)
    report = _empty_report(package)
    errors: list[str] = report["errors"]
    warnings: list[str] = report["warnings"]
    manifest_path = package / "submission.json"
    result_path = package / "result.json"

    if not package.is_dir():
        errors.append("submission package must be a directory")
        return report
    actual_entries = {path.name for path in package.iterdir()}
    unexpected = sorted(actual_entries - ALLOWED_PACKAGE_FILES)
    missing = sorted(ALLOWED_PACKAGE_FILES - actual_entries)
    if missing:
        errors.append(f"missing package files: {', '.join(missing)}")
    if unexpected:
        errors.append(f"unexpected package files: {', '.join(unexpected)}")
    if missing:
        return report
    required_file_invalid = False
    for required_path in (manifest_path, result_path):
        if required_path.is_symlink() or not required_path.is_file():
            errors.append(f"{required_path.name} must be a regular file, not a symlink")
            required_file_invalid = True
    if required_file_invalid:
        return report

    try:
        manifest = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"submission.json: {error}")
        return report
    report["submissionID"] = manifest.get("submissionID")

    try:
        schema = json.loads(SCHEMA_PATH.read_text())
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"submission schema unavailable: {error}")
        return report
    schema_errors = _validate_schema(manifest, schema, schema)
    errors.extend(f"submission manifest: {error}" for error in schema_errors)
    if manifest.get("submissionID") != package.name:
        errors.append("package directory name must equal submissionID")

    declarations = manifest.get("declarations", {})
    declaration_keys = {
        "ranOnPhysicalDevice",
        "authorizedToSubmit",
        "reviewedPublicMetadata",
        "rawResultUnmodified",
        "containsNoPersonalData",
        "acceptsCCBY40",
        "understandsNoRankingGuarantee",
    }
    declaration_valid = all(declarations.get(key) is True for key in declaration_keys)
    report["contributorDeclarations"] = {
        "valid": declaration_valid,
        "reasonCodes": [] if declaration_valid else ["contributor_declaration_incomplete"],
    }
    if not declaration_valid:
        errors.append("contributor declarations are incomplete")

    try:
        result_bytes = result_path.read_bytes()
        result = json.loads(result_bytes)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        errors.append(f"result.json: {error}")
        return report
    report["resultID"] = result.get("resultID")
    reference = manifest.get("result", {})
    actual_result_sha = hashlib.sha256(result_bytes).hexdigest()
    identity_pairs = {
        "sha256": actual_result_sha,
        "schemaVersion": result.get("schemaVersion"),
        "resultID": result.get("resultID"),
        "workloadID": result.get("execution", {}).get("workloadID"),
        "artifactID": result.get("model", {}).get("artifactID"),
        "artifactRevision": result.get("model", {}).get("artifactRevision"),
        "runtimeName": result.get("runtime", {}).get("name"),
        "runtimeVersion": result.get("runtime", {}).get("version"),
        "machineIdentifier": result.get("device", {}).get("machineIdentifier"),
    }
    integrity_reasons: list[str] = []
    for field, expected in identity_pairs.items():
        if reference.get(field) != expected:
            errors.append(f"result.{field} does not match result.json")
            integrity_reasons.append("result_reference_mismatch")
    result_release = result.get("benchmarkRelease", {})
    expected_release = {
        "id": result_release.get("id"),
        "version": result_release.get("version"),
    }
    if manifest.get("benchmarkRelease") != expected_release:
        errors.append("benchmarkRelease does not match result.json")
        integrity_reasons.append("release_identity_mismatch")

    power_report = validate_power_result(result)
    report["powerResultValidation"] = power_report
    if not power_report.get("structuralValidity", {}).get("valid"):
        errors.append("result.json is structurally invalid")
    if not power_report.get("protocolConformance", {}).get("valid"):
        errors.append("result.json is not protocol-conformant")
    report["packageIntegrity"] = {
        "valid": not integrity_reasons,
        "reasonCodes": list(dict.fromkeys(integrity_reasons)),
    }
    if power_report.get("overallStatus") == "validWithWarnings":
        warnings.extend(power_report.get("warnings", []))
    warnings.extend([
        "submission has not received maintainer evidence review",
        "release candidate does not authorize leaderboard ranking",
    ])
    report["warnings"] = list(dict.fromkeys(warnings))
    if not errors and declaration_valid:
        report["overallStatus"] = "validWithWarnings"
    return report


def discover_packages(path: Path) -> list[Path]:
    if (path / "submission.json").is_file():
        return [path]
    if path.is_dir():
        return sorted(child for child in path.iterdir() if child.is_dir())
    return [path]


def validate_path(path: Path) -> dict[str, Any]:
    reports = [validate_package(package) for package in discover_packages(path)]
    if path.is_dir() and not (path / "submission.json").is_file():
        for entry in sorted(path.iterdir()):
            if entry.is_dir() or entry.name == "README.md":
                continue
            report = _empty_report(entry)
            report["errors"].append(
                "unexpected intake entry; only README.md and submission directories are allowed"
            )
            reports.append(report)
    return {
        "schemaVersion": "suite-b-power-intake-report-1.0.0-rc.1",
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "benchmarkRelease": {"id": "suite-b-power", "version": "1.0.0-rc.1"},
        "trustLevelChanged": False,
        "rankingChanged": False,
        "valid": all(report["overallStatus"] != "invalid" for report in reports),
        "entries": reports,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = validate_path(args.path)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered)
    print(rendered, end="")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
