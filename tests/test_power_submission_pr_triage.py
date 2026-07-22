from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import triage_power_submission_pr_1_1_4 as current_triage
from scripts.power import create_package


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = (
    ROOT
    / "results/suite-b-power-1.1.0-rc.1/device-verification/raw/"
    "2026-07-15T15-25-48Z_b-ux-001-short-interaction_"
    "mlx-community-qwen3-0.6b-4bit_iphone15-3_21b5f28f.json"
)
SUBMISSION_ID = "11111111-2222-4333-8444-555555555555"
PREFIX = "submissions/suite-b/power-1.1.0/draft"
_changes = current_triage.base._changes
classify = current_triage.classify


class PowerSubmissionPRTriageTests(unittest.TestCase):
    def test_trusted_workflow_invokes_triage_as_a_module(self) -> None:
        workflow = (
            ROOT / ".github/workflows/power-submission-triage.yml"
        ).read_text()
        self.assertIn(
            "python3 -m scripts.triage_power_submission_pr_1_1_4", workflow
        )
        self.assertNotIn("python3 scripts/triage_power_submission_pr.py", workflow)

    def test_fork_checks_and_auto_merge_resolve_trusted_pr_context(self) -> None:
        identity = (ROOT / ".github/workflows/commit-identity.yml").read_text()
        self.assertIn("  pull_request_target:", identity)
        self.assertNotIn("  pull_request:\n", identity)
        self.assertIn("github.event.pull_request.base.sha || github.sha", identity)
        self.assertIn('pull/${PR_NUMBER}/head:', identity)

        auto_merge = (
            ROOT / ".github/workflows/power-submission-automerge.yml"
        ).read_text()
        self.assertIn("HEAD_REPOSITORY", auto_merge)
        self.assertIn('head="$HEAD_OWNER:$HEAD_BRANCH"', auto_merge)
        self.assertIn("headRefOid", auto_merge)
        self.assertIn("Unable to resolve an open pull request", auto_merge)

    def make_package(
        self,
        root: Path,
        *,
        contributor: str = "ExampleContributor",
        conflict: str = "none",
        thermal: str = "none",
    ) -> Path:
        result = json.loads(FIXTURE.read_text())
        result["resultID"] = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
        result["execution"]["sessionID"] = "bbbbbbbb-cccc-4ddd-8eee-ffffffffffff"
        result_path = root / "candidate-result.json"
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        statement = (
            "No conflict of interest disclosed."
            if conflict == "none"
            else "Contributor works for the model publisher."
        )
        return create_package(
            result_path,
            root / "packages",
            contributor,
            declarations_accepted=True,
            conflict_category=conflict,
            conflict_statement=statement,
            thermal_assistance=thermal,
            submission_id=SUBMISSION_ID,
            created_at="2026-07-15T16:00:00Z",
        )

    def classify_package(self, package: Path) -> dict:
        changes = [
            ("A", f"{PREFIX}/{SUBMISSION_ID}/result.json"),
            ("A", f"{PREFIX}/{SUBMISSION_ID}/submission.json"),
        ]

        def materialize(_head: str, _submission: str, root: Path) -> Path:
            target = root / SUBMISSION_ID
            shutil.copytree(package, target)
            return target

        with mock.patch.object(
            current_triage.base, "_changes", return_value=changes
        ), mock.patch.object(
            current_triage.base, "_materialize_package", side_effect=materialize
        ):
            return classify("base", "head", "ExampleContributor")

    def test_clean_metric_eligible_package_is_auto_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report = self.classify_package(self.make_package(Path(temporary)))
        self.assertEqual(report["classification"], "auto_accept")
        self.assertEqual(report["packageCount"], 1)
        self.assertTrue(report["packages"][0]["performanceRankingEligible"])

    def test_disclosed_conflict_routes_to_manual_review(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = self.make_package(Path(temporary), conflict="model-affiliated")
            report = self.classify_package(package)
        self.assertEqual(report["classification"], "manual_review")
        self.assertIn(
            "conflict_disclosure_requires_review", report["reasonCodes"]
        )

    def test_non_submission_change_is_not_applicable(self) -> None:
        with mock.patch.object(
            current_triage.base,
            "_changes",
            return_value=[("M", "README.md")],
        ):
            report = classify("base", "head", "ExampleContributor")
        self.assertEqual(report["classification"], "not_applicable")

    def test_submission_mixed_with_other_changes_is_rejected(self) -> None:
        changes = [
            ("A", f"{PREFIX}/{SUBMISSION_ID}/result.json"),
            ("A", f"{PREFIX}/{SUBMISSION_ID}/submission.json"),
            ("M", "README.md"),
        ]
        with mock.patch.object(
            current_triage.base, "_changes", return_value=changes
        ):
            report = classify("base", "head", "ExampleContributor")
        self.assertEqual(report["classification"], "rejected")
        self.assertIn("pull_request_scope_invalid", report["reasonCodes"])

    def test_changes_are_measured_from_the_pull_request_merge_base(self) -> None:
        with mock.patch.object(
            current_triage.base, "_git", return_value=b"A\tREADME.md\n"
        ) as git:
            self.assertEqual(_changes("base", "head"), [("A", "README.md")])
        git.assert_called_once_with(
            "diff", "--name-status", "--no-renames", "base...head"
        )

    def test_unsafe_submission_directory_is_rejected(self) -> None:
        changes = [
            ("A", f"{PREFIX}/../result.json"),
            ("A", f"{PREFIX}/../submission.json"),
        ]
        with mock.patch.object(
            current_triage.base, "_changes", return_value=changes
        ):
            report = classify("base", "head", "ExampleContributor")
        self.assertEqual(report["classification"], "rejected")


if __name__ == "__main__":
    unittest.main()
