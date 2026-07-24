from __future__ import annotations

import unittest
from pathlib import Path

from scripts.generate_power_community_ranking import render_coverage
from scripts.generate_power_community_ranking_1_1_4 import build_dataset


ROOT = Path(__file__).resolve().parents[1]


class CommunityOnboardingTests(unittest.TestCase):
    def test_coverage_report_is_a_deterministic_live_derivative(self) -> None:
        dataset = build_dataset()
        expected = render_coverage(dataset)
        self.assertEqual(render_coverage(build_dataset()), expected)
        self.assertIn(
            f"Exact comparison cells: {dataset['cellCount']}", expected
        )
        self.assertIn(
            f"Reproduced cells: {dataset['reproducedCellCount']}", expected
        )
        self.assertIn("does not create placeholder devices", expected)

    def test_site_exposes_current_contribution_and_evidence_entries(self) -> None:
        index = (ROOT / "index.html").read_text()
        app = (ROOT / "site/app.js").read_text()
        self.assertIn("contributor-kit/power.md", index)
        self.assertIn("github.com/YizeSun/iOS-LLM-Leaderboard/blob/main", index)
        self.assertIn('data-mode="ux"', index)
        self.assertIn('data-mode="pipe"', index)
        self.assertIn('data-mode="ship"', index)
        self.assertIn(
            "results/power/text-generation-performance/2.0.0/ranking.json",
            app,
        )
        self.assertIn("products/power/current.json", app)
        self.assertIn("Power 2 · Public intake open", app)
        self.assertIn("Public intake is open", index)

    def test_quickstart_pins_app_identity_and_raw_export(self) -> None:
        guide = (ROOT / "contributor-kit/power-1.0-quickstart.md").read_text()
        self.assertIn("d7fcff7e27b4c46b1121df8988a0b2fb76d56804", guide)
        self.assertIn("history correction mapping", guide)
        self.assertIn("Export Raw JSON", guide)
        self.assertIn("create_suite_b_power_submission.py", guide)
        self.assertIn("validate_suite_b_power_submission.py", guide)
        self.assertIn("contributor.githubHandle", guide)
        self.assertIn("gh pr create --web", guide)

    def test_recommended_model_path_is_separate_and_source_pinned(self) -> None:
        guide = (ROOT / "contributor-kit/test-recommended-model.md").read_text()
        self.assertIn("9ad1e4507bdc8e5d2a3f75387f3af86675bf69ab", guide)
        self.assertIn("App `0.9.0` build `11`", guide)
        self.assertIn("single-contributor community", guide)
        self.assertIn("not itself a benchmark result", guide)


if __name__ == "__main__":
    unittest.main()
