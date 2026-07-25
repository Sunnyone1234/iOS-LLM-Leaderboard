from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

from scripts import triage_power2_submission_pr as triage
from scripts.review_power2_app_release_result import (
    review_result as review_app_release_result,
)
from scripts.lib.power2 import json_schema
from scripts.lib.power2.engine import (
    Power2ValidationError,
    ROOT,
    load_candidate_app_release_review_context,
    load_candidate_certification_review_context,
    load_candidate_context,
    load_product_context,
    validate_package,
)
from scripts.lib.power2.package import create_package
from scripts.lib.power2.ranking import build_dataset


EVALUATED_AT = "2026-07-23T12:00:00Z"
VALIDATOR_SOURCE_REVISION = "a" * 40
APP_SOURCE_REVISION = "b" * 40
SUBMISSION_ID = "44444444-4444-4444-8444-444444444444"
RESULT_ID = "55555555-5555-4555-8555-555555555555"
RUNNER_CERTIFICATE_ID = "power2-test-fixture-certificate"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


class Power2EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.candidate_context = load_candidate_context()
        cls.trusted_context = replace(
            cls.candidate_context,
            public_intake_open=True,
            runner_certificate={
                "certificateID": RUNNER_CERTIFICATE_ID,
                "state": "active",
                "programManifestSHA256": cls.candidate_context.program_reference[
                    "sha256"
                ],
                "targetManifestSHA256": cls.candidate_context.target_reference[
                    "sha256"
                ],
            },
            app_release={
                "state": "supported",
                "version": "2.0-test-fixture",
                "build": "1",
                "sourceRevision": APP_SOURCE_REVISION,
                "supportedRunnerCertificateIDs": [
                    RUNNER_CERTIFICATE_ID
                ],
            },
        )

    def test_public_loader_rejects_an_incomplete_active_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pointer = Path(directory) / "current.json"
            pointer.write_text(
                json.dumps(
                    {
                        "schemaVersion": "power-stack-pointer-1.0.0",
                        "status": "active",
                        "publicIntakeOpen": False,
                        "appRelease": None,
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ValueError,
                "active Power pointer is incomplete",
            ):
                load_product_context(pointer)

    def make_result(self) -> dict:
        context = self.trusted_context
        model_manifest, model_digest = next(
            iter(context.model_entries.values())
        )
        workload, workload_digest = context.workloads[
            "power.text.short-interaction"
        ]
        attempts = []
        for index in range(6):
            token_events = []
            for token_index in range(24):
                received = (
                    100
                    if token_index == 0
                    else 110 + round(790 * (token_index - 1) / 22)
                )
                if token_index == 0:
                    decoded_at = 105
                    decoded_prefix = " "
                    is_special = False
                    is_renderable = False
                elif token_index == 1:
                    decoded_at = 120
                    decoded_prefix = "The"
                    is_special = False
                    is_renderable = True
                else:
                    decoded_at = None
                    decoded_prefix = None
                    is_special = None
                    is_renderable = None
                token_events.append(
                    {
                        "index": token_index,
                        "tokenID": token_index + 1,
                        "receivedNanoseconds": received,
                        "decodedAtNanoseconds": decoded_at,
                        "decodedPrefix": decoded_prefix,
                        "isSpecial": is_special,
                        "isRenderable": is_renderable,
                    }
                )
            attempts.append(
                {
                    "index": index,
                    "phase": "warmup" if index == 0 else "measured",
                    "outcome": "succeeded",
                    "startedAt": f"2026-07-23T12:00:0{index}Z",
                    "endedAt": f"2026-07-23T12:00:1{index}Z",
                    "monotonic": {
                        "clock": "continuous-clock",
                        "requestAcceptedNanoseconds": 0,
                        "firstTokenNanoseconds": 100,
                        "firstRenderableNanoseconds": 120,
                        "completedNanoseconds": 1_000,
                        "promptEvaluationNanoseconds": 100,
                        "decodeNanoseconds": 800,
                    },
                    "tokenCounts": {"input": 20, "output": 24},
                    "tokenEvents": token_events,
                    "generatedText": (
                        "The note is stored locally and safely. "
                        "Synchronization resumes when connectivity returns."
                    ),
                    "memory": {
                        "peakPhysicalFootprintBytes": 500_000_000,
                        "samples": [
                            {
                                "elapsedNanoseconds": 0,
                                "physicalFootprintBytes": 450_000_000,
                            },
                            {
                                "elapsedNanoseconds": 500,
                                "physicalFootprintBytes": 500_000_000,
                            },
                        ],
                    },
                    "thermal": {
                        "start": "nominal",
                        "end": "nominal",
                        "transitions": [],
                    },
                    "failure": None,
                }
            )
        return {
            "schemaVersion": "power-evidence-envelope-1.0.0-draft.1",
            "resultID": RESULT_ID,
            "createdAt": "2026-07-23T11:59:00Z",
            "productID": "power",
            "program": {
                "id": context.program_reference["id"],
                "version": context.program_reference["version"],
                "manifestSHA256": context.program_reference["sha256"],
            },
            "target": {
                "id": context.target_reference["id"],
                "version": context.target_reference["version"],
                "manifestSHA256": context.target_reference["sha256"],
            },
            "runnerCertificateID": RUNNER_CERTIFICATE_ID,
            "appRelease": {
                "version": "2.0-test-fixture",
                "build": "1",
                "sourceRevision": APP_SOURCE_REVISION,
                "embeddedMeasurementStackSHA256": (
                    context.measurement_stack_sha256
                ),
            },
            "model": {
                "registryEntryID": model_manifest["registryEntryID"],
                "registryEntrySHA256": model_digest,
                "artifactID": model_manifest["artifactID"],
                "artifactRevision": model_manifest["artifactRevision"],
                "parameterCount": model_manifest["parameterCount"],
                "quantization": model_manifest["quantization"],
                "format": model_manifest["format"],
            },
            "runtime": {
                "name": "MLX Swift LM",
                "version": "test-fixture",
                "resolvedRevision": "c" * 40,
                "backend": "MLX/Metal",
                "configuration": {"fixture": True},
            },
            "device": {
                "machineIdentifier": "iPhone-test-fixture",
                "osVersion": "test-fixture",
                "osBuild": "test-fixture",
            },
            "environment": {
                "batteryLevelAtStart": 0.8,
                "batteryStateAtStart": "unplugged",
                "lowPowerModeAtStart": False,
                "thermalStateAtStart": "nominal",
                "thermalStateAtEnd": "nominal",
                "thermalAssistance": "none",
            },
            "artifacts": [],
            "payload": {
                "schemaVersion": (
                    "power-text-generation-payload-1.0.0-draft.2"
                ),
                "workload": {
                    "id": workload["workloadID"],
                    "version": workload["workloadVersion"],
                    "sha256": workload_digest,
                },
                "measurementMode": workload["measurementMode"],
                "inferenceConfiguration": workload["generation"],
                "attempts": attempts,
            },
        }

    def make_submission(self, result_bytes: bytes) -> dict:
        model_manifest, _ = next(
            iter(self.trusted_context.model_entries.values())
        )
        return {
            "schemaVersion": "power-submission-1.0.0-draft.1",
            "submissionID": SUBMISSION_ID,
            "createdAt": "2026-07-23T11:59:30Z",
            "contributor": {
                "githubLogin": "power-fixture-user",
                "conflictOfInterest": "none",
            },
            "sourceResult": {
                "path": "result.json",
                "sha256": sha256_bytes(result_bytes),
                "schemaVersion": (
                    "power-evidence-envelope-1.0.0-draft.1"
                ),
            },
            "declarations": {
                "physicalDevice": True,
                "publicMetadataReviewed": True,
                "rawEvidenceUnmodified": True,
                "containsNoPersonalData": True,
                "licenseAccepted": "CC-BY-4.0",
                "rankingNotGuaranteed": True,
            },
            "environmentNotes": (
                "Clearly labeled synthetic unit-test fixture; not evidence "
                f"for {model_manifest['displayName']}."
            ),
        }

    def write_package(
        self,
        parent: Path,
        result: dict,
        *,
        submission_override: dict | None = None,
    ) -> Path:
        package = parent / SUBMISSION_ID
        package.mkdir()
        result_bytes = (
            json.dumps(result, indent=2, sort_keys=True) + "\n"
        ).encode()
        submission = submission_override or self.make_submission(result_bytes)
        (package / "result.json").write_bytes(result_bytes)
        (package / "submission.json").write_text(
            json.dumps(submission, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return package

    def validate(self, package: Path, *, context=None) -> dict:
        return validate_package(
            package,
            context=context or self.trusted_context,
            evaluated_at=EVALUATED_AT,
            validator_source_revision=VALIDATOR_SOURCE_REVISION,
            pr_author="Power-Fixture-User",
        )

    def test_valid_new_package_is_deterministically_auto_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = self.write_package(Path(directory), self.make_result())
            first = self.validate(package)
            second = self.validate(package)

        self.assertEqual(first, second)
        self.assertEqual(first["classification"], "auto-accept")
        self.assertEqual(first["reasonCodes"], [])
        self.assertEqual(
            first["checks"]["behaviorConformance"]["status"], "pass"
        )
        self.assertEqual(
            first["checks"]["recommendationEligibility"]["status"],
            "pass",
        )
        self.assertTrue(
            all(
                check["status"] == "pass"
                for check in first["checks"]["metricEligibility"].values()
                if check["reasonCodes"]
                != ["metric-not-defined-for-workload"]
            )
        )

    def test_submission_uuid_case_does_not_change_identity(self) -> None:
        result = self.make_result()
        result_bytes = (
            json.dumps(result, indent=2, sort_keys=True) + "\n"
        ).encode()
        submission = self.make_submission(result_bytes)
        submission["submissionID"] = SUBMISSION_ID.upper()

        with tempfile.TemporaryDirectory() as directory:
            package = self.write_package(
                Path(directory),
                result,
                submission_override=submission,
            )
            report = self.validate(package)

        self.assertEqual(report["classification"], "auto-accept")
        self.assertNotIn(
            "submission-directory-identity-mismatch",
            report["reasonCodes"],
        )

    def test_failed_oom_and_cancelled_attempts_remain_accepted_evidence(self) -> None:
        result = self.make_result()
        outcomes = ["failed", "oom", "cancelled", "not-run", "failed"]
        for attempt, outcome in zip(
            result["payload"]["attempts"][1:], outcomes
        ):
            attempt["outcome"] = outcome
            attempt["monotonic"] = {
                "clock": "continuous-clock",
                "requestAcceptedNanoseconds": attempt["monotonic"][
                    "requestAcceptedNanoseconds"
                ],
            }
            attempt["tokenCounts"] = {"input": 0, "output": 0}
            attempt["tokenEvents"] = []
            attempt["generatedText"] = ""
            attempt["memory"] = {
                "peakPhysicalFootprintBytes": None,
                "samples": [],
            }
            attempt["failure"] = {
                "code": outcome,
                "message": f"synthetic {outcome} fixture",
            }

        with tempfile.TemporaryDirectory() as directory:
            package = self.write_package(Path(directory), result)
            report = self.validate(package)

        self.assertEqual(report["classification"], "auto-accept")
        self.assertEqual(
            report["checks"]["contractConformance"]["status"], "pass"
        )
        self.assertTrue(
            all(
                check["status"] == "not-applicable"
                for check in report["checks"]["metricEligibility"].values()
            )
        )
        self.assertEqual(
            report["checks"]["behaviorConformance"]["status"],
            "manual-review",
        )

    def test_behavior_is_separate_from_performance_eligibility(self) -> None:
        result = self.make_result()
        for attempt in result["payload"]["attempts"]:
            attempt["generatedText"] = (
                "When the device is offline, the note is automatically "
                "synced to the cloud. It is available when connectivity "
                "returns."
            )

        with tempfile.TemporaryDirectory() as directory:
            package = self.write_package(Path(directory), result)
            report = self.validate(package)

        self.assertEqual(report["classification"], "auto-accept")
        self.assertEqual(
            report["checks"]["behaviorConformance"],
            {
                "status": "manual-review",
                "reasonCodes": ["behavior-not-verified"],
            },
        )
        self.assertEqual(
            report["checks"]["recommendationEligibility"],
            {
                "status": "manual-review",
                "reasonCodes": ["behavior-not-verified"],
            },
        )
        self.assertTrue(
            all(
                check["status"] == "pass"
                for check in report["checks"]["metricEligibility"].values()
                if check["reasonCodes"]
                != ["metric-not-defined-for-workload"]
            )
        )

    def test_direct_behavior_contradiction_blocks_recommendation_only(
        self,
    ) -> None:
        result = self.make_result()
        for attempt in result["payload"]["attempts"]:
            attempt["generatedText"] = (
                "The note is not stored on this device. "
                "It will not sync when connectivity returns."
            )

        with tempfile.TemporaryDirectory() as directory:
            package = self.write_package(Path(directory), result)
            report = self.validate(package)

        self.assertEqual(report["classification"], "auto-accept")
        self.assertEqual(
            report["checks"]["behaviorConformance"]["status"], "fail"
        )
        self.assertEqual(
            report["checks"]["recommendationEligibility"]["status"],
            "fail",
        )

    def test_workload_without_behavior_contract_is_not_applicable(
        self,
    ) -> None:
        result = self.make_result()
        workload, digest = self.trusted_context.workloads[
            "power.text.sustained-generation"
        ]
        result["payload"]["workload"] = {
            "id": workload["workloadID"],
            "version": workload["workloadVersion"],
            "sha256": digest,
        }
        result["payload"]["measurementMode"] = workload["measurementMode"]
        result["payload"]["inferenceConfiguration"] = workload["generation"]

        with tempfile.TemporaryDirectory() as directory:
            package = self.write_package(Path(directory), result)
            report = self.validate(package)

        self.assertEqual(
            report["checks"]["behaviorConformance"]["status"],
            "not-applicable",
        )
        self.assertEqual(
            report["checks"]["recommendationEligibility"]["status"],
            "not-applicable",
        )

    def test_changed_result_bytes_fail_digest_integrity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = self.write_package(Path(directory), self.make_result())
            result = json.loads((package / "result.json").read_text())
            result["device"]["osBuild"] = "tampered"
            (package / "result.json").write_text(
                json.dumps(result, indent=2, sort_keys=True) + "\n"
            )
            report = self.validate(package)

        self.assertEqual(report["classification"], "reject")
        self.assertIn("result-digest-mismatch", report["reasonCodes"])

    def test_raw_summaries_must_recalculate_from_retained_samples(self) -> None:
        result = self.make_result()
        attempt = result["payload"]["attempts"][1]
        attempt["monotonic"]["firstRenderableNanoseconds"] = 121
        attempt["memory"]["peakPhysicalFootprintBytes"] = 499_999_999

        with tempfile.TemporaryDirectory() as directory:
            package = self.write_package(Path(directory), result)
            report = self.validate(package)

        self.assertEqual(report["classification"], "reject")
        self.assertIn("raw-attempt-inconsistent", report["reasonCodes"])
        self.assertTrue(
            any(
                "cannot be reproduced" in diagnostic
                for diagnostic in report["diagnostics"]
            )
        )

    def test_renderability_probing_stops_after_first_renderable_event(
        self,
    ) -> None:
        result = self.make_result()
        event = result["payload"]["attempts"][1]["tokenEvents"][2]
        event.update(
            {
                "decodedAtNanoseconds": 130,
                "decodedPrefix": "later",
                "isSpecial": False,
                "isRenderable": True,
            }
        )

        with tempfile.TemporaryDirectory() as directory:
            package = self.write_package(Path(directory), result)
            report = self.validate(package)

        self.assertEqual(report["classification"], "reject")
        self.assertIn("raw-attempt-inconsistent", report["reasonCodes"])
        self.assertTrue(
            any(
                "after the first renderable event" in diagnostic
                for diagnostic in report["diagnostics"]
            )
        )

    def test_power_1_package_is_rejected_without_translation(self) -> None:
        result = {"schemaVersion": "suite-b-power-result-1.1.0"}
        result_bytes = (json.dumps(result) + "\n").encode()
        submission = {
            "schemaVersion": "suite-b-power-submission-1.1.0",
            "submissionID": SUBMISSION_ID,
            "sourceResult": {
                "path": "result.json",
                "sha256": sha256_bytes(result_bytes),
                "schemaVersion": "suite-b-power-result-1.1.0",
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            package = self.write_package(
                Path(directory),
                result,
                submission_override=submission,
            )
            report = self.validate(package)

        self.assertEqual(report["classification"], "reject")
        self.assertIn("unsupported-major-version", report["reasonCodes"])
        self.assertNotIn("translated", " ".join(report["diagnostics"]).lower())

    def test_real_candidate_stays_closed_until_app_release_and_intake(
        self,
    ) -> None:
        result = self.make_result()
        result["runnerCertificateID"] = (
            self.candidate_context.runner_certificate["certificateID"]
        )
        result["runtime"] = self.candidate_context.runner_certificate[
            "runtime"
        ]
        with tempfile.TemporaryDirectory() as directory:
            package = self.write_package(Path(directory), result)
            report = self.validate(
                package, context=self.candidate_context
            )

        self.assertEqual(report["classification"], "reject")
        self.assertEqual(
            report["checks"]["runnerCertificate"]["status"],
            "pass",
        )
        self.assertIn("app-release-not-supported", report["reasonCodes"])
        self.assertIn("public-intake-closed", report["reasonCodes"])

    def test_certification_review_closes_after_certificate_issuance(
        self,
    ) -> None:
        with self.assertRaises(Power2ValidationError):
            load_candidate_certification_review_context()

    def test_app_release_review_closes_after_activation(
        self,
    ) -> None:
        with self.assertRaises(Power2ValidationError):
            load_candidate_app_release_review_context()

    def test_ranking_preview_excludes_superseded_retained_package(
        self,
    ) -> None:
        retained_submission_id = "34A91509-406A-4948-95A3-54B82E7760A9"
        submissions_root = (
            ROOT
            / "submissions"
            / "power"
            / "text-generation-performance"
            / "2.0.0"
            / "draft"
        )
        with tempfile.TemporaryDirectory() as directory:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "power"),
                    "preview",
                    "--submissions-root",
                    str(submissions_root),
                    "--output",
                    directory,
                    "--generated-at",
                    EVALUATED_AT,
                    "--validator-source-revision",
                    VALIDATOR_SOURCE_REVISION,
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                completed.returncode,
                0,
                completed.stderr or completed.stdout,
            )
            dataset = json.loads(
                (Path(directory) / "ranking.json").read_text()
            )

        retained = next(
            contribution
            for contribution in dataset["excluded"]
            if contribution["submissionID"] == retained_submission_id
        )
        self.assertEqual(retained["classification"], "reject")
        self.assertIn(
            "app-release-not-supported",
            retained["reasonCodes"],
        )
        self.assertIn(
            "runner-certificate-not-active",
            retained["reasonCodes"],
        )

    def test_power2_command_line_entries_run_directly(self) -> None:
        for relative_path in (
            "scripts/issue_power_next_runner_certificate.py",
            "scripts/review_power2_app_release_result.py",
            "scripts/review_power2_certification_result.py",
            "scripts/stage_power_next_app_release.py",
            "scripts/triage_power2_submission_pr.py",
        ):
            with self.subTest(script=relative_path):
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / relative_path),
                        "--help",
                    ],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(
                    completed.returncode,
                    0,
                    completed.stderr,
                )

    def test_registered_model_snapshot_cannot_be_changed(self) -> None:
        result = self.make_result()
        result["model"]["parameterCount"] += 1
        with tempfile.TemporaryDirectory() as directory:
            package = self.write_package(Path(directory), result)
            report = self.validate(package)

        self.assertEqual(report["classification"], "reject")
        self.assertIn(
            "model-artifact-identity-mismatch", report["reasonCodes"]
        )

    def test_json_schema_rejects_unknown_envelope_fields(self) -> None:
        result = self.make_result()
        result["legacyCompatibility"] = True
        errors = json_schema.validate(
            result,
            self.trusted_context.schema_paths["evidence"],
            ROOT,
        )

        self.assertTrue(
            any("unexpected property 'legacyCompatibility'" in error for error in errors)
        )

    def test_pr_author_must_match_declared_contributor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = self.write_package(Path(directory), self.make_result())
            report = validate_package(
                package,
                context=self.trusted_context,
                evaluated_at=EVALUATED_AT,
                validator_source_revision=VALIDATOR_SOURCE_REVISION,
                pr_author="different-user",
            )

        self.assertEqual(report["classification"], "reject")
        self.assertIn("contributor-identity-mismatch", report["reasonCodes"])

    def test_package_generator_preserves_raw_result_bytes(self) -> None:
        result_bytes = (
            json.dumps(self.make_result(), indent=2, sort_keys=True) + "\n"
        ).encode()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            source.write_bytes(result_bytes)
            package = create_package(
                source,
                root / "packages",
                github_login="Power-Fixture-User",
                declarations_accepted=True,
                submission_id=SUBMISSION_ID,
                created_at="2026-07-23T12:00:00Z",
                context=self.trusted_context,
            )

            self.assertEqual(
                (package / "result.json").read_bytes(),
                result_bytes,
            )
            declaration = json.loads(
                (package / "submission.json").read_text()
            )
            self.assertEqual(
                declaration["sourceResult"]["sha256"],
                sha256_bytes(result_bytes),
            )

    def _triage_package(
        self,
        package: Path,
        *,
        changes: list[tuple[str, str]] | None = None,
    ) -> dict:
        prefix = triage.INTAKE.as_posix()
        changes = changes or [
            ("A", f"{prefix}/{SUBMISSION_ID}/result.json"),
            ("A", f"{prefix}/{SUBMISSION_ID}/submission.json"),
        ]

        def materialize(
            _head: str,
            _submission_id: str,
            root: Path,
        ) -> Path:
            target = root / SUBMISSION_ID
            target.mkdir()
            for source in package.iterdir():
                (target / source.name).write_bytes(source.read_bytes())
            return target

        with mock.patch.object(
            triage,
            "_changes",
            return_value=changes,
        ), mock.patch.object(
            triage,
            "_materialize_package",
            side_effect=materialize,
        ), mock.patch.object(
            triage,
            "_accepted_result_digests",
            return_value=set(),
        ):
            return triage.classify(
                "base",
                "head",
                "Power-Fixture-User",
                evaluated_at=EVALUATED_AT,
                validator_source_revision=VALIDATOR_SOURCE_REVISION,
                context=self.trusted_context,
            )

    def test_power2_triage_accepts_only_result_packages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = self.write_package(
                Path(directory),
                self.make_result(),
            )
            report = self._triage_package(package)

        self.assertEqual(report["classification"], "auto_accept")
        self.assertEqual(report["packageCount"], 1)

    def test_power2_triage_does_not_block_normal_code_prs(self) -> None:
        with mock.patch.object(
            triage,
            "_changes",
            return_value=[("M", "README.md")],
        ):
            report = triage.classify(
                "base",
                "head",
                "Power-Fixture-User",
                evaluated_at=EVALUATED_AT,
                validator_source_revision=VALIDATOR_SOURCE_REVISION,
                context=self.trusted_context,
            )

        self.assertEqual(report["classification"], "not_applicable")

    def test_power2_triage_rejects_mixed_scope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = self.write_package(
                Path(directory),
                self.make_result(),
            )
            prefix = triage.INTAKE.as_posix()
            report = self._triage_package(
                package,
                changes=[
                    ("A", f"{prefix}/{SUBMISSION_ID}/result.json"),
                    ("A", f"{prefix}/{SUBMISSION_ID}/submission.json"),
                    ("M", ".github/workflows/power2-intake.yml"),
                ],
            )

        self.assertEqual(report["classification"], "rejected")
        self.assertIn(
            "pull-request-scope-invalid",
            report["reasonCodes"],
        )

    def _write_rankable_package(
        self,
        root: Path,
        *,
        submission_id: str,
        result_id: str,
        contributor: str,
    ) -> Path:
        result = self.make_result()
        result["resultID"] = result_id
        source = root / f"{submission_id}.json"
        source.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return create_package(
            source,
            root / "packages",
            github_login=contributor,
            declarations_accepted=True,
            submission_id=submission_id,
            created_at=EVALUATED_AT,
            context=self.trusted_context,
        )

    def test_power2_ranking_counts_distinct_contributors(self) -> None:
        identities = [
            (
                "10000000-0000-4000-8000-000000000001",
                "20000000-0000-4000-8000-000000000001",
                "Contributor-One",
            ),
            (
                "10000000-0000-4000-8000-000000000002",
                "20000000-0000-4000-8000-000000000002",
                "Contributor-Two",
            ),
            (
                "10000000-0000-4000-8000-000000000003",
                "20000000-0000-4000-8000-000000000003",
                "Contributor-Three",
            ),
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packages = root / "packages"
            for index, (
                submission_id,
                result_id,
                contributor,
            ) in enumerate(identities, start=1):
                self._write_rankable_package(
                    root,
                    submission_id=submission_id,
                    result_id=result_id,
                    contributor=contributor,
                )
                dataset = build_dataset(
                    packages,
                    context=self.trusted_context,
                    generated_at=EVALUATED_AT,
                    validator_source_revision=VALIDATOR_SOURCE_REVISION,
                )
                self.assertEqual(
                    dataset["acceptedContributionCount"],
                    index,
                )
                self.assertEqual(len(dataset["views"]), 1)
                self.assertEqual(
                    dataset["views"][0]["evidenceState"],
                    {
                        1: "accepted",
                        2: "reproduced",
                        3: "contributor-weighted",
                    }[index],
                )


if __name__ == "__main__":
    unittest.main()
