from __future__ import annotations

import re
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
        self.assertIn("contributor-kit/power.md", readme)
        self.assertIn("Power 1.1 evidence", readme)

    def test_website_points_to_current_public_method_and_contribution(self) -> None:
        index = (ROOT / "index.html").read_text()
        app = (ROOT / "site/app.js").read_text()
        self.assertIn('href="docs/power.md"', index)
        self.assertIn("contributor-kit/power.md", index)
        self.assertIn("contributor-kit/power.md", app)
        self.assertIn(
            "results/power/text-generation-performance/2.0.0/ranking.json",
            app,
        )
        self.assertNotIn("contributor-kit/power-1.0-quickstart.md", index)
        self.assertNotIn("contributor-kit/power-1.0-quickstart.md", app)

    def test_current_contributor_surface_does_not_claim_power_1_0_is_active(self) -> None:
        paths = (
            ROOT / "README.md",
            ROOT / "CONTRIBUTING.md",
            ROOT / "contributor-kit/README.md",
            ROOT / "submissions/README.md",
            ROOT / "docs/power.md",
            ROOT / "docs/project-vision.md",
            ROOT / "products/README.md",
        )
        combined = "\n".join(path.read_text() for path in paths)
        self.assertNotIn("Power 1.0 public intake is open", combined)
        self.assertNotIn("## Current Power 1.1 intake", combined)
        self.assertNotIn("Power 2.0 is being built", combined)
        self.assertNotIn(
            "The current Power release is\n"
            "[Power Benchmark 1.1]",
            combined,
        )
        self.assertIn("scripts/power", combined)
        self.assertNotIn("python3 scripts/power.py", combined)
        self.assertIn(
            "submissions/power/text-generation-performance/2.0.0/draft/",
            combined,
        )

    def test_power_and_ship_are_separate_public_products(self) -> None:
        paths = (
            ROOT / "README.md",
            ROOT / "docs/project-vision.md",
            ROOT / "docs/product-architecture.md",
            ROOT / "docs/project-structure.md",
            ROOT / "methodology/overview.md",
            ROOT / "methodology/benchmark-suites.md",
        )
        combined = "\n".join(path.read_text() for path in paths)
        self.assertNotIn("Phase 1 public product is **Power + Ship**", combined)
        self.assertNotIn("Product Phase 1 is Power + Ship", combined)
        self.assertIn("Power does not contain Ship", combined)
        self.assertIn(
            "A Power run does not produce a Ship result",
            combined,
        )
        self.assertNotIn("Power + Ship", combined)

        diagram = (
            ROOT / "docs/assets/readme/power-ship-flow-v2.svg"
        ).read_text()
        self.assertIn(
            "One Benchmark App run produces one Power result",
            diagram,
        )
        self.assertIn("stroke-dasharray", diagram)

    def test_repository_architecture_records_active_power_2(self) -> None:
        docs_index = (ROOT / "docs/README.md").read_text()
        blueprint = (ROOT / "docs/repository-architecture.md").read_text()
        structure = (ROOT / "docs/project-structure.md").read_text()

        self.assertIn("repository-architecture.md", docs_index)
        self.assertIn("Status: architecture implemented", blueprint)
        self.assertIn(
            "Benchmark Cell = Program Version × Target Profile Version",
            blueprint,
        )
        self.assertIn("Power 2 active", blueprint)
        self.assertIn("public intake is open", blueprint)
        self.assertIn("No backward-compatibility layer", blueprint)
        self.assertIn(
            "There are no compatibility readers, schema adapters, policy adapters",
            blueprint,
        )
        self.assertIn(
            "Every active result was newly generated under Power 2.0",
            blueprint,
        )
        self.assertIn(
            "`current.json` is the only active public Power pointer",
            structure,
        )

    def test_only_one_workflow_deploys_github_pages(self) -> None:
        workflows = (ROOT / ".github/workflows").glob("*.yml")
        deployers = [
            path.name for path in workflows
            if "actions/deploy-pages" in path.read_text()
        ]
        self.assertEqual(deployers, ["power-community-ranking.yml"])

    def test_active_workflows_do_not_execute_historical_power(self) -> None:
        workflows = tuple(
            sorted((ROOT / ".github/workflows").glob("*.yml"))
        )
        self.assertNotIn(
            "suite-b-submissions.yml",
            {path.name for path in workflows},
        )
        combined = "\n".join(path.read_text() for path in workflows)
        for retired_surface in (
            "scripts/power.py",
            "validate_suite_b_power",
            "generate_power_community_ranking.py",
            "submissions/suite-b/power-1.",
            "results/suite-b-power-1.1",
            "results/suite-b-power-community",
        ):
            with self.subTest(retired_surface=retired_surface):
                self.assertNotIn(retired_surface, combined)

    def test_active_power_surfaces_do_not_read_the_archive(self) -> None:
        paths = [
            ROOT / "scripts/power",
            ROOT / "index.html",
            ROOT / "site/app.js",
            ROOT / "products/power/current.json",
        ]
        paths.extend(
            sorted((ROOT / ".github/workflows").glob("*.yml"))
        )
        combined = "\n".join(path.read_text() for path in paths)
        for retired_path in (
            "scripts/power.py",
            "contributor-kit/power-1.1-quickstart.md",
            "submissions/suite-b/power-1.1.0",
            "results/suite-b-power-1.1",
            "suite-b-power-1.1.0",
        ):
            with self.subTest(retired_path=retired_path):
                self.assertNotIn(retired_path, combined)

    def test_root_leaderboard_redirects_to_current_views(self) -> None:
        leaderboard = (ROOT / "results/LEADERBOARD.md").read_text()
        self.assertIn(
            "power/text-generation-performance/2.0.0/ranking.json",
            leaderboard,
        )
        self.assertIn("suite-b-power-1.1/LEADERBOARD.md", leaderboard)
        self.assertIn("suite-b-power-community/LEADERBOARD.md", leaderboard)
        self.assertIn("static official snapshot", leaderboard)
        self.assertIn("static community snapshot", leaderboard)
        self.assertNotIn("No eligible non-placeholder results", leaderboard)

    def test_power_table_numbers_follow_the_active_sort(self) -> None:
        app = (ROOT / "site/app.js").read_text()
        self.assertIn('["rank", "#"]', app)
        self.assertIn("const rows = sortRows(filterPowerRows(powerRows()));", app)
        self.assertIn("rows.map((row, index)", app)
        self.assertIn("${index + 1}", app)

    def test_non_ranked_contributions_remain_machine_visible(self) -> None:
        app = (ROOT / "site/app.js").read_text()
        ranking = (
            ROOT
            / "results/power/text-generation-performance/2.0.0/ranking.json"
        ).read_text()
        self.assertIn('"excluded"', ranking)
        self.assertIn('"excludedContributionCount"', ranking)
        self.assertIn("Ranking JSON", app)

    def test_every_leaderboard_column_has_accessible_help(self) -> None:
        index = (ROOT / "index.html").read_text()
        app = (ROOT / "site/app.js").read_text()
        styles = (ROOT / "site/styles.css").read_text()
        column_keys = set(re.findall(r'\["([^"]+)",\s*(?:"[^"]+"|mode\.unit)\]', app))
        help_start = app.index("const COLUMN_HELP")
        help_end = app.index("\n});", help_start)
        help_block = app[help_start:help_end]
        help_keys = {
            quoted or plain
            for quoted, plain in re.findall(
                r'^\s*(?:"([^"]+)"|([A-Za-z][A-Za-z0-9]*))\s*:',
                help_block,
                re.MULTILINE,
            )
        }
        self.assertEqual(column_keys, help_keys)
        self.assertIn('id="column-tooltip" role="tooltip"', index)
        self.assertIn('aria-describedby="column-tooltip"', app)
        self.assertIn('button.addEventListener("mouseenter"', app)
        self.assertIn('button.addEventListener("focus"', app)
        self.assertIn(".column-help", styles)
        self.assertIn(".column-tooltip", styles)

    def test_power_rows_expose_exact_model_usage(self) -> None:
        app = (ROOT / "site/app.js").read_text()
        recipe = (ROOT / "examples/mlx-swift-power/ExactPowerModel.swift").read_text()
        self.assertIn("Open exact model revision", app)
        self.assertIn("modelRevisionURL", app)
        self.assertIn("Source result SHA-256", app)
        self.assertIn("Runner certificate", app)
        self.assertIn("artifactID: String", recipe)
        self.assertIn("revision: String", recipe)

    def test_model_parameter_size_filter_is_available_across_views(self) -> None:
        index = (ROOT / "index.html").read_text()
        app = (ROOT / "site/app.js").read_text()
        self.assertIn('id="size-filter"', index)
        self.assertIn('value="up-to-1b"', index)
        self.assertIn('value="1b-to-2b"', index)
        self.assertIn('value="2b-to-4b"', index)
        self.assertIn('value="over-4b"', index)
        self.assertIn('value="unknown"', index)
        self.assertIn("function modelParameterBillions(value)", app)
        self.assertIn("function modelSizeBucket(value)", app)
        self.assertIn('state.size === "all"', app)
        self.assertIn('elements.size.addEventListener("change"', app)

    def test_leaderboard_defaults_to_dark_and_preserves_theme_choice(self) -> None:
        index = (ROOT / "index.html").read_text()
        app = (ROOT / "site/app.js").read_text()
        styles = (ROOT / "site/styles.css").read_text()
        self.assertIn('<html lang="en" data-theme="dark">', index)
        self.assertIn('id="theme-select"', index)
        self.assertIn('value="dark"', index)
        self.assertIn('value="light"', index)
        self.assertIn('color-scheme: dark', styles)
        self.assertIn(':root[data-theme="light"]', styles)
        self.assertIn('const THEME_STORAGE_KEY = "ios-llm-leaderboard-theme"', app)
        self.assertIn("function applyTheme(theme, persist = false)", app)
        self.assertIn('elements.theme.addEventListener("change"', app)


if __name__ == "__main__":
    unittest.main()
