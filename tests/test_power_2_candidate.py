from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import repoctl
from scripts.lib.power2 import activation


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
    def test_candidate_stack_is_complete_but_inactive(self) -> None:
        summary = repoctl.verify_power_candidate()

        self.assertEqual(summary["status"], "valid-migration-draft")
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
        self.assertEqual(summary["appComponents"], 4)
        self.assertTrue(summary["appShellImplemented"])
        self.assertTrue(summary["runnerCertified"])
        self.assertFalse(summary["appReleased"])
        self.assertFalse(summary["publicIntakeOpen"])

    def test_certified_runner_remains_in_closed_candidate_stack(self) -> None:
        registry = load_json(ROOT / "products" / "power" / "registry.json")
        candidate = load_json(ROOT / registry["candidateStack"])
        measurement_stack = load_json(
            ROOT / candidate["measurementStack"]["path"]
        )

        self.assertIsNone(registry["currentStack"])
        self.assertFalse(registry["publicIntakeOpen"])
        self.assertFalse(candidate["publicIntakeOpen"])
        self.assertEqual(
            measurement_stack["runnerCertificate"],
            candidate["runnerCertificate"],
        )
        runner_certificate = load_json(
            ROOT / candidate["runnerCertificate"]["path"]
        )
        self.assertEqual(runner_certificate["state"], "active")
        self.assertEqual(
            runner_certificate["certificateID"],
            "power2-runner-"
            + candidate["runnerCandidate"]["sha256"][:12],
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
        self.assertFalse(
            (ROOT / "products" / "power" / "current.json").exists()
        )

    def test_prior_official_app_rehearsal_is_retained(self) -> None:
        candidate = load_json(ROOT / "products" / "power" / "candidate.json")
        app_candidate = load_json(
            ROOT / candidate["appReleaseCandidate"]["path"]
        )

        self.assertEqual(
            app_candidate["build"],
            "4",
        )
        self.assertEqual(
            app_candidate["verification"]["genericIOSReleaseBuild"],
            "pass",
        )
        self.assertEqual(
            app_candidate["verification"][
                "physicalDeviceEndToEndRehearsal"
            ],
            "pending",
        )
        self.assertIn(
            "complete a physical-device end-to-end rehearsal",
            app_candidate["releaseBlockedBy"],
        )
        prior_evidence = [
            evidence
            for evidence in candidate["appReleaseRehearsalEvidence"]
            if evidence["appComponents"]["sha256"]
            != candidate["appCandidate"]["sha256"]
        ]
        self.assertEqual(len(prior_evidence), 2)
        result = load_json(ROOT / prior_evidence[-1]["result"]["path"])
        review = load_json(ROOT / prior_evidence[-1]["review"]["path"])
        self.assertEqual(result["appRelease"]["build"], "2")
        self.assertEqual(review["status"], "pass")
        self.assertEqual(review["classification"], "auto-accept")
        self.assertFalse(review["publishable"])
        self.assertFalse(review["rankingEligible"])

    def test_activation_rejects_a_prior_build_without_writing(self) -> None:
        prior_result = (
            ROOT
            / "products"
            / "power"
            / "app-releases"
            / "evidence"
            / "15eb974a-e8de-44e1-80c9-0758ad7fc95b"
            / "result.json"
        )
        with self.assertRaisesRegex(
            activation.Power2ActivationError,
            (
                "did not pass the closed App release review: "
                "classification=reject; "
                "reasonCodes=app-release-not-supported; "
                "failedChecks=appRelease"
            ),
        ):
            activation.render_activation(
                prior_result,
                reviewed_at="2026-07-24T00:00:00Z",
                activated_at="2026-07-24T00:01:00Z",
                validator_source_revision=(
                    "4407a3776636e6c1a3a5892f78a3f4a841cecac7"
                ),
            )
        self.assertFalse(
            (ROOT / "products" / "power" / "current.json").exists()
        )

    def test_activation_renders_the_complete_exact_candidate_set(self) -> None:
        """Exercise the success path with a clearly synthetic in-memory copy."""

        candidate = load_json(ROOT / "products/power/candidate.json")
        app_candidate = load_json(
            ROOT / candidate["appReleaseCandidate"]["path"]
        )
        result = load_json(
            ROOT
            / "products/power/app-releases/evidence"
            / "15eb974a-e8de-44e1-80c9-0758ad7fc95b"
            / "result.json"
        )
        result["resultID"] = "00000000-0000-4000-8000-000000000042"
        result["appRelease"] = {
            "version": app_candidate["version"],
            "build": app_candidate["build"],
            "sourceRevision": app_candidate["sourceRevision"],
            "embeddedMeasurementStackSHA256": (
                candidate["measurementStack"]["sha256"]
            ),
        }

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic-result.json"
            path.write_text(
                json.dumps(result, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
            rendered = activation.render_activation(
                path,
                reviewed_at="2026-07-24T00:00:00Z",
                activated_at="2026-07-24T00:01:00Z",
                validator_source_revision=(
                    "4407a3776636e6c1a3a5892f78a3f4a841cecac7"
                ),
            )

        self.assertEqual(rendered.summary["status"], "ready")
        self.assertEqual(rendered.summary["fileCount"], 6)
        self.assertTrue(rendered.summary["publicIntakeOpen"])
        current = json.loads(
            rendered.files[activation.CURRENT_PATH].decode("utf-8")
        )
        self.assertEqual(current["status"], "active")
        self.assertTrue(current["publicIntakeOpen"])
        self.assertEqual(
            current["appRelease"],
            rendered.summary["appRelease"],
        )
        self.assertFalse(activation.CURRENT_PATH.exists())

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
