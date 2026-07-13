#!/usr/bin/env python3
"""Validate Power 1.0 RC.1 evidence-review transitions."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from scripts.validate_suite_b_power_result import _validate_schema
    from scripts.validate_suite_b_power_submission import comparison_identity
    from scripts.validate_suite_b_power_submission import validate_package
except ModuleNotFoundError:
    from validate_suite_b_power_result import _validate_schema
    from validate_suite_b_power_submission import comparison_identity, validate_package


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/suite-b-power-review-1.0.0-rc.1.schema.json"
TRANSITIONS = {
    "initial-review": {("unreviewed", "community-submitted")},
    "reproduction-review": {("community-submitted", "reproduced")},
    "verification-review": {
        ("community-submitted", "verified"),
        ("reproduced", "verified"),
    },
    "maintainer-reference-review": {
        ("unreviewed", "maintainer-reference"),
        ("community-submitted", "maintainer-reference"),
    },
}


def _load_package(path: Path) -> tuple[dict[str, Any], dict[str, Any], bytes, bytes]:
    manifest_bytes = (path / "submission.json").read_bytes()
    result_bytes = (path / "result.json").read_bytes()
    return (
        json.loads(manifest_bytes),
        json.loads(result_bytes),
        manifest_bytes,
        result_bytes,
    )


def validate_reviews(submissions: Path, reviews: Path) -> dict[str, Any]:
    schema = json.loads(SCHEMA_PATH.read_text())
    packages: dict[str, dict[str, Any]] = {}
    top_level_errors: list[str] = []
    for package_path in sorted(path for path in submissions.iterdir() if path.is_dir()):
        package_report = validate_package(package_path)
        if package_report["overallStatus"] == "invalid":
            top_level_errors.append(f"invalid submission package: {package_path.as_posix()}")
            continue
        manifest, result, manifest_bytes, result_bytes = _load_package(package_path)
        submission_id = manifest.get("submissionID")
        if not isinstance(submission_id, str):
            continue
        packages[submission_id] = {
            "path": package_path,
            "report": package_report,
            "manifest": manifest,
            "result": result,
            "manifestSHA256": hashlib.sha256(manifest_bytes).hexdigest(),
            "resultSHA256": hashlib.sha256(result_bytes).hexdigest(),
        }

    parsed_reviews: list[tuple[Path, dict[str, Any], list[str]]] = []
    for path in sorted(reviews.glob("*.json")):
        errors: list[str] = []
        if path.is_symlink() or not path.is_file():
            parsed_reviews.append((path, {}, ["review record must be a regular file, not a symlink"]))
            continue
        try:
            record = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            record = {}
            errors.append(str(error))
        errors.extend(_validate_schema(record, schema, schema))
        if path.stem != record.get("reviewID"):
            errors.append("review filename must equal reviewID")
        parsed_reviews.append((path, record, errors))

    for path in sorted(reviews.iterdir()):
        if path.name == "README.md" or (path.suffix == ".json" and not path.is_dir()):
            continue
        top_level_errors.append(
            f"unexpected review entry; only README.md and review JSON files are allowed: {path.as_posix()}"
        )

    parsed_reviews.sort(key=lambda item: (str(item[1].get("reviewedAt", "")), item[0].name))
    levels = {submission_id: "unreviewed" for submission_id in packages}
    entries: list[dict[str, Any]] = []
    seen_review_ids: set[str] = set()

    for path, record, errors in parsed_reviews:
        review_id = record.get("reviewID")
        submission_id = record.get("submissionID")
        if review_id in seen_review_ids:
            errors.append("duplicate reviewID")
        if isinstance(review_id, str):
            seen_review_ids.add(review_id)
        package = packages.get(submission_id)
        if package is None:
            errors.append("referenced submission package does not exist")
        else:
            if package["report"]["overallStatus"] == "invalid":
                errors.append("referenced submission package is invalid")
            comparisons = {
                "submissionManifestSHA256": package["manifestSHA256"],
                "resultID": package["result"].get("resultID"),
                "resultSHA256": package["resultSHA256"],
            }
            for field, expected in comparisons.items():
                if record.get(field) != expected:
                    errors.append(f"{field} does not match the immutable package")

            current_level = levels.get(submission_id, "unreviewed")
            if record.get("previousEvidenceLevel") != current_level:
                errors.append("previousEvidenceLevel does not match review history")
            transition = (
                record.get("previousEvidenceLevel"),
                record.get("assignedEvidenceLevel"),
            )
            if transition not in TRANSITIONS.get(record.get("reviewType"), set()):
                errors.append("reviewType does not allow the requested evidence transition")

            supporting_ids = record.get("supportingSubmissionIDs", [])
            if record.get("reviewType") == "reproduction-review" and not supporting_ids:
                errors.append("reproduction review requires supportingSubmissionIDs")
            if record.get("reviewType") != "reproduction-review" and supporting_ids:
                errors.append("only reproduction reviews may name supportingSubmissionIDs")
            for supporting_id in supporting_ids:
                support = packages.get(supporting_id)
                if support is None:
                    errors.append(f"supporting submission does not exist: {supporting_id}")
                    continue
                if supporting_id == submission_id:
                    errors.append("a submission cannot reproduce itself")
                if levels.get(supporting_id) not in {
                    "community-submitted", "reproduced", "verified", "maintainer-reference"
                }:
                    errors.append(f"supporting submission is not accepted: {supporting_id}")
                if comparison_identity(support["result"]) != comparison_identity(package["result"]):
                    errors.append(f"supporting submission is not comparison-compatible: {supporting_id}")
                if (
                    support["manifest"].get("contributor", {}).get("githubHandle", "").casefold()
                    == package["manifest"].get("contributor", {}).get("githubHandle", "").casefold()
                ):
                    errors.append(f"supporting submission is not contributor-independent: {supporting_id}")
                if support["result"].get("resultID") == package["result"].get("resultID"):
                    errors.append(f"supporting submission reuses resultID: {supporting_id}")
                if (
                    support["result"].get("execution", {}).get("sessionID")
                    == package["result"].get("execution", {}).get("sessionID")
                ):
                    errors.append(f"supporting submission reuses sessionID: {supporting_id}")

        if not errors and isinstance(submission_id, str):
            levels[submission_id] = record["assignedEvidenceLevel"]
        entries.append({
            "path": path.as_posix(),
            "reviewID": review_id,
            "submissionID": submission_id,
            "status": "valid" if not errors else "invalid",
            "errors": errors,
        })

    return {
        "schemaVersion": "suite-b-power-review-validation-report-1.0.0-rc.1",
        "valid": not top_level_errors and all(not entry["errors"] for entry in entries),
        "rankingChanged": False,
        "evidenceLevels": levels,
        "errors": top_level_errors,
        "entries": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submissions", type=Path, required=True)
    parser.add_argument("--reviews", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = validate_reviews(args.submissions, args.reviews)
    except (OSError, json.JSONDecodeError) as error:
        print(error)
        return 1
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered)
    print(rendered, end="")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
