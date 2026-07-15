from __future__ import annotations

import copy
import hashlib
import json
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from scripts import validate_suite_b_power_1_1_rc1_result as rc1_validator
from scripts import validate_suite_b_power_1_1_result as draft_validator
from tests.test_suite_b_power_result import refresh_summary, valid_result


ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "benchmarks/suite-b-on-device-performance"


@dataclass(frozen=True)
class ValidatorHistoryCase:
    name: str
    version: str
    validate: Callable[[dict, str], dict]
    validate_report_shape: Callable[[dict], list[str]]
    verify_assets: Callable[[], list[str]]
    reason_registry: Path
    ranking_reason: str
    pins_reference_app: bool


DRAFT = ValidatorHistoryCase(
    name="draft",
    version="1.1.0-draft.1",
    validate=draft_validator.validate,
    validate_report_shape=draft_validator.validate_report_shape,
    verify_assets=draft_validator.verify_draft_assets,
    reason_registry=SUITE / "power-1.1-validation-reasons.json",
    ranking_reason="protocol_draft_not_rank_authorized",
    pins_reference_app=False,
)
RC1 = ValidatorHistoryCase(
    name="rc1",
    version="1.1.0-rc.1",
    validate=rc1_validator.validate,
    validate_report_shape=rc1_validator.validate_report_shape,
    verify_assets=rc1_validator.verify_rc_assets,
    reason_registry=SUITE / "power-1.1-rc1-validation-reasons.json",
    ranking_reason="release_candidate_not_rank_authorized",
    pins_reference_app=True,
)
CASES = (DRAFT, RC1)


def versioned_result(
    case: ValidatorHistoryCase,
    workload_id: str = "b-pipe-001-sustained-generation",
) -> dict:
    result = valid_result(workload_id)
    result["schemaVersion"] = f"suite-b-power-result-{case.version}"
    result["benchmarkRelease"]["version"] = case.version
    result["benchmarkRelease"]["protocolVersion"] = case.version
    result["execution"]["workloadVersion"] = case.version
    if case.pins_reference_app:
        manifest = json.loads(
            (SUITE / "releases/suite-b-power-1.1.0-rc.1.json").read_text()
        )
        reference = manifest["referenceApp"]
        result["execution"]["runnerVersion"] = reference["version"]
        result["execution"]["appVersion"] = reference["version"]
        result["execution"]["appBuild"] = reference["build"]
        result["execution"]["appSourceCommit"] = reference["sourceCommit"]
    return result


def power_1_1_result(
    workload_id: str = "b-pipe-001-sustained-generation",
) -> dict:
    """Build the RC1-shaped fixture consumed by final Power 1.1 tests."""
    return versioned_result(RC1, workload_id)


