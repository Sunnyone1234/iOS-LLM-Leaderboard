from __future__ import annotations

import hashlib
import json
import unittest
from dataclasses import dataclass
from typing import Callable

from scripts import consume_suite_b_power_1_1_rc1_report as rc1_consumer
from scripts import consume_suite_b_power_1_1_report as final_consumer
from scripts.validate_suite_b_power_1_1_final_result import validate as validate_final
from scripts.validate_suite_b_power_1_1_rc1_result import validate as validate_rc1
from tests.test_suite_b_power_1_1_history import power_1_1_result


@dataclass(frozen=True)
class ConsumerHistoryCase:
    name: str
    validate: Callable[[dict, str], dict]
    verify_pair: Callable[[bytes, dict, dict], list[str]]
    consumption_record: Callable[[dict, dict], dict]
    expected_record: dict[str, bool]


CASES = (
    ConsumerHistoryCase(
        name="rc1",
        validate=validate_rc1,
        verify_pair=rc1_consumer.verify_pair,
        consumption_record=rc1_consumer.consumption_record,
        expected_record={
            "acceptedForRCReview": True,
            "measuredPerformanceRankingEligible": False,
            "recommendationEligible": False,
            "rankingAuthorized": False,
        },
    ),
    ConsumerHistoryCase(
        name="final",
        validate=validate_final,
        verify_pair=final_consumer.verify_pair,
        consumption_record=final_consumer.consumption_record,
        expected_record={
            "acceptedForFinalReview": True,
            "measuredPerformanceRankingEligible": True,
            "activePublicRelease": True,
            "publicationAuthorized": True,
        },
    ),
)


def encoded(result: dict) -> bytes:
    return (json.dumps(result, indent=2, sort_keys=True) + "\n").encode()


class PowerOneOneReportConsumerHistoryTests(unittest.TestCase):
    def test_exact_pair_respects_each_release_authority(self) -> None:
        for case in CASES:
            with self.subTest(case=case.name):
                result = power_1_1_result()
                raw = encoded(result)
                report = case.validate(result, hashlib.sha256(raw).hexdigest())
                self.assertEqual(case.verify_pair(raw, result, report), [])
                record = case.consumption_record(result, report)
                for key, value in case.expected_record.items():
                    self.assertEqual(record[key], value)

    def test_changed_result_bytes_fail_closed(self) -> None:
        for case in CASES:
            with self.subTest(case=case.name):
                result = power_1_1_result()
                raw = encoded(result)
                report = case.validate(result, hashlib.sha256(raw).hexdigest())
                errors = case.verify_pair(raw + b" \n", result, report)
                self.assertIn(
                    "validation report does not bind the exact result bytes",
                    errors,
                )

    def test_stale_report_fails_closed(self) -> None:
        for case in CASES:
            with self.subTest(case=case.name):
                result = power_1_1_result()
                raw = encoded(result)
                report = case.validate(result, hashlib.sha256(raw).hexdigest())
                if case.name == "rc1":
                    report["behaviorConformance"]["reasonCodes"] = [
                        "behavior_not_verified"
                    ]
                else:
                    report["performanceRankingEligibility"]["eligible"] = False
                    report["performanceRankingEligibility"]["reasonCodes"] = [
                        "primary_metric_ineligible"
                    ]
                errors = case.verify_pair(raw, result, report)
                self.assertTrue(
                    any("stale" in error or "reasonCodes" in error for error in errors)
                )


if __name__ == "__main__":
    unittest.main()
