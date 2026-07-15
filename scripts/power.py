#!/usr/bin/env python3
"""Small public CLI for Power 1.1 submissions and local ranking previews."""

from __future__ import annotations

import argparse
import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

try:
    from scripts import generate_power_community_ranking as ranking
    from scripts import validate_suite_b_power_1_1_final_result as final
    from scripts.validate_suite_b_power_1_1_submission import validate_package, validate_path
    from scripts.validate_suite_b_power_1_1_rc1_result import _validate_schema
except ModuleNotFoundError:
    import generate_power_community_ranking as ranking
    import validate_suite_b_power_1_1_final_result as final
    from validate_suite_b_power_1_1_submission import validate_package, validate_path
    from validate_suite_b_power_1_1_rc1_result import _validate_schema


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INTAKE = ROOT / "submissions/suite-b/power-1.1.0/draft"
SCHEMA = ROOT / "schemas/suite-b-power-submission-1.1.0.schema.json"
CONFLICT_CATEGORIES = {
    "none",
    "model-affiliated",
    "runtime-affiliated",
    "hardware-affiliated",
    "other-disclosed",
}
THERMAL_ASSISTANCE = {
    "none",
    "deliberate-cooling",
    "deliberate-heating",
    "other-assisted",
    "unknown",
}


def create_package(
    result_path: Path,
    output_root: Path,
    contributor: str,
    *,
    declarations_accepted: bool,
    conflict_category: str = "none",
    conflict_statement: str | None = None,
    display_name: str | None = None,
    thermal_assistance: str = "none",
    environment_notes: str | None = None,
    submission_id: str | None = None,
    created_at: str | None = None,
) -> Path:
    if not declarations_accepted:
        raise ValueError("pass --accept-declarations after reviewing the contributor guide")
    if conflict_category not in CONFLICT_CATEGORIES:
        raise ValueError("unsupported conflict-of-interest category")
    if thermal_assistance not in THERMAL_ASSISTANCE:
        raise ValueError("unsupported thermal-assistance disclosure")
    if conflict_statement is None:
        if conflict_category == "none":
            conflict_statement = "No conflict of interest disclosed."
        else:
            raise ValueError("--conflict-statement is required for an affiliated disclosure")

    result_bytes = result_path.read_bytes()
    result = json.loads(result_bytes)
    digest = hashlib.sha256(result_bytes).hexdigest()
    result_report = final.validate(result, digest)
    if not result_report.get("structuralValidity", {}).get("valid"):
        raise ValueError("result is structurally invalid under Power 1.1")
    if not result_report.get("protocolConformance", {}).get("valid"):
        raise ValueError("result is not protocol-conformant under Power 1.1")
    shape_errors = final.validate_report_shape(result_report)
    if shape_errors:
        raise RuntimeError("invalid final validation report: " + "; ".join(shape_errors))

    submission_id = submission_id or str(uuid.uuid4())
    created_at = created_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    contributor_record = {"githubHandle": contributor}
    if display_name:
        contributor_record["displayName"] = display_name
    environment = {"thermalAssistance": thermal_assistance}
    if environment_notes:
        environment["notes"] = environment_notes
    manifest = {
        "schemaVersion": "suite-b-power-submission-1.1.0",
        "submissionID": submission_id,
        "createdAt": created_at,
        "benchmarkRelease": {"id": "suite-b-power", "version": "1.1.0"},
        "state": "draft",
        "requestedEvidenceLevel": "community-submitted",
        "contributor": contributor_record,
        "conflictOfInterest": {
            "category": conflict_category,
            "statement": conflict_statement,
        },
        "environmentalDisclosure": environment,
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
            "sha256": digest,
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
    schema = json.loads(SCHEMA.read_text())
    errors = _validate_schema(manifest, schema, schema, {schema["$id"]: schema})
    if errors:
        raise ValueError("; ".join(errors))

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


def _submit(args: argparse.Namespace) -> int:
    package = create_package(
        args.result,
        args.output_root,
        args.github,
        declarations_accepted=args.accept_declarations,
        conflict_category=args.conflict_category,
        conflict_statement=args.conflict_statement,
        display_name=args.display_name,
        thermal_assistance=args.thermal_assistance,
        environment_notes=args.environment_notes,
    )
    print(package.relative_to(ROOT) if package.is_relative_to(ROOT) else package)
    print("Next: review both files, commit this directory, and open a pull request.")
    return 0


def _validate(args: argparse.Namespace) -> int:
    report = validate_path(args.path)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["valid"] else 1


def _preview(args: argparse.Namespace) -> int:
    dataset = ranking.write_outputs(output=args.output)
    print(f"wrote {dataset['cellCount']} cells to {args.output}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    submit = subparsers.add_parser("submit", help="Create a Power 1.1 PR package")
    submit.add_argument("result", type=Path)
    submit.add_argument("--github", required=True, help="GitHub account opening the PR")
    submit.add_argument("--display-name")
    submit.add_argument("--output-root", type=Path, default=DEFAULT_INTAKE)
    submit.add_argument("--conflict-category", choices=sorted(CONFLICT_CATEGORIES), default="none")
    submit.add_argument("--conflict-statement")
    submit.add_argument("--thermal-assistance", choices=sorted(THERMAL_ASSISTANCE), default="none")
    submit.add_argument("--environment-notes")
    submit.add_argument("--accept-declarations", action="store_true")
    submit.set_defaults(handler=_submit)

    validate = subparsers.add_parser("validate", help="Validate a package or intake directory")
    validate.add_argument("path", type=Path)
    validate.set_defaults(handler=_validate)

    preview = subparsers.add_parser("preview", help="Regenerate the live ranking locally")
    preview.add_argument("--output", type=Path, default=ranking.DEFAULT_OUTPUT)
    preview.set_defaults(handler=_preview)

    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, RuntimeError) as error:
        print(f"error: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
