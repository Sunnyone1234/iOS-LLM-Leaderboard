from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.power import create_package
from scripts.generate_power_community_ranking import make_contribution
from scripts import validate_suite_b_power_1_1_final_result as frozen_final
from scripts.validate_suite_b_power_1_1_compatible_result import (
    validate,
    verify_compatibility_assets,
)
from scripts.validate_suite_b_power_1_1_submission import validate_package


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = (
    ROOT
    / "results/suite-b-power-1.1.0-rc.1/device-verification/raw/"
    "2026-07-15T15-25-48Z_b-ux-001-short-interaction_"
    "mlx-community-qwen3-0.6b-4bit_iphone15-3_21b5f28f.json"
)
POLICY_PATH = (
    ROOT
    / "benchmarks/suite-b-on-device-performance/"
    "power-1.1-compatible-runners-1.1.1.json"
)
RELEASE_PATH = (
    ROOT
    / "benchmarks/suite-b-on-device-performance/releases/"
    "suite-b-power-1.1.1.json"
)
APP_SOURCE_COMMIT = "792d5e2974c3e3f131343071bb2e9d90b3231b32"


def digest(result: dict) -> str:
    raw = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def compatible_result() -> dict:
    result = json.loads(FIXTURE.read_text())
    result["execution"].update(
        {
            "runnerVersion": "0.16.0",
            "appVersion": "0.16.0",
            "appBuild": "19",
            "appSourceCommit": APP_SOURCE_COMMIT,
        }
    )
    return result


class PowerOneOneCompatibleRunnerTests(unittest.TestCase):
    def test_compatibility_release_assets_are_pinned(self) -> None:
        self.assertEqual(verify_compatibility_assets(), [])
        release = json.loads(RELEASE_PATH.read_text())
        self.assertEqual(release["releaseVersion"], "1.1.1")
        self.assertFalse(release["contractAdoption"]["protocolSemanticsChanged"])
        self.assertFalse(release["contractAdoption"]["resultSchemaChanged"])
        self.assertFalse(release["contractAdoption"]["referenceAppChanged"])
        self.assertTrue(release["contractAdoption"]["compatibleRunnerPolicyAdded"])

    def test_policy_runner_commit_remains_the_approved_app_016_commit(self) -> None:
        policy = json.loads(POLICY_PATH.read_text())
        compatible = next(
            runner
            for runner in policy["approvedRunners"]
            if runner["kind"] == "compatible"
        )
        subprocess.run(
            ["git", "cat-file", "-e", f"{APP_SOURCE_COMMIT}^{{commit}}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        self.assertEqual(compatible["appSourceCommit"], APP_SOURCE_COMMIT)

    def test_frozen_reference_and_exact_app_016_are_accepted(self) -> None:
        reference = json.loads(FIXTURE.read_text())
        reference_report = validate(reference, digest(reference))
        self.assertTrue(reference_report["valid"])
        self.assertEqual(
            reference_report["runnerCompatibility"]["matchType"], "reference"
        )

        result = compatible_result()
        original = copy.deepcopy(result)
        report = validate(result, digest(result))
        self.assertTrue(report["valid"])
        self.assertEqual(result, original)
        self.assertEqual(
            report["runnerCompatibility"]["approvalID"],
            "ios-compatible-app-0.16.0-build-19",
        )
        self.assertTrue(
            report["powerResultValidation"]["protocolConformance"]["valid"]
        )

    def test_old_unapproved_or_mismatched_app_identity_stays_rejected(self) -> None:
        old = compatible_result()
        old["execution"].update(
            {
                "runnerVersion": "0.15.0",
                "appVersion": "0.15.0",
                "appBuild": "18",
                "appSourceCommit": "0463cf42f6e236ab4838af8e371cedfd32048150",
            }
        )
        old_report = validate(old, digest(old))
        self.assertFalse(old_report["valid"])
        self.assertIn(
            "runner_incompatible",
            old_report["runnerCompatibility"]["reasonCodes"],
        )

        for field, value in (
            ("appBuild", "20"),
            ("appSourceCommit", "a" * 40),
        ):
            with self.subTest(field=field):
                mismatched = compatible_result()
                mismatched["execution"][field] = value
                report = validate(mismatched, digest(mismatched))
                self.assertFalse(report["valid"])
                self.assertIn(
                    "runner_incompatible",
                    report["runnerCompatibility"]["reasonCodes"],
                )

        runtime_mismatch = compatible_result()
        runtime_mismatch["runtime"]["version"] = "3.31.5"
        report = validate(runtime_mismatch, digest(runtime_mismatch))
        self.assertFalse(report["valid"])

    def test_frozen_validator_remains_unchanged_and_rejects_app_016(self) -> None:
        result = compatible_result()
        report = frozen_final.validate(result, digest(result))
        self.assertFalse(report["protocolConformance"]["valid"])
        self.assertIn(
            "runner_incompatible",
            report["protocolConformance"]["reasonCodes"],
        )

    def test_submission_validator_accepts_exact_app_016_package(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = compatible_result()
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
        self.assertEqual(
            report["runnerCompatibility"]["approvalID"],
            "ios-compatible-app-0.16.0-build-19",
        )
        self.assertTrue(
            report["powerResultValidation"]["performanceRankingEligibility"][
                "eligible"
            ]
        )

    def test_ranking_revalidates_app_016_through_compatibility_policy(self) -> None:
        result = compatible_result()
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
            "ios-compatible-app-0.16.0-build-19",
        )
        self.assertTrue(
            contribution["validation"]["performanceRankingEligibility"][
                "eligible"
            ]
        )


if __name__ == "__main__":
    unittest.main()
