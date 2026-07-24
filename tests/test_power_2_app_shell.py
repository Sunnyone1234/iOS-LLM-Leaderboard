from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "apps" / "ios"
APP_PROJECT = APP_ROOT / "PowerBenchmarkApp.xcodeproj"
CERTIFICATION_SCHEME = (
    APP_PROJECT
    / "xcshareddata"
    / "xcschemes"
    / "PowerCertification.xcscheme"
)
OFFICIAL_SCHEME = (
    APP_PROJECT
    / "xcshareddata"
    / "xcschemes"
    / "PowerOfficial.xcscheme"
)
RUNNER_ROOT = ROOT / "apps" / "PowerRunnerKit"
APP_KIT_ROOT = ROOT / "apps" / "PowerAppKit"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Power2AppShellTests(unittest.TestCase):
    def test_product_identity_does_not_compile_repository_intake_state(
        self,
    ) -> None:
        app_manifest = subprocess.run(
            [
                "python3",
                "scripts/generate_power_app_component_manifest.py",
                "--check",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            app_manifest.returncode,
            0,
            app_manifest.stderr,
        )
        completed = subprocess.run(
            [
                "python3",
                "scripts/generate_power2_product_identity.py",
                "--check",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

        identity = (
            APP_ROOT / "Power2ProductIdentity.generated.swift"
        ).read_text(encoding="utf-8")
        model = (
            APP_ROOT
            / "PowerBenchmarkApp"
            / "PowerAppModel.swift"
        ).read_text(encoding="utf-8")
        self.assertIn("static let appReleaseAvailable = true", identity)
        self.assertNotIn("publicIntakeOpen", identity)
        self.assertNotIn("submissionRehearsalAvailable", identity)
        self.assertIn(
            "Power2ProductIdentity.appReleaseAvailable",
            model,
        )
        self.assertNotIn("publicIntakeOpen", model)
        self.assertNotIn("submissionRehearsalAvailable", model)
        self.assertIn("selectedResultMatchesCurrentRelease", model)

    def test_certification_catalog_is_generated_from_candidate(self) -> None:
        completed = subprocess.run(
            [
                "python3",
                "scripts/generate_power2_app_catalog.py",
                "--check",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

        catalog = (
            APP_ROOT / "Power2CandidateCatalog.generated.swift"
        ).read_text(encoding="utf-8")
        registry = load_json(ROOT / "models" / "registry.json")
        for entry in registry["entries"]:
            model = load_json(ROOT / entry["path"])
            self.assertIn(
                f'id: "{model["registryEntryID"]}"',
                catalog,
            )
        self.assertIn("power2-runner-", catalog)

    def test_certification_build_is_isolated_and_source_bound(self) -> None:
        project = (APP_PROJECT / "project.pbxproj").read_text(
            encoding="utf-8"
        )
        scheme = CERTIFICATION_SCHEME.read_text(encoding="utf-8")
        identity = (
            APP_ROOT
            / "PowerBenchmarkApp"
            / "PowerAppBuildIdentity.swift"
        ).read_text(encoding="utf-8")
        info_plist = (
            APP_ROOT / "PowerBenchmarkApp" / "Info.plist"
        ).read_text(encoding="utf-8")
        model = (
            APP_ROOT
            / "PowerBenchmarkApp"
            / "PowerAppModel.swift"
        ).read_text(encoding="utf-8")

        self.assertEqual(project.count("POWER_CERTIFICATION"), 1)
        self.assertIn('buildConfiguration = "Certification"', scheme)
        self.assertIn('allowLocationSimulation = "NO"', scheme)
        self.assertIn('SUPPORTED_PLATFORMS = "iphoneos";', project)
        self.assertIn("PowerSourceRevision", identity)
        self.assertIn("isValidSourceRevision", identity)
        self.assertIn(
            "generated App component-manifest ",
            identity,
        )
        self.assertIn("<key>PowerSourceRevision</key>", info_plist)
        self.assertIn(
            "<string>$(POWER_SOURCE_REVISION)</string>",
            info_plist,
        )
        self.assertIn("AppleIPhoneTargetAdapter()", model)
        self.assertIn("PowerRunner(runtime: runtime, target: target)", model)
        self.assertIn("PowerEvidenceEnvelope(", model)
        self.assertIn("store.save(envelope: envelope)", model)

    def test_candidate_rehearsal_is_read_only_and_isolated(self) -> None:
        workflow = (
            ROOT
            / ".github"
            / "workflows"
            / "power2-candidate-rehearsal.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertNotIn("pull-requests: write", workflow)
        self.assertNotIn("issues: write", workflow)
        self.assertNotIn("gh pr edit", workflow)
        self.assertNotIn("gh pr merge", workflow)
        self.assertIn(
            "scripts/triage_power2_submission_pr.py",
            workflow,
        )
        self.assertNotIn("ref: main", workflow)
        self.assertIn(
            "--base refs/remotes/origin/main",
            workflow,
        )
        self.assertIn(
            '--validator-source-revision "$(git rev-parse HEAD)"',
            workflow,
        )
        self.assertIn("--app-release-rehearsal", workflow)

    def test_signing_is_local_and_build_kinds_are_fail_closed(self) -> None:
        project = (APP_PROJECT / "project.pbxproj").read_text(
            encoding="utf-8"
        )
        signing = (
            APP_ROOT / "Configuration" / "Signing.xcconfig"
        ).read_text(encoding="utf-8")
        release_identity = load_json(
            APP_ROOT / "Configuration" / "ReleaseIdentity.json"
        )
        release_configuration = (
            APP_ROOT
            / "Configuration"
            / "ReleaseIdentity.generated.xcconfig"
        ).read_text(encoding="utf-8")
        official_scheme = OFFICIAL_SCHEME.read_text(encoding="utf-8")
        identity = (
            APP_ROOT
            / "PowerBenchmarkApp"
            / "PowerAppBuildIdentity.swift"
        ).read_text(encoding="utf-8")
        model = (
            APP_ROOT
            / "PowerBenchmarkApp"
            / "PowerAppModel.swift"
        ).read_text(encoding="utf-8")

        self.assertNotIn("DEVELOPMENT_TEAM =", project)
        self.assertIn("LocalSigning.xcconfig", signing)
        self.assertIn("ReleaseIdentity.generated.xcconfig", signing)
        self.assertIn("POWER_SOURCE_REVISION =", signing)
        self.assertNotIn('POWER_SOURCE_REVISION = "";', project)
        self.assertLess(
            signing.index("POWER_SOURCE_REVISION ="),
            signing.index('#include? "LocalSigning.xcconfig"'),
        )
        self.assertNotIn("CURRENT_PROJECT_VERSION =", project)
        self.assertNotIn("MARKETING_VERSION =", project)
        self.assertIn(
            f"POWER_APP_BUILD_NUMBER = {release_identity['build']}",
            release_configuration,
        )
        self.assertIn(
            "POWER_APP_DEVELOPER_DISPLAY_NAME = Power Benchmark Dev",
            release_configuration,
        )
        self.assertIn("POWER_BUILD_KIND = developer", project)
        self.assertIn("POWER_BUILD_KIND = certification", project)
        self.assertIn("POWER_BUILD_KIND = official", project)
        self.assertEqual(project.count("POWER_OFFICIAL"), 1)
        self.assertIn('buildConfiguration = "Official"', official_scheme)
        self.assertIn("case developer", identity)
        self.assertIn("case certification", identity)
        self.assertIn("case official", identity)
        self.assertIn("declaredKind == compiledKind", identity)
        self.assertIn("measurementLockReason", identity)
        self.assertIn("App source", (
            APP_ROOT / "PowerBenchmarkApp" / "PowerTestView.swift"
        ).read_text(encoding="utf-8"))
        self.assertIn(
            "PowerAppBuildIdentity.officialReleaseAvailable",
            model,
        )

        generated = subprocess.run(
            [
                "python3",
                "scripts/generate_power_app_release_identity.py",
                "--check",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(generated.returncode, 0, generated.stderr)

        ignored = subprocess.run(
            [
                "git",
                "check-ignore",
                "apps/ios/Configuration/LocalSigning.xcconfig",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(ignored.returncode, 0, ignored.stderr)

    def test_app_uses_separate_test_and_results_tabs(self) -> None:
        root_view = (
            APP_ROOT
            / "PowerBenchmarkApp"
            / "PowerRootView.swift"
        ).read_text(encoding="utf-8")
        self.assertIn('Label("Test", systemImage:', root_view)
        self.assertIn('Label("Results", systemImage:', root_view)
        self.assertIn("PowerTestView", root_view)
        self.assertIn("PowerResultsView", root_view)

    def test_results_view_connects_exact_bytes_to_github_submission(
        self,
    ) -> None:
        model = (
            APP_ROOT
            / "PowerBenchmarkApp"
            / "PowerAppModel.swift"
        ).read_text(encoding="utf-8")
        view = (
            APP_ROOT
            / "PowerBenchmarkApp"
            / "PowerResultsView.swift"
        ).read_text(encoding="utf-8")
        info_plist = (
            APP_ROOT
            / "PowerBenchmarkApp"
            / "Info.plist"
        ).read_text(encoding="utf-8")
        project = (APP_PROJECT / "project.pbxproj").read_text(
            encoding="utf-8"
        )

        self.assertIn("store.encodedEvidence", model)
        self.assertIn("PowerSubmissionPackage(", model)
        self.assertIn("client.publish(", model)
        self.assertIn("client.waitForAccessToken", model)
        self.assertIn("model.submitSelectedResult()", view)
        self.assertNotIn('Button("Submit to GitHub") {}', view)
        self.assertIn(".textSelection(.enabled)", view)
        self.assertIn('"Copy code"', view)
        self.assertIn('"Authorize on GitHub"', view)
        self.assertIn("<key>GitHubOAuthClientID</key>", info_plist)
        self.assertEqual(
            project.count("GITHUB_OAUTH_CLIENT_ID ="),
            4,
        )

    def test_app_links_new_local_modules_only(self) -> None:
        project = (APP_PROJECT / "project.pbxproj").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            'XCLocalSwiftPackageReference "../PowerRunnerKit"',
            project,
        )
        self.assertIn(
            'XCLocalSwiftPackageReference "../PowerAppKit"',
            project,
        )
        self.assertNotIn("../ios-app", project)
        self.assertNotIn("power-1.1", project.lower())

    def test_xcode_and_package_dependency_pins_match(self) -> None:
        runner = load_json(RUNNER_ROOT / "Package.resolved")
        app_kit = load_json(APP_KIT_ROOT / "Package.resolved")
        xcode = load_json(
            APP_PROJECT
            / "project.xcworkspace"
            / "xcshareddata"
            / "swiftpm"
            / "Package.resolved"
        )
        self.assertEqual(runner["pins"], app_kit["pins"])
        self.assertEqual(runner["pins"], xcode["pins"])

    def test_github_submission_never_synchronizes_default_fork_branch(
        self,
    ) -> None:
        source = (
            APP_KIT_ROOT
            / "Sources"
            / "PowerGitHubSubmission"
            / "GitHubSubmissionClient.swift"
        ).read_text(encoding="utf-8")
        self.assertNotIn("merge-upstream", source)
        self.assertIn("upstreamReference.object.sha", source)
        self.assertIn('"parents": [upstreamReference.object.sha]', source)


if __name__ == "__main__":
    unittest.main()
