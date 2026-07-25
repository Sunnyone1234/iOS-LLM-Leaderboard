from __future__ import annotations

import hashlib
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IDENTITY_PATH = ROOT / "ios-app/Config/release-identity.json"
PROJECT_PATH = ROOT / "ios-app/BenchmarkApp.xcodeproj/project.pbxproj"
XCCONFIG_PATH = ROOT / "ios-app/Config/AppVersion.xcconfig"
SIGNING_CONFIG_PATH = ROOT / "ios-app/Config/Signing.xcconfig"
SWIFT_PATH = (
    ROOT / "ios-app/BenchmarkApp/AppReleaseIdentity.generated.swift"
)
CURRENT_POLICY_INDEX = (
    ROOT
    / "benchmarks/suite-b-on-device-performance/"
    "power-compatible-runners-current.json"
)


class IOSAppReleaseIdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.identity = json.loads(IDENTITY_PATH.read_text())
        self.app = self.identity["app"]
        self.power = self.identity["power"]

    def test_generated_xcode_and_swift_files_are_current(self) -> None:
        completed = subprocess.run(
            [
                "python3",
                "scripts/generate_ios_app_release_identity.py",
                "--check",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_xcode_has_one_app_version_source_for_both_configurations(self) -> None:
        project = PROJECT_PATH.read_text()
        xcconfig = XCCONFIG_PATH.read_text()
        self.assertNotIn("MARKETING_VERSION =", project)
        self.assertNotIn("CURRENT_PROJECT_VERSION =", project)
        self.assertEqual(
            project.count(
                "baseConfigurationReference = "
                "A20000000000000000000048 /* Signing.xcconfig */;"
            ),
            2,
        )
        signing = SIGNING_CONFIG_PATH.read_text()
        self.assertIn('#include "AppVersion.xcconfig"', signing)
        self.assertIn('#include? "LocalSigning.xcconfig"', signing)
        self.assertNotIn("DEVELOPMENT_TEAM =", project)
        self.assertIn(
            f"MARKETING_VERSION = {self.app['version']}\n",
            xcconfig,
        )
        self.assertIn(
            f"CURRENT_PROJECT_VERSION = {self.app['build']}\n",
            xcconfig,
        )
        self.assertEqual(
            project.count(
                "AppReleaseIdentity.generated.swift in Sources"
            ),
            2,
        )
        swift = SWIFT_PATH.read_text()
        self.assertIn(
            f'static let appVersion = "{self.app["version"]}"',
            swift,
        )
        self.assertIn(
            f'static let appBuild = "{self.app["build"]}"',
            swift,
        )

        ignored = subprocess.run(
            [
                "git",
                "check-ignore",
                "ios-app/Config/LocalSigning.xcconfig",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(ignored.returncode, 0, ignored.stderr)

    def test_current_power_plans_and_schemas_match_release_identity(self) -> None:
        protocol = self.power["sourceProtocolVersion"]
        result_schema_version = self.power["resultSchemaVersion"]
        for name in (
            "suite-b-pilot-001.json",
            "b-ux-001-short-interaction.json",
        ):
            plan = json.loads(
                (ROOT / "ios-app/benchmark-plans" / name).read_text()
            )
            self.assertEqual(plan["plan_version"], protocol)
            self.assertEqual(
                plan["workload"]["workload_version"],
                protocol,
            )

        result_schema = json.loads(
            (ROOT / "schemas" / f"{result_schema_version}.schema.json")
            .read_text()
        )
        self.assertEqual(
            result_schema["properties"]["schemaVersion"]["const"],
            result_schema_version,
        )
        release = result_schema["properties"]["benchmarkRelease"][
            "properties"
        ]
        self.assertEqual(release["id"]["const"], self.power["releaseID"])
        self.assertEqual(release["version"]["const"], protocol)
        self.assertEqual(release["protocolVersion"]["const"], protocol)
        self.assertEqual(
            result_schema["properties"]["execution"]["properties"][
                "workloadVersion"
            ]["const"],
            protocol,
        )

        submission_schema = json.loads(
            (
                ROOT
                / "schemas"
                / f"{self.power['submissionSchemaVersion']}.schema.json"
            ).read_text()
        )
        self.assertEqual(
            submission_schema["properties"]["schemaVersion"]["const"],
            self.power["submissionSchemaVersion"],
        )
        self.assertEqual(
            submission_schema["properties"]["benchmarkRelease"][
                "properties"
            ]["version"]["const"],
            self.power["publishedReleaseVersion"],
        )
        self.assertEqual(
            submission_schema["properties"]["result"]["properties"][
                "schemaVersion"
            ]["const"],
            result_schema_version,
        )
        self.assertTrue((ROOT / self.power["submissionDirectory"]).is_dir())

    def test_published_release_adopts_the_exact_source_protocol(self) -> None:
        release_path = (
            ROOT
            / "benchmarks/suite-b-on-device-performance/releases"
            / (
                "suite-b-power-"
                f"{self.power['publishedReleaseVersion']}.json"
            )
        )
        release = json.loads(release_path.read_text())
        self.assertEqual(release["releaseID"], self.power["releaseID"])
        self.assertEqual(
            release["releaseVersion"],
            self.power["publishedReleaseVersion"],
        )
        self.assertEqual(
            release["contractAdoption"]["sourceRelease"],
            {
                "id": self.power["releaseID"],
                "version": self.power["sourceProtocolVersion"],
            },
        )
        self.assertFalse(
            release["contractAdoption"]["protocolSemanticsChanged"]
        )
        self.assertFalse(
            release["contractAdoption"]["resultSchemaChanged"]
        )

    def test_historical_compatibility_assets_are_retained_but_not_current_ci(
        self,
    ) -> None:
        index = json.loads(CURRENT_POLICY_INDEX.read_text())
        current = index["currentPolicy"]
        policy_path = ROOT / current["path"]
        policy = json.loads(policy_path.read_text())
        self.assertEqual(
            current["sha256"],
            hashlib.sha256(policy_path.read_bytes()).hexdigest(),
        )
        self.assertEqual(policy["policyVersion"], current["policyVersion"])
        self.assertEqual(
            policy["benchmarkRelease"]["sourceRelease"],
            {
                "id": self.power["releaseID"],
                "version": self.power["publishedReleaseVersion"],
            },
        )
        self.assertFalse(policy["protocolSemanticsChanged"])
        self.assertFalse(policy["resultSchemaChanged"])

        suffix = current["policyVersion"].replace(".", "_")
        adapters = (
            f"validate_suite_b_power_1_1_compatible_result_{suffix}.py",
            f"validate_suite_b_power_1_1_submission_{suffix}.py",
            f"generate_power_community_ranking_{suffix}.py",
            f"triage_power_submission_pr_{suffix}.py",
        )
        for name in adapters:
            self.assertTrue((ROOT / "scripts" / name).is_file(), name)
        ranking_workflow = (
            ROOT / ".github/workflows/power-community-ranking.yml"
        ).read_text()
        triage_workflow = (
            ROOT / ".github/workflows/power-submission-triage.yml"
        ).read_text()
        for name in adapters[:3]:
            self.assertNotIn(name, ranking_workflow)
        self.assertNotIn(Path(adapters[3]).stem, triage_workflow)
        self.assertNotIn("scripts/power validate", ranking_workflow)
        self.assertIn("scripts/power preview", ranking_workflow)
        self.assertIn("scripts/triage_power2_submission_pr.py", triage_workflow)

    def test_current_app_version_is_never_silently_reused(self) -> None:
        index = json.loads(CURRENT_POLICY_INDEX.read_text())
        policy = json.loads((ROOT / index["currentPolicy"]["path"]).read_text())
        matching = [
            runner
            for runner in policy["approvedRunners"]
            if runner["appVersion"] == self.app["version"]
            and runner["appBuild"] == self.app["build"]
        ]
        if not matching:
            return
        self.assertEqual(len(matching), 1)
        source_commit = subprocess.run(
            ["git", "log", "-1", "--format=%H", "--", "ios-app"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertEqual(matching[0]["appSourceCommit"], source_commit)


if __name__ == "__main__":
    unittest.main()
