#!/usr/bin/env python3
"""Safely classify a Power 1.1 evidence-only pull request.

The script runs from the trusted base checkout. It reads candidate package bytes
from a git object rather than executing code from the pull request.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

from scripts import generate_power_community_ranking as ranking
from scripts.validate_suite_b_power_1_1_submission import validate_package


ROOT = Path(__file__).resolve().parents[1]
INTAKE = PurePosixPath("submissions/suite-b/power-1.1.0/draft")
PACKAGE_FILES = {"submission.json", "result.json"}
MAX_PACKAGES_PER_PR = 10
UUID_PATTERN = re.compile(
    r"^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[1-5][0-9A-Fa-f]{3}-"
    r"[89ABab][0-9A-Fa-f]{3}-[0-9A-Fa-f]{12}$"
)


def _git(*args: str, cwd: Path = ROOT) -> bytes:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _changes(base_ref: str, head_ref: str) -> list[tuple[str, str]]:
    lines = _git(
        "diff", "--name-status", "--no-renames", f"{base_ref}...{head_ref}"
    ).decode("utf-8")
    changes: list[tuple[str, str]] = []
    for line in lines.splitlines():
        if not line:
            continue
        status, separator, path = line.partition("\t")
        if not separator:
            raise ValueError(f"unparseable git diff entry: {line}")
        changes.append((status, path))
    return changes


def _candidate_packages(
    changes: list[tuple[str, str]],
) -> tuple[dict[str, set[str]], list[str]]:
    packages: dict[str, set[str]] = {}
    errors: list[str] = []
    for status, raw_path in changes:
        path = PurePosixPath(raw_path)
        parts = path.parts
        if (
            status != "A"
            or len(parts) != len(INTAKE.parts) + 2
            or parts[: len(INTAKE.parts)] != INTAKE.parts
            or parts[-1] not in PACKAGE_FILES
        ):
            errors.append(f"non-evidence-only change: {status} {raw_path}")
            continue
        submission_id = parts[-2]
        if UUID_PATTERN.fullmatch(submission_id) is None:
            errors.append(f"invalid submission directory name: {submission_id}")
            continue
        packages.setdefault(submission_id, set()).add(parts[-1])
    if not packages:
        errors.append("no Power 1.1 submission package was added")
    if len(packages) > MAX_PACKAGES_PER_PR:
        errors.append(
            f"a pull request may add at most {MAX_PACKAGES_PER_PR} packages"
        )
    for submission_id, names in sorted(packages.items()):
        if names != PACKAGE_FILES:
            missing = ", ".join(sorted(PACKAGE_FILES - names))
            errors.append(f"{submission_id}: incomplete package; missing {missing}")
    return packages, errors


def _materialize_package(head_ref: str, submission_id: str, root: Path) -> Path:
    package = root / submission_id
    package.mkdir()
    for name in sorted(PACKAGE_FILES):
        source = (INTAKE / submission_id / name).as_posix()
        (package / name).write_bytes(_git("show", f"{head_ref}:{source}"))
    return package


def classify(
    base_ref: str,
    head_ref: str,
    expected_contributor: str,
) -> dict[str, Any]:
    changes = _changes(base_ref, head_ref)
    touches_intake = any(
        PurePosixPath(path).parts[: len(INTAKE.parts)] == INTAKE.parts
        for _status, path in changes
    )
    if not touches_intake:
        return {
            "schemaVersion": "power-submission-pr-triage-1.0",
            "classification": "not_applicable",
            "expectedContributor": expected_contributor,
            "packageCount": 0,
            "reasonCodes": [],
            "errors": [],
            "warnings": [],
            "packages": [],
        }
    package_names, change_errors = _candidate_packages(changes)
    report: dict[str, Any] = {
        "schemaVersion": "power-submission-pr-triage-1.0",
        "classification": "rejected",
        "expectedContributor": expected_contributor,
        "packageCount": len(package_names),
        "reasonCodes": [],
        "errors": list(change_errors),
        "warnings": [],
        "packages": [],
    }
    if change_errors:
        report["reasonCodes"].append("pull_request_scope_invalid")
        return report

    manual_reasons: list[str] = []
    with tempfile.TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        candidate_root = temporary_root / "candidate"
        candidate_root.mkdir()
        combined_root = temporary_root / "combined"
        shutil.copytree(ranking.DEFAULT_CURRENT_SUBMISSIONS, combined_root)

        for submission_id in sorted(package_names):
            package = _materialize_package(head_ref, submission_id, candidate_root)
            package_report = validate_package(package)
            manifest = json.loads((package / "submission.json").read_text())
            contributor = manifest.get("contributor", {}).get("githubHandle")
            package_summary = {
                "submissionID": submission_id,
                "overallStatus": package_report["overallStatus"],
                "contributor": contributor,
                "ordinaryLiveRankingEligible": package_report[
                    "ordinaryLiveRankingEligibility"
                ]["eligible"],
                "performanceRankingEligible": bool(
                    package_report.get("powerResultValidation", {})
                    .get("performanceRankingEligibility", {})
                    .get("eligible")
                ),
                "recommendationEligible": bool(
                    package_report.get("powerResultValidation", {})
                    .get("recommendationEligibility", {})
                    .get("eligible")
                ),
                "runnerApprovalID": package_report.get(
                    "runnerCompatibility", {}
                ).get("approvalID"),
            }
            report["packages"].append(package_summary)

            if package_report["overallStatus"] == "invalid":
                report["reasonCodes"].append("submission_invalid")
                report["errors"].extend(
                    f"{submission_id}: {error}"
                    for error in package_report.get("errors", [])
                )
                continue
            if not isinstance(contributor, str) or (
                contributor.casefold() != expected_contributor.casefold()
            ):
                report["reasonCodes"].append("contributor_mismatch")
                report["errors"].append(
                    f"{submission_id}: contributor.githubHandle must match "
                    f"pull-request author {expected_contributor}"
                )
            if not package_summary["performanceRankingEligible"]:
                report["reasonCodes"].append("primary_metric_ineligible")
                report["errors"].append(
                    f"{submission_id}: the workload primary metric is ineligible"
                )

            conflict = manifest.get("conflictOfInterest", {}).get("category")
            if conflict != "none":
                manual_reasons.append("conflict_disclosure_requires_review")
            if not package_summary["ordinaryLiveRankingEligible"]:
                manual_reasons.append("environmental_disclosure_requires_review")

            shutil.copytree(package, combined_root / submission_id)

        if not report["errors"]:
            try:
                ranking.build_dataset(current_submissions_path=combined_root)
            except (OSError, KeyError, ValueError, json.JSONDecodeError) as error:
                report["reasonCodes"].append("duplicate_or_dataset_conflict")
                report["errors"].append(str(error))

    report["reasonCodes"] = list(dict.fromkeys(report["reasonCodes"]))
    if report["errors"]:
        report["classification"] = "rejected"
        return report
    if manual_reasons:
        report["classification"] = "manual_review"
        report["reasonCodes"] = list(dict.fromkeys(manual_reasons))
        report["warnings"].append(
            "valid evidence is retained for review but is not eligible for automatic merge"
        )
        return report
    report["classification"] = "auto_accept"
    report["reasonCodes"] = []
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--expected-contributor", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        report = classify(args.base, args.head, args.expected_contributor)
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        ValueError,
        subprocess.CalledProcessError,
    ) as error:
        report = {
            "schemaVersion": "power-submission-pr-triage-1.0",
            "classification": "rejected",
            "expectedContributor": args.expected_contributor,
            "packageCount": 0,
            "reasonCodes": ["triage_failed"],
            "errors": [str(error)],
            "warnings": [],
            "packages": [],
        }
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered)
    print(rendered, end="")
    print(f"classification={report['classification']}", file=sys.stderr)
    return 0 if report["classification"] != "rejected" else 1


if __name__ == "__main__":
    raise SystemExit(main())
