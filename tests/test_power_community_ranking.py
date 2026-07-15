from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.generate_power_community_ranking import aggregate_contributions
from scripts.generate_power_community_ranking import build_dataset
from scripts.generate_power_community_ranking import current_display_cells
from scripts.generate_power_community_ranking import load_current_community_contributions
from scripts.generate_power_community_ranking import make_contribution
from scripts.generate_power_community_ranking import os_minor_family
from scripts.generate_power_community_ranking import render_leaderboard
from scripts.validate_power_pr_contributor import validate_contributor
from scripts.power import create_package
from tests.test_suite_b_power_result import valid_result


ROOT = Path(__file__).resolve().parents[1]


def contribution(
    number: int,
    contributor: str,
    *,
    workload: str = "b-pipe-001-sustained-generation",
    runtime_version: str = "1.0",
    app_version: str = "1.0",
    app_build: str = "1",
    system_version: str = "26.5",
    system_build: str = "23F1",
    primary_value: float | None = None,
    raw_sha256: str | None = None,
) -> dict:
    result = copy.deepcopy(valid_result(workload))
    result["resultID"] = f"{number:08x}-1111-4111-8111-{number:012x}"
    result["execution"]["sessionID"] = f"{number:08x}-2222-4222-8222-{number:012x}"
    result["createdAt"] = f"2026-07-13T12:{number:02d}:00Z"
    result["runtime"]["version"] = runtime_version
    result["execution"]["appVersion"] = app_version
    result["execution"]["appBuild"] = app_build
    result["device"]["systemVersion"] = system_version
    result["device"]["systemBuild"] = system_build
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
        self.assertEqual(dataset["communityResultCount"], 22)
        self.assertEqual(dataset["cellCount"], 28)
        self.assertEqual(dataset["activeRankedCellCount"], 19)
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

    def test_current_display_combines_patch_releases_and_prefers_newest_app(self) -> None:
        cells = aggregate_contributions([
            contribution(
                1,
                "Alice",
                app_version="0.8.0",
                app_build="10",
                system_version="26.5",
                system_build="23F80",
                primary_value=20,
            ),
            contribution(
                2,
                "Alice",
                app_version="0.10.1",
                app_build="13",
                system_version="26.5.2",
                system_build="23F84",
                primary_value=18,
            ),
        ])
        current = current_display_cells(cells)
        self.assertEqual(len(cells), 2)
        self.assertEqual(len(current), 1)
        self.assertEqual(current[0]["configuration"]["device"]["appVersion"], "0.10.1")
        self.assertEqual(current[0]["configuration"]["device"]["systemVersion"], "26.5.2")

    def test_current_display_keeps_different_ios_minor_families_separate(self) -> None:
        cells = aggregate_contributions([
            contribution(1, "Alice", system_version="26.1", primary_value=20),
            contribution(2, "Alice", system_version="26.5", primary_value=18),
        ])
        self.assertEqual(len(current_display_cells(cells)), 2)
        self.assertEqual(os_minor_family("26.5.2"), "26.5")

    def test_current_display_does_not_fall_back_to_old_ranked_cell(self) -> None:
        old = contribution(
            1,
            "Alice",
            app_version="0.8.0",
            app_build="10",
            system_version="26.5",
            primary_value=20,
        )
        current = contribution(
            2,
            "Alice",
            app_version="0.10.1",
            app_build="13",
            system_version="26.5.2",
            primary_value=18,
        )
        current["validation"]["metricEligibility"]["decode_tokens_per_second@1"] = {
            "eligible": False,
            "eligibleMeasuredAttempts": 0,
            "reasonCodes": ["synthetic_test_ineligible"],
        }
        selected = current_display_cells(aggregate_contributions([old, current]))
        self.assertEqual(len(selected), 1)
        self.assertFalse(selected[0]["rankingEligibility"]["active"])
        self.assertEqual(selected[0]["configuration"]["device"]["appVersion"], "0.10.1")

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

    def test_assisted_current_submission_is_evidence_but_not_ranked(self) -> None:
        fixture = next(
            (ROOT / "results/suite-b-power-1.1.0-rc.1/device-verification/raw").glob(
                "*b-ux-001*21b5f28f.json"
            )
        )
        with tempfile.TemporaryDirectory() as temporary:
            intake = Path(temporary)
            create_package(
                fixture,
                intake,
                "Alice",
                declarations_accepted=True,
                thermal_assistance="deliberate-cooling",
                submission_id="11111111-2222-4333-8444-555555555555",
                created_at="2026-07-15T16:00:00Z",
            )
            contribution_item = load_current_community_contributions(intake)[0]
            self.assertFalse(contribution_item["ordinaryLiveRankingAllowed"])
            cell = aggregate_contributions([contribution_item])[0]
            self.assertEqual(cell["community"]["runCount"], 1)
            self.assertFalse(cell["rankingEligibility"]["active"])

    def test_pr_author_must_match_declared_github_handle_case_insensitively(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "submission.json"
            path.write_text(json.dumps({"contributor": {"githubHandle": "Alice"}}))
            self.assertEqual(validate_contributor([path], "alice"), [])
            self.assertTrue(validate_contributor([path], "bob"))

    def test_site_reads_live_community_dataset(self) -> None:
        app = (ROOT / "site/app.js").read_text()
        self.assertIn("results/suite-b-power-community/normalized-results.json", app)
        self.assertIn("results/suite-b-power-1.1/normalized-results.json", app)
        self.assertIn("currentDisplayKey", app)
        self.assertIn("osMinorFamily", app)
        self.assertIn("No metric-eligible result", app)

    def test_generated_leaderboard_uses_current_display_without_deleting_history(self) -> None:
        dataset = build_dataset()
        rendered = render_leaderboard(dataset)
        self.assertIn("Current display: 11 model configurations", rendered)
        self.assertEqual(rendered.count("| Qwen3 1.7B | 4-bit |"), 2)
        self.assertIn("Current configurations without a rank", rendered)
        self.assertIn("Exact patch builds and older App baselines remain", rendered)
        self.assertEqual(
            (ROOT / "results/suite-b-power-community/LEADERBOARD.md").read_text(),
            rendered,
        )


if __name__ == "__main__":
    unittest.main()
