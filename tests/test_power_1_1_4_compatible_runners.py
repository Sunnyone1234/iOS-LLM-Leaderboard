from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts import validate_suite_b_power_1_1_compatible_result_1_1_3 as policy_1_1_3
from scripts.generate_power_community_ranking_1_1_4 import make_contribution
from scripts.power_1_1_4 import create_package
from scripts.validate_suite_b_power_1_1_compatible_result_1_1_4 import (
    validate,
    verify_compatibility_assets,
)
from scripts.validate_suite_b_power_1_1_submission_1_1_4 import validate_package
from tests.test_power_1_1_3_compatible_runners import compatible_017_main_result
from tests.test_power_1_1_compatible_runners import digest


ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "benchmarks/suite-b-on-device-performance"
POLICY_PATH = SUITE / "power-1.1-compatible-runners-1.1.4.json"
INDEX_PATH = SUITE / "power-compatible-runners-current.json"
RELEASE_PATH = SUITE / "releases/suite-b-power-1.1.4.json"
APP_018_SOURCE_COMMIT = "8920a423f4b4abff4e34a2d8a128a3962899258e"


def compatible_018_result() -> dict:
    result = compatible_017_main_result()
    result["execution"].update(
        {
            "runnerVersion": "0.18.0",
            "appVersion": "0.18.0",
            "appBuild": "21",
            "appSourceCommit": APP_018_SOURCE_COMMIT,
        }
    )
    return result


class PowerOneOneFourCompatibleRunnerTests(unittest.TestCase):
    def test_release_assets_and_discovery_digest_are_valid(self) -> None:
        self.assertEqual(verify_compatibility_assets(), [])
        release = json.loads(RELEASE_PATH.read_text())
        self.assertEqual(release["releaseVersion"], "1.1.4")
        self.assertEqual(release["previousPublishedRelease"], "1.1.3")
        self.assertFalse(release["contractAdoption"]["protocolSemanticsChanged"])
        self.assertFalse(release["contractAdoption"]["resultSchemaChanged"])
        self.assertTrue(release["contractAdoption"]["newExecutionRequired"])

        index = json.loads(INDEX_PATH.read_text())
        current = index["currentPolicy"]
        self.assertEqual(current["policyVersion"], "1.1.4")
        self.assertEqual(current["path"], POLICY_PATH.relative_to(ROOT).as_posix())
        self.assertEqual(
            current["sha256"], hashlib.sha256(POLICY_PATH.read_bytes()).hexdigest()
        )

    def test_app_018_commit_remains_in_ios_history_when_available(self) -> None:
        policy = json.loads(POLICY_PATH.read_text())
        app_018 = next(
            runner
            for runner in policy["approvedRunners"]
            if runner["approvalID"] == "ios-compatible-app-0.18.0-build-21-main"
        )
        self.assertEqual(app_018["appSourceCommit"], APP_018_SOURCE_COMMIT)

        available = subprocess.run(
            ["git", "cat-file", "-e", f"{APP_018_SOURCE_COMMIT}^{{commit}}"],
            cwd=ROOT,
            capture_output=True,
        )
        if available.returncode != 0:
            return
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", APP_018_SOURCE_COMMIT, "HEAD"],
            cwd=ROOT,
            capture_output=True,
        )
        self.assertEqual(ancestor.returncode, 0)

    def test_previous_app_017_and_exact_app_018_are_accepted(self) -> None:
        app_017 = compatible_017_main_result()
        app_017_report = validate(app_017, digest(app_017))
        self.assertTrue(app_017_report["valid"])
        self.assertEqual(
            app_017_report["runnerCompatibility"]["approvalID"],
            "ios-compatible-app-0.17.0-build-20-main",
        )

        app_018 = compatible_018_result()
        app_018_report = validate(app_018, digest(app_018))
        self.assertTrue(app_018_report["valid"])
        self.assertEqual(
            app_018_report["runnerCompatibility"]["approvalID"],
            "ios-compatible-app-0.18.0-build-21-main",
        )

    def test_app_018_requires_exact_source_and_runtime(self) -> None:
        source_mismatch = compatible_018_result()
        source_mismatch["execution"]["appSourceCommit"] = "a" * 40
        report = validate(source_mismatch, digest(source_mismatch))
        self.assertFalse(report["valid"])

        runtime_mismatch = compatible_018_result()
        runtime_mismatch["runtime"]["version"] = "3.31.5"
        report = validate(runtime_mismatch, digest(runtime_mismatch))
        self.assertFalse(report["valid"])

    def test_policy_1_1_3_remains_immutable_and_rejects_app_018(self) -> None:
        result = compatible_018_result()
        report = policy_1_1_3.validate(result, digest(result))
        self.assertFalse(report["valid"])
        self.assertIn(
            "runner_incompatible",
            report["runnerCompatibility"]["reasonCodes"],
        )

    def test_submission_and_ranking_adapters_accept_app_018(self) -> None:
        result = compatible_018_result()
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
                created_at="2026-07-22T22:55:00Z",
            )
            report = validate_package(package)
        self.assertNotEqual(report["overallStatus"], "invalid")
        self.assertEqual(report["validator"]["version"], "1.1.4")
        self.assertEqual(
            report["runnerCompatibility"]["approvalID"],
            "ios-compatible-app-0.18.0-build-21-main",
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
            "ios-compatible-app-0.18.0-build-21-main",
        )

    def test_trusted_adapters_support_direct_ci_invocation(self) -> None:
        scripts = (
            "validate_suite_b_power_1_1_compatible_result_1_1_4.py",
            "validate_suite_b_power_1_1_submission_1_1_4.py",
            "generate_power_community_ranking_1_1_4.py",
            "triage_power_submission_pr_1_1_4.py",
            "power_1_1_4.py",
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
