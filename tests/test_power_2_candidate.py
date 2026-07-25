from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import repoctl
from scripts.lib.power2 import activation, next_activation


ROOT = Path(__file__).resolve().parents[1]
PROGRAM_ROOT = (
    ROOT
    / "products"
    / "power"
    / "programs"
    / "text-generation-performance"
    / "versions"
    / "2.0.0-draft.2"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Power2CandidateTests(unittest.TestCase):
    def staged_next_release(self) -> dict:
        completed = load_json(
            ROOT / "products" / "power" / "next.json"
        )
        staged = {
            **completed,
            "state": "app-release-rehearsal-required",
            "baseRelease": {
                "path": "products/power/current.json",
                "sha256": repoctl._sha256(
                    ROOT / "products/power/current.json"
                ),
            },
            "appRelease": None,
        }
        staged.pop("activatedAt", None)
        staged.pop("activationEvidence", None)
        return staged

    def staged_next_loader(self, staged: dict):
        def loader(path: Path, label: str) -> dict:
            del label
            if path == next_activation.NEXT_PATH:
                return staged
            return load_json(path)

        return loader

    def test_active_stack_is_complete(self) -> None:
        summary = repoctl.verify_power_candidate()

        self.assertEqual(summary["status"], "valid-active")
        self.assertEqual(
            summary["program"],
            "text-generation-performance@2.0.0-draft.2",
        )
        self.assertEqual(
            summary["target"],
            "apple-iphone-physical@1.0.0-draft.1",
        )
        self.assertEqual(summary["pinnedProgramAssets"], 10)
        self.assertEqual(summary["schemas"], 5)
        self.assertEqual(summary["registeredModels"], 4)
        self.assertEqual(summary["runnerComponents"], 5)
        self.assertTrue(summary["runtimeAdapterImplemented"])
        self.assertEqual(summary["appComponents"], 6)
        self.assertTrue(summary["appShellImplemented"])
        self.assertTrue(summary["runnerCertified"])
        self.assertTrue(summary["appReleased"])
        self.assertTrue(summary["publicIntakeOpen"])
        self.assertEqual(
            summary["appRelease"],
            "power-app-2.0.0-build.5-a9b1c359107c",
        )
        self.assertEqual(
            summary["nextReleaseState"],
            "activated",
        )
        self.assertEqual(
            summary["nextRunnerCertificate"],
            "power2-runner-ac490be49347",
        )
        next_release = load_json(
            ROOT / "products" / "power" / "next.json"
        )
        next_app_candidate = load_json(
            ROOT / next_release["appReleaseCandidate"]["path"]
        )
        self.assertEqual(
            summary["nextAppReleaseCandidate"],
            next_app_candidate["releaseID"],
        )

    def test_active_pointer_preserves_the_certified_runner(self) -> None:
        registry = load_json(ROOT / "products" / "power" / "registry.json")
        candidate = load_json(ROOT / registry["candidateStack"])
        current = load_json(ROOT / registry["currentStack"])
        measurement_stack = load_json(
            ROOT / current["measurementStack"]["path"]
        )

        self.assertEqual(
            registry["currentStack"], "products/power/current.json"
        )
        self.assertTrue(registry["publicIntakeOpen"])
        self.assertFalse(candidate["publicIntakeOpen"])
        self.assertEqual(
            measurement_stack["runnerCertificate"],
            current["runnerCertificate"],
        )
        runner_certificate = load_json(
            ROOT / current["runnerCertificate"]["path"]
        )
        self.assertEqual(runner_certificate["state"], "active")
        self.assertEqual(
            runner_certificate["certificateID"],
            "power2-runner-"
            + current["runnerComponents"]["sha256"][:12],
        )
        self.assertEqual(
            runner_certificate["verification"][
                "physicalDeviceSmokeRun"
            ],
            "pass",
        )
        self.assertEqual(
            runner_certificate["verification"]["rawResultReview"],
            "pass",
        )
        evidence = runner_certificate["certificationEvidence"]
        for key in ("result", "review", "measurementStack"):
            reference = evidence[key]
            self.assertEqual(
                reference["sha256"],
                repoctl._sha256(ROOT / reference["path"]),
            )
        self.assertIsNone(candidate["appRelease"])
        self.assertIsNotNone(candidate["runnerCandidate"])
        self.assertIsNotNone(candidate["appCandidate"])
        self.assertTrue(
            (ROOT / "products" / "power" / "current.json").exists()
        )

    def test_supported_app_release_retains_exact_activation_evidence(
        self,
    ) -> None:
        current = load_json(ROOT / "products/power/current.json")
        app_release = load_json(
            ROOT / current["appRelease"]["path"]
        )

        self.assertEqual(app_release["state"], "supported")
        self.assertEqual(app_release["build"], "5")
        self.assertEqual(
            app_release["sourceRevision"],
            "a9b1c359107c0806b023c61f190b4ce49c61ee1cf7da2cc59bafea8435493c8f",
        )
        self.assertEqual(
            app_release["verification"]["genericIOSReleaseBuild"],
            "pass",
        )
        self.assertEqual(
            app_release["verification"][
                "physicalDeviceEndToEndRehearsal"
            ],
            "pass",
        )
        self.assertEqual(
            current["activationEvidence"],
            app_release["releaseEvidence"],
        )
        result = load_json(
            ROOT / app_release["releaseEvidence"]["result"]["path"]
        )
        review = load_json(
            ROOT / app_release["releaseEvidence"]["review"]["path"]
        )
        self.assertEqual(
            result["resultID"],
            "F38B67EC-5347-4F35-B4CD-895A0595E9B1",
        )
        self.assertEqual(result["appRelease"]["build"], "5")
        self.assertEqual(review["status"], "pass")
        self.assertEqual(review["classification"], "auto-accept")
        self.assertFalse(review["publishable"])
        self.assertFalse(review["rankingEligible"])

    def test_activation_is_one_time(self) -> None:
        current = load_json(ROOT / "products/power/current.json")
        result = ROOT / current["activationEvidence"]["result"]["path"]
        with self.assertRaisesRegex(
            activation.Power2ActivationError,
            "Power current pointer already exists; activation is one-time",
        ):
            activation.render_activation(
                result,
                reviewed_at="2026-07-24T00:00:00Z",
                activated_at="2026-07-24T00:01:00Z",
                validator_source_revision=(
                    "4407a3776636e6c1a3a5892f78a3f4a841cecac7"
                ),
            )

    def test_next_activation_rejects_superseded_rehearsal(self) -> None:
        superseded = load_json(
            ROOT
            / "products"
            / "power"
            / "app-releases"
            / "evidence"
            / "656cf217-8ef5-4ccd-bb18-cb34062d4b7c"
            / "record.json"
        )
        result = ROOT / superseded["result"]["path"]
        staged = self.staged_next_release()
        with (
            mock.patch.object(
                next_activation,
                "_load",
                side_effect=self.staged_next_loader(staged),
            ),
            mock.patch.object(
                next_activation,
                "review_result",
                return_value={
                    "status": "reject",
                    "physicalDeviceEndToEndRehearsal": "fail",
                    "classification": "reject",
                    "publishable": False,
                    "rankingEligible": False,
                    "reasonCodes": ["superseded-app-release-rehearsal"],
                    "diagnostics": [],
                },
            ),
        ):
            with self.assertRaisesRegex(
                next_activation.Power2NextActivationError,
                "did not pass the closed App release review",
            ):
                next_activation.render_next_activation(
                    result,
                    reviewed_at="2026-07-25T15:00:00Z",
                    activated_at="2026-07-25T15:01:00Z",
                    validator_source_revision=(
                        "b70019ff2b807a204702e1b59e8a31362b767515"
                    ),
                )

    def test_next_activation_renders_one_atomic_upgrade_set(self) -> None:
        next_release = self.staged_next_release()
        candidate = load_json(
            ROOT / next_release["appReleaseCandidate"]["path"]
        )
        certificate = load_json(
            ROOT / next_release["runnerCertificate"]["path"]
        )
        result = {
            "resultID": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            "appRelease": {
                "version": candidate["version"],
                "build": candidate["build"],
                "sourceRevision": candidate["sourceRevision"],
                "embeddedMeasurementStackSHA256":
                    next_release["measurementStack"]["sha256"],
            },
            "runnerCertificateID": certificate["certificateID"],
        }
        with (
            tempfile.TemporaryDirectory() as directory,
            tempfile.TemporaryDirectory(dir=ROOT) as output_directory,
        ):
            result_path = Path(directory) / "synthetic-render-fixture.json"
            result_bytes = (
                json.dumps(result, indent=2, sort_keys=True) + "\n"
            ).encode()
            result_path.write_bytes(result_bytes)
            review = {
                "status": "pass",
                "physicalDeviceEndToEndRehearsal": "pass",
                "classification": "auto-accept",
                "publishable": False,
                "rankingEligible": False,
                "sourceResultSHA256":
                    hashlib.sha256(result_bytes).hexdigest(),
                "appRelease": result["appRelease"],
                "runnerCertificateID":
                    result["runnerCertificateID"],
            }
            with (
                mock.patch.object(
                    next_activation,
                    "_load",
                    side_effect=self.staged_next_loader(next_release),
                ),
                mock.patch.object(
                    next_activation,
                    "review_result",
                    return_value=review,
                ),
                mock.patch.object(
                    next_activation,
                    "APP_RELEASE_ROOT",
                    Path(output_directory),
                ),
                mock.patch.object(
                    next_activation,
                    "APP_EVIDENCE_ROOT",
                    Path(output_directory) / "evidence",
                ),
            ):
                rendered = next_activation.render_next_activation(
                    result_path,
                    reviewed_at="2026-07-25T15:00:00Z",
                    activated_at="2026-07-25T15:01:00Z",
                    validator_source_revision=(
                        "b70019ff2b807a204702e1b59e8a31362b767515"
                    ),
                )

        self.assertEqual(rendered.summary["status"], "ready")
        self.assertTrue(rendered.summary["publicIntakeOpen"])
        advanced_current = json.loads(
            rendered.files[
                ROOT / "products" / "power" / "current.json"
            ]
        )
        advanced_plan = json.loads(
            rendered.files[
                ROOT / "products" / "power" / "next.json"
            ]
        )
        self.assertEqual(advanced_plan["state"], "activated")
        self.assertEqual(
            advanced_plan["appRelease"],
            advanced_current["appRelease"],
        )
        self.assertEqual(
            advanced_plan["activationEvidence"],
            advanced_current["activationEvidence"],
        )
        self.assertNotEqual(
            advanced_plan["baseRelease"]["path"],
            "products/power/current.json",
        )

    def test_active_pointer_binds_every_release_reference(self) -> None:
        current = load_json(ROOT / "products/power/current.json")
        self.assertEqual(current["status"], "active")
        self.assertTrue(current["publicIntakeOpen"])
        for key in (
            "measurementStack",
            "runnerComponents",
            "runnerCertificate",
            "appRelease",
        ):
            reference = current[key]
            self.assertEqual(
                reference["sha256"],
                repoctl._sha256(ROOT / reference["path"]),
            )
        for reference in current["activationEvidence"].values():
            self.assertEqual(
                reference["sha256"],
                repoctl._sha256(ROOT / reference["path"]),
            )

    def test_active_candidate_json_has_no_power_1_dispatch(self) -> None:
        active_json = [
            ROOT / "products" / "power" / "registry.json",
            ROOT / "products" / "power" / "candidate.json",
            ROOT / "models" / "registry.json",
            ROOT
            / "models"
            / "cohorts"
            / "small-language-models"
            / "1.0.0-draft.1.json",
        ]
        active_json.extend(
            path
            for path in (ROOT / "products" / "power").rglob("*.json")
            if path not in active_json
        )
        active_json.extend(
            path
            for path in (ROOT / "models" / "artifacts").rglob("*.json")
            if path not in active_json
        )
        documents = [
            (str(path.relative_to(ROOT)), load_json(path))
            for path in active_json
        ]

        repoctl._reject_legacy_references(documents)

    def test_program_contract_keeps_metrics_separate(self) -> None:
        contract = load_json(PROGRAM_ROOT / "contract.json")
        metric_ids = {metric["id"] for metric in contract["metrics"]}

        self.assertFalse(contract["globalScoreDefined"])
        self.assertEqual(contract["attemptContract"]["warmupAttempts"], 1)
        self.assertEqual(contract["attemptContract"]["measuredAttempts"], 5)
        self.assertEqual(
            contract["attemptContract"]["preserveOutcomes"],
            ["succeeded", "failed", "cancelled", "oom", "not-run"],
        )
        self.assertIn("first_renderable_ms", metric_ids)
        self.assertIn("pipeline_ttft_ms", metric_ids)
        self.assertIn("decode_tokens_per_second", metric_ids)

    def test_payload_schema_fixes_attempt_order_and_outcomes(self) -> None:
        schema = load_json(
            PROGRAM_ROOT / "schemas" / "text-generation-payload.schema.json"
        )
        attempts = schema["properties"]["attempts"]
        positions = attempts["prefixItems"]

        self.assertEqual(attempts["minItems"], 6)
        self.assertEqual(attempts["maxItems"], 6)
        self.assertFalse(attempts["items"])
        self.assertEqual(
            [
                item["allOf"][1]["properties"]["index"]["const"]
                for item in positions
            ],
            list(range(6)),
        )
        self.assertEqual(
            [
                item["allOf"][1]["properties"]["phase"]["const"]
                for item in positions
            ],
            ["warmup", "measured", "measured", "measured", "measured", "measured"],
        )
        self.assertEqual(
            schema["$defs"]["attempt"]["properties"]["outcome"]["enum"],
            ["succeeded", "failed", "cancelled", "oom", "not-run"],
        )

    def test_evidence_binds_exact_release_and_model_identity(self) -> None:
        schema = load_json(
            PROGRAM_ROOT / "schemas" / "evidence-envelope.schema.json"
        )
        required = set(schema["required"])
        app_required = set(
            schema["properties"]["appRelease"]["required"]
        )
        model_required = set(schema["properties"]["model"]["required"])

        self.assertIn("runnerCertificateID", required)
        self.assertIn("appRelease", required)
        self.assertIn("model", required)
        self.assertEqual(
            app_required,
            {
                "version",
                "build",
                "sourceRevision",
                "embeddedMeasurementStackSHA256",
            },
        )
        self.assertTrue(
            {
                "registryEntrySHA256",
                "artifactID",
                "artifactRevision",
                "parameterCount",
                "quantization",
                "format",
            }.issubset(model_required)
        )

    def test_policy_distinguishes_acceptance_from_reproduction(self) -> None:
        ranking = load_json(
            ROOT
            / "products"
            / "power"
            / "policies"
            / "ranking"
            / "1.0.0-draft.2.json"
        )
        intake = load_json(
            ROOT
            / "products"
            / "power"
            / "policies"
            / "intake"
            / "1.0.0-draft.1.json"
        )
        report_schema = load_json(
            PROGRAM_ROOT / "schemas" / "validation-report.schema.json"
        )

        self.assertEqual(
            ranking["distinctContributorThresholds"]["acceptedEvidence"],
            1,
        )
        self.assertEqual(
            ranking["distinctContributorThresholds"]["reproduced"],
            2,
        )
        self.assertEqual(
            ranking["distinctContributorThresholds"][
                "contributorWeightedAggregation"
            ],
            3,
        )
        self.assertIn("auto-accept", intake["classifications"])
        self.assertIn(
            "auto-accept",
            report_schema["properties"]["classification"]["enum"],
        )
        self.assertIn(
            "runnerCertificateID",
            ranking["exactComparisonKey"],
        )
        self.assertTrue(
            {
                "behaviorConformance",
                "recommendationEligibility",
                "metricEligibility",
            }.issubset(
                report_schema["properties"]["checks"]["properties"]
            )
        )

    def test_model_registry_selects_exact_rerun_candidates_only(self) -> None:
        registry = load_json(ROOT / "models" / "registry.json")
        cohort = load_json(
            ROOT
            / "models"
            / "cohorts"
            / "small-language-models"
            / "1.0.0-draft.1.json"
        )

        self.assertEqual(len(registry["entries"]), 4)
        self.assertFalse(registry["oldRankingStatusImported"])
        self.assertTrue(registry["performanceClaimsRequireNewAcceptedEvidence"])
        self.assertEqual(cohort["predicate"]["field"], "parameterCount")
        self.assertEqual(cohort["predicate"]["value"], 4_000_000_000)
        self.assertFalse(cohort["brandRestricted"])
        for entry in registry["entries"]:
            manifest = load_json(ROOT / entry["path"])
            self.assertEqual(manifest["status"], "rerun-candidate")
            self.assertFalse(manifest["oldRankingStatusImported"])
            self.assertTrue(
                manifest["performanceClaimsRequireNewAcceptedEvidence"]
            )
            self.assertEqual(len(manifest["artifactRevision"]), 40)
            self.assertEqual(len(manifest["weights"][0]["sha256"]), 64)
            self.assertEqual(len(manifest["tokenizer"]["sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
