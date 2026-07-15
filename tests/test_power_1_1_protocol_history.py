from __future__ import annotations

import hashlib
import json
import unittest
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "benchmarks" / "suite-b-on-device-performance"
POWER_1_0_RESULT_SCHEMA = ROOT / "schemas/suite-b-power-result-1.0.0-rc.1.schema.json"


@dataclass(frozen=True)
class ProtocolHistoryCase:
    name: str
    version: str
    protocol_status: str
    manifest_status: str
    protocol_json: Path
    protocol_markdown: Path
    manifest_path: Path
    report_schema_path: Path
    result_schema_path: Path
    pins_ranking_policy: bool

    def load(self) -> dict[str, object]:
        return {
            "protocol": json.loads(self.protocol_json.read_text()),
            "document": self.protocol_markdown.read_text(),
            "manifest": json.loads(self.manifest_path.read_text()),
            "report_schema": json.loads(self.report_schema_path.read_text()),
            "result_schema": json.loads(self.result_schema_path.read_text()),
        }


CASES = (
    ProtocolHistoryCase(
        name="draft",
        version="1.1.0-draft.1",
        protocol_status="protocol-draft",
        manifest_status="protocol-draft",
        protocol_json=SUITE / "power-1.1-protocol.json",
        protocol_markdown=SUITE / "power-1.1-protocol.md",
        manifest_path=SUITE / "releases/suite-b-power-1.1.0-draft.1.json",
        report_schema_path=ROOT
        / "schemas/suite-b-power-validation-report-1.1.0-draft.1.schema.json",
        result_schema_path=ROOT
        / "schemas/suite-b-power-result-1.1.0-draft.1.schema.json",
        pins_ranking_policy=False,
    ),
    ProtocolHistoryCase(
        name="rc1",
        version="1.1.0-rc.1",
        protocol_status="release-candidate",
        manifest_status="schema-validator-app-frozen",
        protocol_json=SUITE / "power-1.1-rc1-protocol.json",
        protocol_markdown=SUITE / "power-1.1-rc1-protocol.md",
        manifest_path=SUITE / "releases/suite-b-power-1.1.0-rc.1.json",
        report_schema_path=ROOT
        / "schemas/suite-b-power-validation-report-1.1.0-rc.1.schema.json",
        result_schema_path=ROOT
        / "schemas/suite-b-power-result-1.1.0-rc.1.schema.json",
        pins_ranking_policy=True,
    ),
)


def references(value: object) -> list[str]:
    if isinstance(value, dict):
        found = [value["$ref"]] if isinstance(value.get("$ref"), str) else []
        return found + [
            reference for child in value.values() for reference in references(child)
        ]
    if isinstance(value, list):
        return [
            reference for child in value for reference in references(child)
        ]
    return []


class PowerOneOneProtocolHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.history = [(case, case.load()) for case in CASES]
        cls.power_1_0_protocol = json.loads(
            (SUITE / "power-1.0-protocol.json").read_text()
        )
        cls.power_1_0_result_schema = json.loads(
            POWER_1_0_RESULT_SCHEMA.read_text()
        )

    def test_non_official_versions_preserve_workload_ids(self) -> None:
        for case, assets in self.history:
            with self.subTest(case=case.name):
                protocol = assets["protocol"]
                self.assertEqual(protocol["protocol_version"], case.version)
                self.assertEqual(protocol["status"], case.protocol_status)
                self.assertFalse(protocol["official_result_eligible"])
                self.assertFalse(protocol["ranking_authorized"])
                self.assertFalse(protocol["publication_authorized"])
                self.assertEqual(
                    [item["workload_id"] for item in protocol["workloads"]],
                    [
                        "b-ux-001-short-interaction",
                        "b-pipe-001-sustained-generation",
                    ],
                )

    def test_fixture_and_measurement_identities_match_power_1_0(self) -> None:
        old = {
            item["workload_id"]: item
            for item in self.power_1_0_protocol["workloads"]
        }
        for case, assets in self.history:
            with self.subTest(case=case.name):
                new = {
                    item["workload_id"]: item
                    for item in assets["protocol"]["workloads"]
                }
                self.assertEqual(set(old), set(new))
                for workload_id in old:
                    self.assertEqual(
                        new[workload_id]["fixture_sha256"],
                        old[workload_id]["fixture_sha256"],
                    )
                    self.assertEqual(
                        new[workload_id]["measurement_mode"],
                        old[workload_id]["measurement_mode"],
                    )

    def test_app_exports_measurements_and_validator_owns_decisions(self) -> None:
        for case, assets in self.history:
            with self.subTest(case=case.name):
                protocol = assets["protocol"]
                export = protocol["app_evidence_export"]
                validator = protocol["submission_validator"]
                self.assertEqual(export["role"], "evidence-producer")
                self.assertTrue(export["must_export_raw_evidence"])
                self.assertTrue(export["must_export_technically_derivable_metrics"])
                self.assertFalse(export["behavior_failure_may_null_metrics"])
                self.assertEqual(export["local_behavior_assessment"], "advisory-only")
                self.assertTrue(validator["decision_authority"])
                self.assertTrue(validator["recompute_metrics_from_raw_evidence"])
                self.assertTrue(
                    validator["recompute_behavior_conformance_from_generated_text"]
                )
                self.assertFalse(validator["trust_app_behavior_assessment"])

    def test_behavior_conformance_never_gates_a_metric(self) -> None:
        for case, assets in self.history:
            with self.subTest(case=case.name):
                protocol = assets["protocol"]
                self.assertTrue(protocol["metric_behavior_gates"])
                self.assertTrue(
                    all(
                        gated is False
                        for gated in protocol["metric_behavior_gates"].values()
                    )
                )
                ux = protocol["workloads"][0]["response_conformance"]
                self.assertFalse(ux["affects_measurement_eligibility"])
                self.assertFalse(ux["affects_performance_ranking_eligibility"])
                self.assertTrue(ux["affects_recommendation_eligibility"])
                self.assertEqual(
                    ux["assessment_statuses"],
                    ["verified", "not_verified", "contradicted"],
                )
                self.assertEqual(ux["policy_non_match_status"], "not_verified")

    def test_submission_determines_facts_and_ranking_consumes_report(self) -> None:
        for case, assets in self.history:
            with self.subTest(case=case.name):
                protocol = assets["protocol"]
                validator = protocol["submission_validator"]
                report = protocol["validation_report"]
                leaderboard = protocol["leaderboard_consumer"]
                self.assertEqual(
                    validator["execution_stage"], "submission-intake-and-review"
                )
                self.assertEqual(report["producer"], "submission-validator")
                self.assertTrue(report["authoritative_fact_record"])
                self.assertTrue(report["binds_exact_result_sha256"])
                self.assertTrue(report["behavior_nonconformant_evidence_may_be_retained"])
                self.assertEqual(
                    leaderboard["role"], "validation-report-policy-consumer"
                )
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
        expected_properties = {
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
        }
        for case, assets in self.history:
            with self.subTest(case=case.name):
                properties = assets["report_schema"]["properties"]
                self.assertFalse(assets["report_schema"]["additionalProperties"])
                self.assertEqual(set(properties), expected_properties)
                self.assertNotIn("attempts", properties)
                self.assertNotIn("rawEvidence", properties)
                self.assertEqual(
                    properties["result"]["properties"]["sha256"]["pattern"],
                    "^[0-9a-f]{64}$",
                )
                if case.name == "rc1":
                    self.assertEqual(
                        properties["validator"]["properties"]["version"]["const"],
                        case.version,
                    )
                    self.assertEqual(
                        properties["rankingPolicy"]["properties"]["version"]["const"],
                        case.version,
                    )
                report_contract = assets["protocol"]["validation_report"]
                self.assertTrue(report_contract["automatically_generated"])
                self.assertFalse(report_contract["contributor_supplied"])
                self.assertFalse(report_contract["duplicates_raw_evidence"])

    def test_result_schema_versions_the_same_submitted_field_shape(self) -> None:
        previous = self.power_1_0_result_schema
        for case, assets in self.history:
            with self.subTest(case=case.name):
                current = assets["result_schema"]
                self.assertEqual(current["required"], previous["required"])
                self.assertEqual(set(current["properties"]), set(previous["properties"]))
                self.assertEqual(
                    current["properties"]["schemaVersion"]["const"],
                    f"suite-b-power-result-{case.version}",
                )
                release = current["properties"]["benchmarkRelease"]["properties"]
                self.assertEqual(release["version"]["const"], case.version)
                self.assertEqual(release["protocolVersion"]["const"], case.version)
                execution = current["properties"]["execution"]["properties"]
                self.assertEqual(execution["workloadVersion"]["const"], case.version)
                self.assertFalse(
                    current["properties"]["officialResultEligible"]["const"]
                )
                self.assertEqual(
                    assets["protocol"]["result_schema"]["new_contributor_fields"],
                    [],
                )

    def test_result_schema_keeps_app_behavior_advisory(self) -> None:
        for case, assets in self.history:
            with self.subTest(case=case.name):
                result_schema = assets["result_schema"]
                attempts = result_schema["properties"]["attempts"]
                summary = result_schema["properties"]["summary"]
                self.assertIn("advisory App observation only", attempts["description"])
                self.assertIn(
                    "must not suppress technically derivable", attempts["description"]
                )
                self.assertIn("independently of advisory", summary["description"])
                contract = assets["protocol"]["result_schema"]
                self.assertEqual(
                    contract["app_response_conformance_member"], "advisory-only"
                )
                self.assertTrue(contract["semantic_validator_recomputes_behavior"])
                self.assertTrue(
                    contract[
                        "technically_derivable_metrics_independent_of_app_behavior_assessment"
                    ]
                )

    def test_result_schema_reuses_only_valid_power_1_0_pointers(self) -> None:
        base_id = self.power_1_0_result_schema["$id"]
        for case, assets in self.history:
            with self.subTest(case=case.name):
                refs = references(assets["result_schema"])
                self.assertTrue(refs)
                for reference in refs:
                    self.assertTrue(reference.startswith(f"{base_id}#/"))
                    target: object = self.power_1_0_result_schema
                    for raw_part in reference.split("#/", 1)[1].split("/"):
                        part = raw_part.replace("~1", "/").replace("~0", "~")
                        target = (
                            target[int(part)]
                            if isinstance(target, list)
                            else target[part]
                        )
                    self.assertIsNotNone(target)

    def test_behavior_assessment_distinguishes_unverified_from_contradicted(self) -> None:
        for case, assets in self.history:
            with self.subTest(case=case.name):
                behavior = assets["report_schema"]["properties"][
                    "behaviorConformance"
                ]
                self.assertEqual(
                    behavior["properties"]["status"]["enum"],
                    ["verified", "not_verified", "contradicted", None],
                )
                contract = assets["protocol"]["validation_report"][
                    "behavior_assessment"
                ]
                self.assertFalse(contract["non_match_is_semantic_failure"])
                self.assertEqual(contract["non_match_status"], "not_verified")

    def test_migration_and_manifest_status_are_versioned(self) -> None:
        for case, assets in self.history:
            with self.subTest(case=case.name):
                migration = assets["protocol"]["migration"]
                self.assertTrue(migration["power_1_0_evidence_immutable"])
                self.assertFalse(migration["power_1_0_evidence_promotable"])
                self.assertTrue(migration["new_execution_required_for_official_1_1"])
                self.assertEqual(assets["manifest"]["status"], case.manifest_status)
                self.assertFalse(assets["manifest"]["officialResultEligible"])
                self.assertFalse(assets["manifest"]["rankingAuthorized"])

    def test_manifest_pins_every_versioned_asset(self) -> None:
        for case, assets in self.history:
            with self.subTest(case=case.name):
                manifest = assets["manifest"]
                pinned = [
                    manifest["protocol"]["markdown"],
                    manifest["protocol"]["machineReadable"],
                    manifest["resultSchema"]["schema"],
                    manifest["resultSchema"]["baseShapeDependency"],
                    manifest["validationReportSchema"],
                    manifest["validator"],
                    manifest["validationReasonRegistry"],
                ]
                if case.pins_ranking_policy:
                    pinned.append(manifest["rankingPolicy"])
                for asset in pinned:
                    path = ROOT / asset["path"]
                    self.assertEqual(
                        hashlib.sha256(path.read_bytes()).hexdigest(),
                        asset["sha256"],
                    )

    def test_human_protocol_states_submission_authority(self) -> None:
        expected = (
            "The App is an evidence producer",
            "The independent validator is the sole authority",
            "never set a technically derivable metric to `null`",
            "Submission-time fact determination",
            "Ranking-time policy application",
            "consumer of the validation report",
            "not a claim that the response is semantically wrong",
            "synonym such as `secure`",
            "No contributor-authored field is added",
            "explicitly\nadvisory",
            "Power 1.0 evidence is immutable",
        )
        for case, assets in self.history:
            with self.subTest(case=case.name):
                document = assets["document"]
                for statement in expected:
                    self.assertIn(statement, document)
                if case.name == "rc1":
                    self.assertIn("frozen, non-official release", document)


if __name__ == "__main__":
    unittest.main()
