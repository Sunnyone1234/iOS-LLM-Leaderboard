from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PublicSurfaceTests(unittest.TestCase):
    def test_homepage_is_short_and_keeps_complete_suite_map(self) -> None:
        readme = (ROOT / "README.md").read_text()
        self.assertLessEqual(len(readme.splitlines()), 180)
        for suite in ("Suite A", "Suite B", "Suite C", "Suite D", "Suite E"):
            self.assertIn(suite, readme)
        self.assertIn("Build Research", readme)
        self.assertIn("contributor-kit/power-1.1-quickstart.md", readme)

    def test_website_points_to_current_public_method_and_contribution(self) -> None:
        index = (ROOT / "index.html").read_text()
        app = (ROOT / "site/app.js").read_text()
        self.assertIn('href="docs/power.md"', index)
        self.assertIn("contributor-kit/power-1.1-quickstart.md", index)
        self.assertIn("contributor-kit/power-1.1-quickstart.md", app)
        self.assertNotIn("contributor-kit/power-1.0-quickstart.md", index)
        self.assertNotIn("contributor-kit/power-1.0-quickstart.md", app)

    def test_current_contributor_surface_does_not_claim_power_1_0_is_active(self) -> None:
        paths = (
            ROOT / "README.md",
            ROOT / "CONTRIBUTING.md",
            ROOT / "contributor-kit/README.md",
            ROOT / "submissions/README.md",
            ROOT / "docs/community-contribution-model.md",
        )
        combined = "\n".join(path.read_text() for path in paths)
        self.assertNotIn("Power 1.0 public intake is open", combined)
        self.assertIn("scripts/power.py", combined)

    def test_only_one_workflow_deploys_github_pages(self) -> None:
        workflows = (ROOT / ".github/workflows").glob("*.yml")
        deployers = [
            path.name for path in workflows
            if "actions/deploy-pages" in path.read_text()
        ]
        self.assertEqual(deployers, ["power-community-ranking.yml"])

    def test_root_leaderboard_redirects_to_current_views(self) -> None:
        leaderboard = (ROOT / "results/LEADERBOARD.md").read_text()
        self.assertIn("suite-b-power-1.1/LEADERBOARD.md", leaderboard)
        self.assertIn("suite-b-power-community/LEADERBOARD.md", leaderboard)
        self.assertNotIn("No eligible non-placeholder results", leaderboard)


if __name__ == "__main__":
    unittest.main()
