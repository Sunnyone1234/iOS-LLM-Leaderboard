#!/usr/bin/env python3
"""Create an immutable Power 1.0 RC.1 submission package from an App export."""

from __future__ import annotations

import argparse
import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

try:
    from scripts.validate_suite_b_power_result import _validate_schema
    from scripts.validate_suite_b_power_result import validate as validate_power_result
    from scripts.validate_suite_b_power_submission import SCHEMA_PATH, validate_package
except ModuleNotFoundError:
    from validate_suite_b_power_result import _validate_schema
    from validate_suite_b_power_result import validate as validate_power_result
    from validate_suite_b_power_submission import SCHEMA_PATH, validate_package


CONFLICT_CATEGORIES = {
    "none",
    "model-affiliated",
    "runtime-affiliated",
    "hardware-affiliated",
    "other-disclosed",
}


def create_package(
    result_path: Path,
    output_root: Path,
    contributor: str,
    conflict_category: str,
    conflict_statement: str,
    declarations_accepted: bool,
    display_name: str | None = None,
    submission_id: str | None = None,
    created_at: str | None = None,
) -> Path:
    if not declarations_accepted:
        raise ValueError("all contributor declarations must be explicitly accepted")
    if conflict_category not in CONFLICT_CATEGORIES:
        raise ValueError("unsupported conflict-of-interest category")
    result_bytes = result_path.read_bytes()
    result = json.loads(result_bytes)
    result_report = validate_power_result(result)
    if not result_report.get("structuralValidity", {}).get("valid"):
        raise ValueError("result is structurally invalid under the frozen Power validator")
    if not result_report.get("protocolConformance", {}).get("valid"):
        raise ValueError("result is not protocol-conformant under the frozen Power validator")

    submission_id = submission_id or str(uuid.uuid4())
    created_at = created_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    contributor_record = {"githubHandle": contributor}
    if display_name:
        contributor_record["displayName"] = display_name
    manifest = {
        "schemaVersion": "suite-b-power-submission-1.0.0-rc.1",
        "submissionID": submission_id,
        "createdAt": created_at,
        "benchmarkRelease": {"id": "suite-b-power", "version": "1.0.0-rc.1"},
        "state": "draft",
        "requestedEvidenceLevel": "community-submitted",
        "contributor": contributor_record,
        "conflictOfInterest": {
            "category": conflict_category,
            "statement": conflict_statement,
        },
        "declarations": {
            "ranOnPhysicalDevice": True,
            "authorizedToSubmit": True,
            "reviewedPublicMetadata": True,
            "rawResultUnmodified": True,
            "containsNoPersonalData": True,
            "acceptsCCBY40": True,
            "understandsNoRankingGuarantee": True,
        },
        "result": {
            "path": "result.json",
            "sha256": hashlib.sha256(result_bytes).hexdigest(),
            "schemaVersion": result.get("schemaVersion"),
            "resultID": result.get("resultID"),
            "workloadID": result.get("execution", {}).get("workloadID"),
            "artifactID": result.get("model", {}).get("artifactID"),
            "artifactRevision": result.get("model", {}).get("artifactRevision"),
            "runtimeName": result.get("runtime", {}).get("name"),
            "runtimeVersion": result.get("runtime", {}).get("version"),
            "machineIdentifier": result.get("device", {}).get("machineIdentifier"),
        },
    }
    schema = json.loads(SCHEMA_PATH.read_text())
    schema_errors = _validate_schema(manifest, schema, schema)
    if schema_errors:
        raise ValueError("; ".join(schema_errors))

    package = output_root / submission_id
    if package.exists():
        raise ValueError(f"submission package already exists: {package}")
    package.mkdir(parents=True)
    (package / "result.json").write_bytes(result_bytes)
    (package / "submission.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    package_report = validate_package(package)
    if package_report["overallStatus"] == "invalid":
        raise RuntimeError("created package failed post-write validation")
    return package


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--contributor", required=True)
    parser.add_argument("--display-name")
    parser.add_argument("--conflict-category", choices=sorted(CONFLICT_CATEGORIES), required=True)
    parser.add_argument("--conflict-statement", required=True)
    parser.add_argument(
        "--accept-declarations",
        action="store_true",
        help="Accept every declaration listed in the Power submission guide.",
    )
    args = parser.parse_args()
    try:
        package = create_package(
            result_path=args.result,
            output_root=args.output_root,
            contributor=args.contributor,
            display_name=args.display_name,
            conflict_category=args.conflict_category,
            conflict_statement=args.conflict_statement,
            declarations_accepted=args.accept_declarations,
        )
    except (OSError, json.JSONDecodeError, ValueError, RuntimeError) as error:
        print(error)
        return 1
    print(package)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