def result_digest(result: dict) -> str:
    raw = json.dumps(result, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()


def report_for(case: ValidatorHistoryCase, result: dict) -> dict:
    return case.validate(result, result_digest(result))


def report_reason_codes(report: object) -> set[str]:
    if isinstance(report, dict):
        found = set(report.get("reasonCodes", []))
        for value in report.values():
            found.update(report_reason_codes(value))
        return found
    if isinstance(report, list):
        return {
            reason for value in report for reason in report_reason_codes(value)
        }
    return set()


class PowerOneOneValidatorHistoryTests(unittest.TestCase):
    def test_all_frozen_assets_are_digest_pinned(self) -> None:
        for case in CASES:
            with self.subTest(case=case.name):
                self.assertEqual(case.verify_assets(), [])

    def test_short_interaction_keeps_measurement_and_behavior_separate(self) -> None:
        for case in CASES:
            with self.subTest(case=case.name):
                result = versioned_result(case, "b-ux-001-short-interaction")
                digest = result_digest(result)
                report = case.validate(result, digest)
                self.assertEqual(case.validate_report_shape(report), [])
                self.assertEqual(report["result"]["sha256"], digest)
                self.assertTrue(report["structuralValidity"]["valid"])
                self.assertTrue(report["protocolConformance"]["valid"])
                self.assertTrue(
                    report["metricEligibility"][
                        "first_renderable_proxy_ttft_ms@1"
                    ]["eligible"]
                )
                self.assertEqual(report["behaviorConformance"]["status"], "verified")
                self.assertFalse(report["performanceRankingEligibility"]["eligible"])
                self.assertIn(
                    case.ranking_reason,
                    report["performanceRankingEligibility"]["reasonCodes"],
                )

    def test_correct_synonym_is_not_verified_without_losing_metrics(self) -> None:
        for case in CASES:
            with self.subTest(case=case.name):
                result = versioned_result(case, "b-ux-001-short-interaction")
                for attempt in result["attempts"][1:]:
                    attempt["generatedText"] = (
                        "Your note is securely stored on this device. "
                        "It will sync when connectivity returns."
                    )
                report = report_for(case, result)
                metric = report["metricEligibility"][
                    "first_renderable_proxy_ttft_ms@1"
                ]
                self.assertTrue(report["protocolConformance"]["valid"])
                self.assertEqual(
                    report["behaviorConformance"]["status"], "not_verified"
                )
                self.assertEqual(
                    report["behaviorConformance"]["reasonCodes"],
                    ["behavior_not_verified"],
                )
                self.assertTrue(metric["eligible"])
                self.assertNotIn("behavior_not_verified", metric["reasonCodes"])
                self.assertIn(
                    "behavior_verification_required",
                    report["recommendationEligibility"]["reasonCodes"],
                )

    def test_app_behavior_assessment_is_advisory_only(self) -> None:
        for case in CASES:
            with self.subTest(case=case.name):
                result = versioned_result(case, "b-ux-001-short-interaction")
                for attempt in result["attempts"]:
                    attempt["responseConformance"] = {
                        "status": "fail",
                        "reasonCodes": ["response_conformance_failed"],
                    }
                report = report_for(case, result)
                self.assertTrue(report["protocolConformance"]["valid"])
                self.assertEqual(report["behaviorConformance"]["status"], "verified")

    def test_behavior_gated_null_metrics_are_rejected(self) -> None:
        for case in CASES:
            with self.subTest(case=case.name):
                result = versioned_result(case, "b-ux-001-short-interaction")
                for attempt in result["attempts"][1:]:
                    attempt["responseConformance"] = {
                        "status": "fail",
                        "reasonCodes": ["response_conformance_failed"],
                    }
                    attempt["derivedMetrics"] = {
                        key: None for key in attempt["derivedMetrics"]
                    }
                refresh_summary(result)
                report = report_for(case, result)
                self.assertFalse(report["protocolConformance"]["valid"])
                self.assertIn(
                    "aggregate_mismatch",
                    report["protocolConformance"]["reasonCodes"],
                )
                self.assertTrue(
                    report["metricEligibility"][
                        "first_renderable_proxy_ttft_ms@1"
                    ]["eligible"]
                )

    def test_pipeline_behavior_is_not_applicable(self) -> None:
        for case in CASES:
            with self.subTest(case=case.name):
                report = report_for(case, versioned_result(case))
                self.assertTrue(report["protocolConformance"]["valid"])
                self.assertEqual(
                    report["behaviorConformance"],
                    {
                        "applicable": False,
                        "policyID": None,
                        "status": None,
                        "reasonCodes": [],
                    },
                )
                self.assertEqual(case.validate_report_shape(report), [])

    def test_structurally_invalid_result_emits_a_valid_minimal_report(self) -> None:
        for case in CASES:
            with self.subTest(case=case.name):
                result = versioned_result(case)
                del result["model"]["displayName"]
                report = report_for(case, result)
                self.assertFalse(report["structuralValidity"]["valid"])
                self.assertFalse(report["protocolConformance"]["valid"])
                self.assertEqual(report["metricEligibility"], {})
                self.assertEqual(case.validate_report_shape(report), [])

    def test_tampered_token_identity_is_protocol_invalid(self) -> None:
        for case in CASES:
            with self.subTest(case=case.name):
                result = versioned_result(case)
                result["attempts"][2]["tokenEvents"][1]["index"] = 7
                report = report_for(case, result)
                self.assertFalse(report["protocolConformance"]["valid"])
                self.assertIn(
                    "token_evidence_invalid",
                    report["protocolConformance"]["reasonCodes"],
                )

    def test_behavior_uses_three_of_five_measured_attempts(self) -> None:
        for case in CASES:
            with self.subTest(case=case.name):
                result = versioned_result(case, "b-ux-001-short-interaction")
                for attempt in result["attempts"][1:3]:
                    attempt["generatedText"] = "Done."
                self.assertEqual(
                    report_for(case, result)["behaviorConformance"]["status"],
                    "verified",
                )
                result["attempts"][3]["generatedText"] = "Done."
                self.assertEqual(
                    report_for(case, result)["behaviorConformance"]["status"],
                    "not_verified",
                )

    def test_report_reason_codes_are_registered(self) -> None:
        for case in CASES:
            with self.subTest(case=case.name):
                registry = set(json.loads(case.reason_registry.read_text())["reason_codes"])
                reports = [
                    report_for(case, versioned_result(case)),
                    report_for(
                        case,
                        versioned_result(case, "b-ux-001-short-interaction"),
                    ),
                ]
                invalid = versioned_result(case)
                invalid["environment"]["batteryLevelPercentAtStart"] = 20
                reports.append(report_for(case, invalid))
                for report in reports:
                    self.assertLessEqual(report_reason_codes(report), registry)

    def test_validation_is_deterministic_and_does_not_mutate_result(self) -> None:
        for case in CASES:
            with self.subTest(case=case.name):
                result = versioned_result(case, "b-ux-001-short-interaction")
                original = copy.deepcopy(result)
                digest = result_digest(result)
                self.assertEqual(
                    case.validate(result, digest), case.validate(result, digest)
                )
                self.assertEqual(result, original)

    def test_rc1_executes_its_schema_without_identity_translation(self) -> None:
        result = power_1_1_result()
        result["model"]["unexpected"] = True
        report = report_for(RC1, result)
        self.assertFalse(report["structuralValidity"]["valid"])

    def test_rc1_report_rejects_unfrozen_versions(self) -> None:
        report = report_for(RC1, power_1_1_result())
        report["validator"]["version"] = "other"
        report["rankingPolicy"]["version"] = "other"
        errors = RC1.validate_report_shape(report)
        self.assertTrue(any("validator.version" in error for error in errors))
        self.assertTrue(any("rankingPolicy.version" in error for error in errors))

    def test_rc1_report_rejects_inconsistent_behavior_reason(self) -> None:
        report = report_for(
            RC1, power_1_1_result("b-ux-001-short-interaction")
        )
        report["behaviorConformance"]["status"] = "not_verified"
        report["behaviorConformance"]["reasonCodes"] = []
        self.assertNotEqual(RC1.validate_report_shape(report), [])


if __name__ == "__main__":
    unittest.main()
