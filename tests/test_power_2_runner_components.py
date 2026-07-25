from __future__ import annotations

import hashlib
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = (
    ROOT / "apps/PowerRunnerKit/candidate-component-manifest.json"
)
NEXT_PATH = ROOT / "products/power/next.json"
IDENTITY_PATH = ROOT / "apps/ios/Power2ProductIdentity.generated.swift"
ACTIVE_RUNNER_CERTIFICATE_PATH = (
    ROOT
    / "products/power/runner-certificates"
    / "power2-runner-ac490be49347.json"
)


class Power2RunnerComponentTests(unittest.TestCase):
    def test_component_manifest_is_generated_from_exact_swift_sources(
        self,
    ) -> None:
        dependency_identity = subprocess.run(
            [
                "python3",
                "scripts/generate_power_mlx_dependency_identity.py",
                "--check",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            dependency_identity.returncode,
            0,
            dependency_identity.stderr,
        )
        completed = subprocess.run(
            [
                "python3",
                "scripts/generate_power_runner_component_manifest.py",
                "--check",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

        manifest = json.loads(MANIFEST_PATH.read_text())
        self.assertEqual(
            manifest["schemaVersion"],
            "power-runner-component-manifest-1.0.0",
        )
        self.assertNotIn("status", manifest)
        self.assertNotIn("completeForCertification", manifest)
        self.assertNotIn("certificationBlockers", manifest)
        self.assertIsInstance(
            manifest["components"]["runtimeAdapter"],
            dict,
        )
        for name in (
            "evidenceEnvelope",
            "runnerCore",
            "programModule",
            "targetAdapter",
            "runtimeAdapter",
        ):
            component = manifest["components"][name]
            self.assertTrue(component["files"])
            files = component["files"]
            canonical = json.dumps(
                files,
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
            self.assertEqual(
                component["sha256"],
                hashlib.sha256(canonical).hexdigest(),
            )
            for reference in files:
                path = ROOT / reference["path"]
                self.assertEqual(
                    reference["sha256"],
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                )
        dependency_lock = manifest["resolvedDependencies"]
        self.assertEqual(
            dependency_lock["sha256"],
            hashlib.sha256(
                (ROOT / dependency_lock["path"]).read_bytes()
            ).hexdigest(),
        )
        runtime_identity = manifest["runtimeIdentity"]
        self.assertEqual(
            runtime_identity["sha256"],
            hashlib.sha256(
                (ROOT / runtime_identity["path"]).read_bytes()
            ).hexdigest(),
        )

    def test_product_swift_identity_excludes_intake_lifecycle(self) -> None:
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

        candidate = json.loads(NEXT_PATH.read_text())
        swift = IDENTITY_PATH.read_text()
        self.assertFalse(candidate["publicIntakeOpen"])
        self.assertEqual(candidate["state"], "activated")
        self.assertIsInstance(candidate["appRelease"], dict)
        self.assertIn(candidate["measurementStack"]["sha256"], swift)
        self.assertIn(candidate["runnerComponents"]["sha256"], swift)
        self.assertNotIn("isReleaseCandidate", swift)
        self.assertNotIn("appReleaseAvailable", swift)
        self.assertNotIn("publicIntakeOpen", swift)
        self.assertNotIn("submissionRehearsalAvailable", swift)

    def test_next_release_is_generated_source_bound_and_fail_closed(
        self,
    ) -> None:
        completed = subprocess.run(
            [
                "python3",
                "scripts/generate_power_next_release.py",
                "--check",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

        candidate = json.loads(NEXT_PATH.read_text())
        active_runner = json.loads(
            ACTIVE_RUNNER_CERTIFICATE_PATH.read_text()
        )
        app_identity = json.loads(
            (
                ROOT
                / "apps"
                / "ios"
                / "Configuration"
                / "ReleaseIdentity.json"
            ).read_text()
        )
        self.assertEqual(active_runner["state"], "active")
        self.assertEqual(
            candidate["state"],
            "activated",
        )
        self.assertFalse(candidate["publicIntakeOpen"])
        self.assertEqual(
            candidate["runnerCertificate"]["path"],
            (
                "products/power/runner-certificates/"
                "power2-runner-ac490be49347.json"
            ),
        )
        self.assertIsInstance(candidate["appRelease"], dict)
        self.assertIsInstance(candidate["appReleaseCandidate"], dict)
        self.assertEqual(
            candidate["app"],
            {
                "version": app_identity["version"],
                "build": app_identity["build"],
            },
        )
        self.assertEqual(
            candidate["runnerComponents"]["path"],
            (
                "products/power/runner-certificates/evidence/"
                "83ecb818-e1f7-4118-80c9-1df9e6fbe8fe/"
                "runner-component-manifest.json"
            ),
        )
        frozen_runner = ROOT / candidate["runnerComponents"]["path"]
        self.assertEqual(
            candidate["runnerComponents"]["sha256"],
            hashlib.sha256(frozen_runner.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            candidate["runnerCertificationCandidateID"],
            "power2-certification-candidate-"
            + candidate["runnerComponents"]["sha256"][:12],
        )
        self.assertEqual(active_runner["state"], "active")
        self.assertEqual(
            active_runner["runnerComponents"],
            candidate["runnerComponents"],
        )
        app_candidate_path = (
            ROOT / candidate["appReleaseCandidate"]["path"]
        )
        app_candidate = json.loads(app_candidate_path.read_text())
        self.assertEqual(
            app_candidate["embeddedMeasurementStack"],
            candidate["measurementStack"],
        )
        self.assertEqual(
            app_candidate["supportedRunnerCertificateIDs"],
            [active_runner["certificateID"]],
        )
        self.assertEqual(
            app_candidate["verification"][
                "physicalDeviceEndToEndRehearsal"
            ],
            "pending",
        )
        superseded_reference = candidate[
            "supersededAppReleaseRehearsal"
        ]
        superseded_path = ROOT / superseded_reference["path"]
        self.assertEqual(
            superseded_reference["sha256"],
            hashlib.sha256(superseded_path.read_bytes()).hexdigest(),
        )
        superseded = json.loads(superseded_path.read_text())
        self.assertEqual(superseded["state"], "superseded")
        self.assertFalse(superseded["publishable"])
        self.assertFalse(superseded["rankingEligible"])
        self.assertEqual(
            superseded["supersededBy"],
            candidate["appReleaseCandidate"],
        )
        for key in ("appReleaseCandidate", "appComponents", "result", "review"):
            reference = superseded[key]
            path = ROOT / reference["path"]
            self.assertEqual(
                reference["sha256"],
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )


if __name__ == "__main__":
    unittest.main()
