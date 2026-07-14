from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "benchmarks" / "suite-b-on-device-performance"
MANIFEST = SUITE / "releases" / "suite-b-power-1.1.0-draft.1.json"
REPORT_SCHEMA = ROOT / "schemas" / "suite-b-power-validation-report-1.1.0-draft.1.schema.json"


class PowerOneOneProtocolDraftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.protocol = json.loads((SUITE / "power-1.1-protocol.json").read_text())
        cls.manifest = json.loads(MANIFEST.read_text())
        cls.report_schema = json.loads(REPORT_SCHEMA.read_text())

    def test_draft_is_non_official_and_preserves_workload_ids(self) -> None:
        self.assertEqual(self.protocol["protocol_version"], "1.1.0-draft.1")
        self.assertEqual(self.protocol["status"], "protocol-draft")
        self.assertFalse(self.protocol["official_result_eligible"])
        self.assertFalse(self.protocol["ranking_authorized"])
        self.assertFalse(self.protocol["publication_authorized"])
        self.assertEqual(
            [item["workload_id"] for item in self.protocol["workloads"]],
            ["b-ux-001-short-interaction", "b-pipe-001-sustained-generation"],
        )

    def test_fixture_and_measurement_identities_match_power_1_0(self) -> None:
        previous = json.loads((SUITE / "power-1.0-protocol.json").read_text())
        old = {item["workload_id"]: item for item in previous["workloads"]}
        new = {item["workload_id"]: item for item in self.protocol["workloads"]}
        self.assertEqual(set(old), set(new))
        for workload_id in old:
            self.assertEqual(new[workload_id]["fixture_sha256"], old[workload_id]["fixture_sha256"])
            self.assertEqual(new[workload_id]["measurement_mode"], old[workload_id]["measurement_mode"])

    def test_app_exports_measurements_and_validator_owns_decisions(self) -> None:
        export = self.protocol["app_evidence_export"]
        validator = self.protocol["submission_validator"]
        self.assertEqual(export["role"], "evidence-producer")
        self.assertTrue(export["must_export_raw_evidence"])
        self.assertTrue(export["must_export_technically_derivable_metrics"])
        self.assertFalse(export["behavior_failure_may_null_metrics"])
        self.assertEqual(export["local_behavior_assessment"], "advisory-only")
        self.assertTrue(validator["decision_authority"])
        self.assertTrue(validator["recompute_metrics_from_raw_evidence"])
        self.assertTrue(validator["recompute_behavior_conformance_from_generated_text"])
        self.assertFalse(validator["trust_app_behavior_assessment"])

    def test_behavior_conformance_never_gates_a_metric(self) -> None:
        self.assertTrue(self.protocol["metric_behavior_gates"])
        self.assertTrue(
            all(gated is False for gated in self.protocol["metric_behavior_gates"].values())
        )
        ux = self.protocol["workloads"][0]["response_conformance"]
        self.assertFalse(ux["affects_measurement_eligibility"])
        self.assertFalse(ux["affects_performance_ranking_eligibility"])
        self.assertTrue(ux["affects_recommendation_eligibility"])
        self.assertEqual(
            ux["assessment_statuses"],
            ["verified", "not_verified", "contradicted"],
        )
        self.assertEqual(ux["policy_non_match_status"], "not_verified")

    def test_submission_determines_facts_and_ranking_consumes_report(self) -> None:
        validator = self.protocol["submission_validator"]
        report = self.protocol["validation_report"]
        leaderboard = self.protocol["leaderboard_consumer"]
        self.assertEqual(validator["execution_stage"], "submission-intake-and-review")
        self.assertEqual(report["producer"], "submission-validator")
        self.assertTrue(report["authoritative_fact_record"])
        self.assertTrue(report["binds_exact_result_sha256"])
        self.assertTrue(report["behavior_nonconformant_evidence_may_be_retained"])
        self.assertEqual(leaderboard["role"], "validation-report-policy-consumer")
        self.assertFalse(leaderboard["recompute_conformance_from_raw_result"])
        self.assertFalse(leaderboard["duplicate_validator_rules"])
        self.assertEqual(
            leaderboard["measured_performance_decision"],
            "performance-ranking-eligibility",
        )
        self.assertEqual(
            leaderboard["missing_stale_unsupported_or_mismatched_report"],
            "fail-closed",
        )

    def test_validation_report_is_minimal_internal_contract(self) -> None:
        properties = self.report_schema["properties"]
        self.assertFalse(self.report_schema["additionalProperties"])
        self.assertEqual(
            set(properties),
            {
                "schemaVersion",
                "result",
                "benchmarkRelease",
                "validator",
                "rankingPolicy",
                "structuralValidity",
                "protocolConformance",
                "metricEligibility",
                "behaviorConformance",
                "performanceRankingEligibility",
                "recommendationEligibility",
            },
        )
        self.assertNotIn("attempts", properties)
        self.assertNotIn("rawEvidence", properties)
        self.assertEqual(
            properties["result"]["properties"]["sha256"]["pattern"],
            "^[0-9a-f]{64}$",
        )
        report_contract = self.protocol["validation_report"]
        self.assertTrue(report_contract["automatically_generated"])
        self.assertFalse(report_contract["contributor_supplied"])
        self.assertFalse(report_contract["duplicates_raw_evidence"])

    def test_behavior_assessment_distinguishes_unverified_from_contradicted(self) -> None:
        behavior = self.report_schema["properties"]["behaviorConformance"]
        self.assertEqual(
            behavior["properties"]["status"]["enum"],
            ["verified", "not_verified", "contradicted", None],
        )
        contract = self.protocol["validation_report"]["behavior_assessment"]
        self.assertFalse(contract["non_match_is_semantic_failure"])
        self.assertEqual(contract["non_match_status"], "not_verified")

    def test_migration_keeps_power_1_0_immutable(self) -> None:
        migration = self.protocol["migration"]
        self.assertTrue(migration["power_1_0_evidence_immutable"])
        self.assertFalse(migration["power_1_0_evidence_promotable"])
        self.assertTrue(migration["new_execution_required_for_official_1_1"])
        self.assertEqual(self.manifest["status"], "protocol-draft")
        self.assertFalse(self.manifest["officialResultEligible"])
        self.assertFalse(self.manifest["rankingAuthorized"])

    def test_draft_manifest_pins_protocol_files(self) -> None:
        for asset in (
            self.manifest["protocol"]["markdown"],
            self.manifest["protocol"]["machineReadable"],
            self.manifest["validationReportSchema"],
        ):
            path = ROOT / asset["path"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), asset["sha256"])

    def test_human_protocol_states_submission_authority(self) -> None:
        document = (SUITE / "power-1.1-protocol.md").read_text()
        self.assertIn("The App is an evidence producer", document)
        self.assertIn("The independent validator is the sole authority", document)
        self.assertIn("never set a technically derivable metric to `null`", document)
        self.assertIn("Submission-time fact determination", document)
        self.assertIn("Ranking-time policy application", document)
        self.assertIn("consumer of the validation report", document)
        self.assertIn("not a claim that the response is semantically wrong", document)
        self.assertIn("synonym such as `secure`", document)
        self.assertIn("Power 1.0 evidence is immutable", document)


if __name__ == "__main__":
    unittest.main()
