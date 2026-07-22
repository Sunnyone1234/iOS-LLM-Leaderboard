from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts import validate_suite_b_power_1_1_compatible_result as policy_1_1_1
from scripts.generate_power_community_ranking_1_1_2 import make_contribution
from scripts.power_1_1_2 import create_package
from scripts.validate_suite_b_power_1_1_compatible_result_1_1_2 import (
    validate,
    verify_compatibility_assets,
)
from scripts.validate_suite_b_power_1_1_submission_1_1_2 import validate_package
from tests.test_power_1_1_compatible_runners import compatible_result, digest


ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "benchmarks/suite-b-on-device-performance"
POLICY_PATH = SUITE / "power-1.1-compatible-runners-1.1.2.json"
INDEX_PATH = SUITE / "power-compatible-runners-current.json"
RELEASE_PATH = SUITE / "releases/suite-b-power-1.1.2.json"
APP_SOURCE_COMMIT = "7e99fb060454f5f59e4255d04981d38eeec732f0"


def compatible_017_result() -> dict:
    result = compatible_result()
    result["execution"].update(
        {
            "runnerVersion": "0.17.0",
            "appVersion": "0.17.0",
            "appBuild": "20",
            "appSourceCommit": APP_SOURCE_COMMIT,
        }
    )
    return result


class PowerOneOneTwoCompatibleRunnerTests(unittest.TestCase):
    def test_release_assets_and_discovery_digest_are_valid(self) -> None:
        self.assertEqual(verify_compatibility_assets(), [])
        release = json.loads(RELEASE_PATH.read_text())
        self.assertEqual(release["releaseVersion"], "1.1.2")
        self.assertEqual(release["previousPublishedRelease"], "1.1.1")
        self.assertFalse(release["contractAdoption"]["protocolSemanticsChanged"])
        self.assertFalse(release["contractAdoption"]["resultSchemaChanged"])
        self.assertTrue(
            release["contractAdoption"]["compatibleRunnerPolicyExtended"]
        )

        index = json.loads(INDEX_PATH.read_text())
        current = index["currentPolicy"]
        self.assertEqual(current["policyVersion"], "1.1.2")
        self.assertEqual(current["path"], POLICY_PATH.relative_to(ROOT).as_posix())
        self.assertEqual(
            current["sha256"], hashlib.sha256(POLICY_PATH.read_bytes()).hexdigest()
        )

    def test_app_017_policy_commit_is_latest_ios_app_commit(self) -> None:
        policy = json.loads(POLICY_PATH.read_text())
        app_017 = next(
            runner
            for runner in policy["approvedRunners"]
            if runner["approvalID"] == "ios-compatible-app-0.17.0-build-20"
        )
        latest_ios_commit = subprocess.run(
            ["git", "log", "-1", "--format=%H", "--", "ios-app"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertEqual(app_017["appSourceCommit"], latest_ios_commit)
        self.assertEqual(app_017["appSourceCommit"], APP_SOURCE_COMMIT)

    def test_reference_app_016_and_exact_app_017_are_accepted(self) -> None:
        app_016 = compatible_result()
        report_016 = validate(app_016, digest(app_016))
        self.assertTrue(report_016["valid"])
        self.assertEqual(
            report_016["runnerCompatibility"]["approvalID"],
            "ios-compatible-app-0.16.0-build-19",
        )

        app_017 = compatible_017_result()
        report_017 = validate(app_017, digest(app_017))
        self.assertTrue(report_017["valid"])
        self.assertEqual(
            report_017["runnerCompatibility"]["approvalID"],
            "ios-compatible-app-0.17.0-build-20",
        )

    def test_app_017_requires_exact_source_and_runtime(self) -> None:
        source_mismatch = compatible_017_result()
        source_mismatch["execution"]["appSourceCommit"] = "a" * 40
        report = validate(source_mismatch, digest(source_mismatch))
        self.assertFalse(report["valid"])
        self.assertIn(
            "runner_incompatible",
            report["runnerCompatibility"]["reasonCodes"],
        )

        runtime_mismatch = compatible_017_result()
        runtime_mismatch["runtime"]["version"] = "3.31.5"
        report = validate(runtime_mismatch, digest(runtime_mismatch))
        self.assertFalse(report["valid"])

    def test_policy_1_1_1_remains_immutable_and_rejects_app_017(self) -> None:
        result = compatible_017_result()
        report = policy_1_1_1.validate(result, digest(result))
        self.assertFalse(report["valid"])
        self.assertIn(
            "runner_incompatible",
            report["runnerCompatibility"]["reasonCodes"],
        )

    def test_submission_and_ranking_adapters_accept_app_017(self) -> None:
        result = compatible_017_result()
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
                created_at="2026-07-22T15:00:00Z",
            )
            report = validate_package(package)
        self.assertNotEqual(report["overallStatus"], "invalid")
        self.assertEqual(report["validator"]["version"], "1.1.2")
        self.assertEqual(
            report["runnerCompatibility"]["approvalID"],
            "ios-compatible-app-0.17.0-build-20",
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
            "ios-compatible-app-0.17.0-build-20",
        )

    def test_trusted_adapters_support_direct_ci_invocation(self) -> None:
        scripts = (
            "validate_suite_b_power_1_1_compatible_result_1_1_2.py",
            "validate_suite_b_power_1_1_submission_1_1_2.py",
            "generate_power_community_ranking_1_1_2.py",
            "triage_power_submission_pr_1_1_2.py",
            "power_1_1_2.py",
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
