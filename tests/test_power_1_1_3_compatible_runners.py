from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts import validate_suite_b_power_1_1_compatible_result_1_1_2 as policy_1_1_2
from scripts.generate_power_community_ranking_1_1_3 import make_contribution
from scripts.power_1_1_3 import create_package
from scripts.validate_suite_b_power_1_1_compatible_result_1_1_3 import (
    validate,
    verify_compatibility_assets,
)
from scripts.validate_suite_b_power_1_1_submission_1_1_3 import validate_package
from tests.test_power_1_1_2_compatible_runners import compatible_017_result
from tests.test_power_1_1_compatible_runners import digest


ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "benchmarks/suite-b-on-device-performance"
POLICY_PATH = SUITE / "power-1.1-compatible-runners-1.1.3.json"
INDEX_PATH = SUITE / "power-compatible-runners-current.json"
RELEASE_PATH = SUITE / "releases/suite-b-power-1.1.3.json"
APP_MAIN_SOURCE_COMMIT = "508eaec469b5cc0f2556d464b22d056ec7c15b03"


def compatible_017_main_result() -> dict:
    result = compatible_017_result()
    result["execution"]["appSourceCommit"] = APP_MAIN_SOURCE_COMMIT
    return result


class PowerOneOneThreeCompatibleRunnerTests(unittest.TestCase):
    def test_release_assets_and_discovery_digest_are_valid(self) -> None:
        self.assertEqual(verify_compatibility_assets(), [])
        release = json.loads(RELEASE_PATH.read_text())
        self.assertEqual(release["releaseVersion"], "1.1.3")
        self.assertEqual(release["previousPublishedRelease"], "1.1.2")
        self.assertFalse(release["contractAdoption"]["protocolSemanticsChanged"])
        self.assertFalse(release["contractAdoption"]["resultSchemaChanged"])
        self.assertTrue(release["contractAdoption"]["newExecutionRequired"])

        index = json.loads(INDEX_PATH.read_text())
        current = index["currentPolicy"]
        self.assertEqual(current["policyVersion"], "1.1.3")
        self.assertEqual(current["path"], POLICY_PATH.relative_to(ROOT).as_posix())
        self.assertEqual(
            current["sha256"], hashlib.sha256(POLICY_PATH.read_bytes()).hexdigest()
        )

    def test_main_app_commit_remains_in_ios_history_when_available(self) -> None:
        policy = json.loads(POLICY_PATH.read_text())
        main_runner = next(
            runner
            for runner in policy["approvedRunners"]
            if runner["approvalID"] == "ios-compatible-app-0.17.0-build-20-main"
        )
        self.assertEqual(main_runner["appSourceCommit"], APP_MAIN_SOURCE_COMMIT)

        available = subprocess.run(
            ["git", "cat-file", "-e", f"{APP_MAIN_SOURCE_COMMIT}^{{commit}}"],
            cwd=ROOT,
            capture_output=True,
        )
        if available.returncode != 0:
            return
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", APP_MAIN_SOURCE_COMMIT, "HEAD"],
            cwd=ROOT,
            capture_output=True,
        )
        self.assertEqual(ancestor.returncode, 0)

    def test_branch_and_main_app_017_identities_are_accepted(self) -> None:
        branch_result = compatible_017_result()
        branch_report = validate(branch_result, digest(branch_result))
        self.assertTrue(branch_report["valid"])
        self.assertEqual(
            branch_report["runnerCompatibility"]["approvalID"],
            "ios-compatible-app-0.17.0-build-20",
        )

        main_result = compatible_017_main_result()
        main_report = validate(main_result, digest(main_result))
        self.assertTrue(main_report["valid"])
        self.assertEqual(
            main_report["runnerCompatibility"]["approvalID"],
            "ios-compatible-app-0.17.0-build-20-main",
        )

    def test_main_app_identity_requires_exact_source_and_runtime(self) -> None:
        source_mismatch = compatible_017_main_result()
        source_mismatch["execution"]["appSourceCommit"] = "a" * 40
        report = validate(source_mismatch, digest(source_mismatch))
        self.assertFalse(report["valid"])

        runtime_mismatch = compatible_017_main_result()
        runtime_mismatch["runtime"]["version"] = "3.31.5"
        report = validate(runtime_mismatch, digest(runtime_mismatch))
        self.assertFalse(report["valid"])

    def test_policy_1_1_2_remains_immutable_and_rejects_main_commit(self) -> None:
        result = compatible_017_main_result()
        report = policy_1_1_2.validate(result, digest(result))
        self.assertFalse(report["valid"])
        self.assertIn(
            "runner_incompatible",
            report["runnerCompatibility"]["reasonCodes"],
        )

    def test_submission_and_ranking_adapters_accept_main_app(self) -> None:
        result = compatible_017_main_result()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result_path = root / "result.json"
            result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
            package = create_package(
                result_path,
                root / "packages",
                "ExampleContributor",
                declarations_accepted=True,
                submission_id="11111111-2222-4333-8444-555555555555",
                created_at="2026-07-22T20:15:00Z",
            )
            report = validate_package(package)
        self.assertNotEqual(report["overallStatus"], "invalid")
        self.assertEqual(report["validator"]["version"], "1.1.3")
        self.assertEqual(
            report["runnerCompatibility"]["approvalID"],
            "ios-compatible-app-0.17.0-build-20-main",
        )

        contribution = make_contribution(
            contributor="ExampleContributor",
            result=result,
            raw_path="candidate/result.json",
            raw_sha256=digest(result),
            source_kind="community-submission",
            evidence_level="unreviewed",
        )
        self.assertEqual(
            contribution["runnerCompatibility"]["approvalID"],
            "ios-compatible-app-0.17.0-build-20-main",
        )

    def test_trusted_adapters_support_direct_ci_invocation(self) -> None:
        scripts = (
            "validate_suite_b_power_1_1_compatible_result_1_1_3.py",
            "validate_suite_b_power_1_1_submission_1_1_3.py",
            "generate_power_community_ranking_1_1_3.py",
            "triage_power_submission_pr_1_1_3.py",
            "power_1_1_3.py",
        )
        for script in scripts:
            with self.subTest(script=script):
                completed = subprocess.run(
                    ["python3", f"scripts/{script}", "--help"],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
