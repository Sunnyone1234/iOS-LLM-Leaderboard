#!/usr/bin/env python3
"""Validate a two-file Power 1.1 community submission package."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts import validate_suite_b_power_1_1_final_result as final
    from scripts.validate_suite_b_power_1_1_rc1_result import _validate_schema
except ModuleNotFoundError:
    import validate_suite_b_power_1_1_final_result as final
    from validate_suite_b_power_1_1_rc1_result import _validate_schema


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/suite-b-power-submission-1.1.0.schema.json"
VALIDATOR_ID = "suite-b-power-submission-validator"
VALIDATOR_VERSION = "1.1.0"
ALLOWED_PACKAGE_FILES = {"submission.json", "result.json"}
DECLARATIONS = {
    "ranOnPhysicalDevice",
    "authorizedToSubmit",
    "reviewedPublicMetadata",
    "rawResultUnmodified",
    "containsNoPersonalData",
    "acceptsCCBY40",
    "understandsNoRankingGuarantee",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _empty_report(package: Path) -> dict[str, Any]:
    return {
        "schemaVersion": "suite-b-power-submission-validation-report-1.1.0",
        "package": package.as_posix(),
        "submissionID": None,
        "resultID": None,
        "benchmarkRelease": {"id": "suite-b-power", "version": "1.1.0"},
        "validator": {"id": VALIDATOR_ID, "version": VALIDATOR_VERSION},
        "overallStatus": "invalid",
        "packageIntegrity": {"valid": False, "reasonCodes": []},
        "contributorDeclarations": {"valid": False, "reasonCodes": []},
        "powerResultValidation": None,
        "ordinaryLiveRankingEligibility": {
            "eligible": False,
            "reasonCodes": ["submission_invalid"],
        },
        "assignedEvidenceLevel": "unreviewed",
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
    entries = {path.name for path in package.iterdir()}
    missing = sorted(ALLOWED_PACKAGE_FILES - entries)
    unexpected = sorted(entries - ALLOWED_PACKAGE_FILES)
    if missing:
        errors.append(f"missing package files: {', '.join(missing)}")
    if unexpected:
        errors.append(f"unexpected package files: {', '.join(unexpected)}")
    if missing:
        return report
    if any(path.is_symlink() or not path.is_file() for path in (manifest_path, result_path)):
        errors.append("submission.json and result.json must be regular files, not symlinks")
        return report

    try:
        manifest = json.loads(manifest_path.read_text())
        schema = json.loads(SCHEMA_PATH.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        errors.append(f"submission manifest unavailable: {error}")
        return report
    report["submissionID"] = manifest.get("submissionID")
    registry = {schema["$id"]: schema}
    errors.extend(
        f"submission manifest: {error}"
        for error in _validate_schema(manifest, schema, schema, registry)
    )
    if manifest.get("submissionID") != package.name:
        errors.append("package directory name must equal submissionID")

    declarations = manifest.get("declarations", {})
    declarations_valid = all(declarations.get(key) is True for key in DECLARATIONS)
    report["contributorDeclarations"] = {
        "valid": declarations_valid,
        "reasonCodes": [] if declarations_valid else ["contributor_declaration_incomplete"],
    }
    if not declarations_valid:
        errors.append("contributor declarations are incomplete")

    try:
        result_bytes = result_path.read_bytes()
        result = json.loads(result_bytes)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        errors.append(f"result.json: {error}")
        return report
    report["resultID"] = result.get("resultID")

    reference = manifest.get("result", {})
    identity = {
        "sha256": sha256_bytes(result_bytes),
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
    for field, actual in identity.items():
        if reference.get(field) != actual:
            errors.append(f"result.{field} does not match result.json")
            integrity_reasons.append("result_reference_mismatch")

    power_report = final.validate(result, identity["sha256"])
    report["powerResultValidation"] = power_report
    shape_errors = final.validate_report_shape(power_report)
    if shape_errors:
        errors.extend(f"Power validation report: {error}" for error in shape_errors)
    if not power_report.get("structuralValidity", {}).get("valid"):
        errors.append("result.json is structurally invalid")
    if not power_report.get("protocolConformance", {}).get("valid"):
        errors.append("result.json is not protocol-conformant")

    report["packageIntegrity"] = {
        "valid": not integrity_reasons,
        "reasonCodes": list(dict.fromkeys(integrity_reasons)),
    }
    thermal = manifest.get("environmentalDisclosure", {}).get("thermalAssistance")
    ordinary_eligible = thermal == "none"
    report["ordinaryLiveRankingEligibility"] = {
        "eligible": ordinary_eligible,
        "reasonCodes": [] if ordinary_eligible else ["thermal_assistance_not_unassisted"],
    }
    if not ordinary_eligible:
        warnings.append(
            "evidence is retained but excluded from the ordinary live ranking because "
            "thermal assistance was disclosed as assisted or unknown"
        )
    warnings.append("submission has not received maintainer evidence review")
    report["warnings"] = list(dict.fromkeys(warnings))
    if not errors and declarations_valid:
        report["overallStatus"] = "validWithWarnings" if warnings else "valid"
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
            invalid = _empty_report(entry)
            invalid["errors"].append(
                "unexpected intake entry; only README.md and submission directories are allowed"
            )
            reports.append(invalid)
    return {
        "schemaVersion": "suite-b-power-intake-report-1.1.0",
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "benchmarkRelease": {"id": "suite-b-power", "version": "1.1.0"},
        "trustLevelChanged": False,
        "valid": all(item["overallStatus"] != "invalid" for item in reports),
        "entries": reports,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    report = validate_path(args.path)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered)
    print(rendered, end="")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
