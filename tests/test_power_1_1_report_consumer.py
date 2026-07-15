from __future__ import annotations

import hashlib
import json
import unittest

from scripts.consume_suite_b_power_1_1_report import (
    consumption_record,
    verify_pair,
)
from scripts.validate_suite_b_power_1_1_final_result import validate
from tests.test_suite_b_power_1_1_rc1_result import power_1_1_result


def encoded(result: dict) -> bytes:
    return (json.dumps(result, indent=2, sort_keys=True) + "\n").encode()


class PowerOneOneFinalReportConsumerTests(unittest.TestCase):
    def test_exact_pair_is_accepted_but_candidate_is_not_published(self) -> None:
        result = power_1_1_result()
        raw = encoded(result)
        report = validate(result, hashlib.sha256(raw).hexdigest())

        self.assertEqual(verify_pair(raw, result, report), [])
        record = consumption_record(result, report)
        self.assertTrue(record["acceptedForFinalReview"])
        self.assertTrue(record["measuredPerformanceRankingEligible"])
        self.assertFalse(record["activePublicRelease"])
        self.assertFalse(record["publicationAuthorized"])

    def test_changed_result_bytes_fail_closed(self) -> None:
        result = power_1_1_result()
        raw = encoded(result)
        report = validate(result, hashlib.sha256(raw).hexdigest())

        errors = verify_pair(raw + b" \n", result, report)

        self.assertIn(
            "validation report does not bind the exact result bytes", errors
        )

    def test_stale_report_fails_closed(self) -> None:
        result = power_1_1_result()
        raw = encoded(result)
        report = validate(result, hashlib.sha256(raw).hexdigest())
        report["performanceRankingEligibility"]["eligible"] = False
        report["performanceRankingEligibility"]["reasonCodes"] = [
            "primary_metric_ineligible"
        ]

        errors = verify_pair(raw, result, report)

        self.assertTrue(any("stale" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
