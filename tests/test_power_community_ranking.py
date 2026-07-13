from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.generate_power_community_ranking import aggregate_contributions
from scripts.generate_power_community_ranking import build_dataset
from scripts.generate_power_community_ranking import make_contribution
from scripts.validate_power_pr_contributor import validate_contributor
from tests.test_suite_b_power_result import valid_result


ROOT = Path(__file__).resolve().parents[1]


def contribution(
    number: int,
    contributor: str,
    *,
    workload: str = "b-pipe-001-sustained-generation",
    runtime_version: str = "1.0",
    primary_value: float | None = None,
    raw_sha256: str | None = None,
) -> dict:
    result = copy.deepcopy(valid_result(workload))
    result["resultID"] = f"{number:08x}-1111-4111-8111-{number:012x}"
    result["execution"]["sessionID"] = f"{number:08x}-2222-4222-8222-{number:012x}"
    result["createdAt"] = f"2026-07-13T12:{number:02d}:00Z"
    result["runtime"]["version"] = runtime_version
    item = make_contribution(
        contributor=contributor,
        result=result,
        raw_path=f"synthetic/{number}.json",
        raw_sha256=raw_sha256 or hashlib.sha256(str(number).encode()).hexdigest(),
        source_kind="community-submission",
        evidence_level="unreviewed",
        submission_id=f"{number:08x}-3333-4333-8333-{number:012x}",
    )
    if primary_value is not None:
        field = (
            "medianFirstRenderableProxyTTFTMilliseconds"
            if workload.startswith("b-ux")
            else "medianDecodeTokensPerSecond"
        )
        item["result"]["summary"]["metrics"][field] = primary_value
    return item


class CommunityRankingTests(unittest.TestCase):
    def test_current_official_matrix_builds_without_mutating_release(self) -> None:
        dataset = build_dataset()
        self.assertEqual(dataset["officialReferenceResultCount"], 6)
        self.assertEqual(dataset["communityResultCount"], 0)
        self.assertEqual(dataset["cellCount"], 6)
        self.assertEqual(dataset["activeRankedCellCount"], 5)
        self.assertEqual(dataset["contributorCount"], 1)
        self.assertEqual(dataset["reproducedCellCount"], 0)

    def test_same_account_counts_once_within_same_cell(self) -> None:
        cells = aggregate_contributions([
            contribution(1, "Alice", primary_value=10),
            contribution(2, "alice", primary_value=14),
            contribution(3, "Bob", primary_value=20),
            contribution(4, "Carol", primary_value=30),
        ])
        self.assertEqual(len(cells), 1)
        cell = cells[0]
        self.assertEqual(cell["community"]["contributorCount"], 3)
        self.assertEqual(cell["community"]["runCount"], 4)
        self.assertEqual(cell["community"]["status"], "reproduced")
        self.assertEqual(cell["community"]["aggregateStatus"], "community-aggregate")
        # Alice contributes median(10, 14) = 12 once; median(12, 20, 30) = 20.
        self.assertEqual(cell["primaryMetric"]["value"], 20)

    def test_same_account_can_count_in_multiple_different_cells(self) -> None:
        cells = aggregate_contributions([
            contribution(1, "Alice", runtime_version="1.0"),
            contribution(2, "Alice", runtime_version="2.0"),
            contribution(3, "Alice", workload="b-ux-001-short-interaction"),
        ])
        self.assertEqual(len(cells), 3)
        self.assertTrue(all(cell["community"]["contributorCount"] == 1 for cell in cells))

    def test_two_accounts_mark_cell_reproduced_without_enabling_aggregate(self) -> None:
        cell = aggregate_contributions([
            contribution(1, "Alice"),
            contribution(2, "Bob"),
        ])[0]
        self.assertEqual(cell["community"]["status"], "reproduced")
        self.assertEqual(cell["community"]["aggregateStatus"], "provisional")

    def test_duplicate_result_evidence_is_rejected(self) -> None:
        digest = "a" * 64
        with self.assertRaisesRegex(ValueError, "duplicate rawSHA256"):
            aggregate_contributions([
                contribution(1, "Alice", raw_sha256=digest),
                contribution(2, "Bob", raw_sha256=digest),
            ])

    def test_high_variation_warns_but_does_not_remove_cell(self) -> None:
        cell = aggregate_contributions([
            contribution(1, "Alice", primary_value=10),
            contribution(2, "Bob", primary_value=40),
        ])[0]
        variation = cell["community"]["primaryMetricVariation"]
        self.assertTrue(variation["high"])
        self.assertFalse(variation["affectsEligibility"])
        self.assertTrue(cell["rankingEligibility"]["active"])

    def test_metric_ineligible_run_does_not_change_displayed_metric(self) -> None:
        ineligible = contribution(1, "Alice", primary_value=1)
        ineligible["validation"]["metricEligibility"]["decode_tokens_per_second@1"] = {
            "eligible": False,
            "eligibleMeasuredAttempts": 0,
            "reasonCodes": ["synthetic_test_ineligible"],
        }
        eligible = contribution(2, "Bob", primary_value=20)
        cell = aggregate_contributions([ineligible, eligible])[0]
        self.assertEqual(cell["summary"]["medianDecodeTokensPerSecond"], 20)
        self.assertEqual(cell["primaryMetric"]["value"], 20)
        self.assertEqual(cell["community"]["eligibleContributorCount"], 1)
        self.assertEqual(cell["community"]["status"], "single-contributor")

    def test_pr_author_must_match_declared_github_handle_case_insensitively(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "submission.json"
            path.write_text(json.dumps({"contributor": {"githubHandle": "Alice"}}))
            self.assertEqual(validate_contributor([path], "alice"), [])
            self.assertTrue(validate_contributor([path], "bob"))

    def test_site_reads_live_community_dataset(self) -> None:
        app = (ROOT / "site/app.js").read_text()
        self.assertIn("results/suite-b-power-community/normalized-results.json", app)


if __name__ == "__main__":
    unittest.main()
