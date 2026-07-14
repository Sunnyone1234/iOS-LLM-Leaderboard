from __future__ import annotations

import unittest
from pathlib import Path

from scripts.generate_power_community_ranking import build_dataset
from scripts.generate_power_community_ranking import render_coverage


ROOT = Path(__file__).resolve().parents[1]


class CommunityOnboardingTests(unittest.TestCase):
    def test_coverage_report_is_a_deterministic_live_derivative(self) -> None:
        expected = render_coverage(build_dataset())
        actual = (
            ROOT / "results/suite-b-power-community/COVERAGE.md"
        ).read_text()
        self.assertEqual(actual, expected)
        self.assertIn("Exact comparison cells: 28", actual)
        self.assertIn("Reproduced cells: 0", actual)
        self.assertIn("does not create placeholder devices", actual)

    def test_site_exposes_contribution_and_coverage_entries(self) -> None:
        index = (ROOT / "index.html").read_text()
        app = (ROOT / "site/app.js").read_text()
        self.assertIn("contributor-kit/power-1.0-quickstart.md", index)
        self.assertIn("github.com/YizeSun/iOS-LLM-Leaderboard/blob/main", index)
        self.assertIn('data-mode="coverage"', index)
        self.assertIn("buildCoverageRows", app)
        self.assertIn("eligibleContributorCount", app)
        self.assertIn("COVERAGE.md", app)

    def test_quickstart_pins_app_identity_and_raw_export(self) -> None:
        guide = (ROOT / "contributor-kit/power-1.0-quickstart.md").read_text()
        self.assertIn("2f105ff463bc9b281b19655ba711b1ca7dee8759", guide)
        self.assertIn("Export Raw JSON", guide)
        self.assertIn("create_suite_b_power_submission.py", guide)
        self.assertIn("validate_suite_b_power_submission.py", guide)
        self.assertIn("contributor.githubHandle", guide)
        self.assertIn("gh pr create --web", guide)


if __name__ == "__main__":
    unittest.main()
