from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "models" / "power-test-catalog.json"
SWIFT_PROFILE_PATH = ROOT / "ios-app" / "BenchmarkApp" / "PilotPlan.swift"


class PowerModelCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = json.loads(CATALOG_PATH.read_text())

    def test_catalog_contains_four_unique_community_tested_models(self) -> None:
        models = self.catalog["models"]
        self.assertEqual([model["recommendedPriority"] for model in models], [1, 2, 3, 4])
        self.assertEqual(len({model["artifactID"] for model in models}), 4)
        self.assertTrue(
            all(
                model["physicalDeviceEvidenceStatus"]
                == "community-submitted-single-contributor"
                for model in models
            )
        )
        self.assertTrue(
            all(model["runtimeRegistryStatus"] == "registered-device-tested" for model in models)
        )
        self.assertTrue(all(re.fullmatch(r"[0-9a-f]{40}", model["artifactRevision"]) for model in models))
        self.assertTrue(all(model["artifactRevision"] in model["sourceURL"] for model in models))
        catalog_keys = {
            key.casefold()
            for entry in self.catalog["models"] + self.catalog["openModelWatchlist"]
            for key in entry
        }
        for forbidden in (
            "ttft",
            "decodetokenspersecond",
            "prefilltokenspersecond",
            "rank",
            "score",
        ):
            self.assertNotIn(forbidden, catalog_keys)

    def test_catalog_contains_the_eleven_requested_public_weight_models_as_watchlist_only(self) -> None:
        watchlist = self.catalog["openModelWatchlist"]
        self.assertEqual(
            [model["officialModelID"] for model in watchlist],
            [
                "zai-org/GLM-5.2",
                "zai-org/GLM-5.1",
                "moonshotai/Kimi-K2.7-Code",
                "deepseek-ai/DeepSeek-V4-Pro",
                "moonshotai/Kimi-K2.6",
                "XiaomiMiMo/MiMo-V2.5-Pro",
                "MiniMaxAI/MiniMax-M3",
                "deepseek-ai/DeepSeek-V4-Flash",
                "MiniMaxAI/MiniMax-M2.7",
                "google/gemma-4-31B-it",
                "nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-NVFP4",
            ],
        )
        self.assertEqual(len({model["officialModelID"] for model in watchlist}), 11)
        self.assertTrue(all(model["licenseIdentifier"] for model in watchlist))
        self.assertTrue(all(model["appEligibility"] == "not-app-testable" for model in watchlist))
        self.assertTrue(all(model["officialModelID"] in model["sourceURL"] for model in watchlist))
        self.assertTrue(all(model["licenseSourceURL"].startswith("https://") for model in watchlist))
        self.assertFalse(self.catalog["openModelWatchlistPolicy"]["appSelectable"])
        self.assertFalse(self.catalog["openModelWatchlistPolicy"]["rankingEligible"])
        self.assertIn("OSI", self.catalog["openModelWatchlistPolicy"]["eligibilityDefinition"])

    def test_catalog_runtime_matches_the_locked_app_dependency(self) -> None:
        package = json.loads(
            (
                ROOT
                / "ios-app"
                / "BenchmarkApp.xcodeproj"
                / "project.xcworkspace"
                / "xcshareddata"
                / "swiftpm"
                / "Package.resolved"
            ).read_text()
        )
        pin = next(item for item in package["pins"] if item["identity"] == "mlx-swift-lm")
        self.assertEqual(self.catalog["runtime"]["version"], pin["state"]["version"])
        self.assertEqual(self.catalog["runtime"]["revision"], pin["state"]["revision"])

    def test_every_catalog_artifact_is_selectable_in_the_candidate_app(self) -> None:
        swift = SWIFT_PROFILE_PATH.read_text()
        for model in self.catalog["models"]:
            self.assertIn(f'artifactId: "{model["artifactID"]}"', swift)
            self.assertIn(f'artifactRevision: "{model["artifactRevision"]}"', swift)
        project = (ROOT / "ios-app" / "BenchmarkApp.xcodeproj" / "project.pbxproj").read_text()
        self.assertEqual(project.count("MARKETING_VERSION = 0.14.0;"), 2)
        self.assertEqual(project.count("CURRENT_PROJECT_VERSION = 17;"), 2)

    def test_every_community_app_profile_has_exact_accepted_evidence(self) -> None:
        swift = SWIFT_PROFILE_PATH.read_text()
        selectable_pairs = re.findall(
            r'artifactId: "([^"]+)",\n\s+artifactRevision: "([0-9a-f]{40})"',
            swift,
        )
        self.assertEqual(len(selectable_pairs), 11)

        community = json.loads(
            (ROOT / "results/suite-b-power-community/normalized-results.json").read_text()
        )
        accepted_pairs = {
            (
                row["configuration"]["model"]["artifactID"],
                row["configuration"]["model"]["artifactRevision"],
            )
            for row in community["results"]
        }
        self.assertTrue(set(selectable_pairs[3:]).issubset(accepted_pairs))

    def test_watchlist_models_are_not_misrepresented_as_app_options(self) -> None:
        swift = SWIFT_PROFILE_PATH.read_text()
        for model in self.catalog["openModelWatchlist"]:
            self.assertNotIn(model["officialModelID"], swift)

    def test_catalog_evidence_matches_rankings_and_watchlist_stays_absent(self) -> None:
        app_ready_ids = {model["artifactID"] for model in self.catalog["models"]}
        watchlist_ids = {
            model["officialModelID"] for model in self.catalog["openModelWatchlist"]
        }
        official = json.loads(
            (ROOT / "results/suite-b-power-1.1/normalized-results.json").read_text()
        )
        community = json.loads(
            (ROOT / "results/suite-b-power-community/normalized-results.json").read_text()
        )
        official_ids = {
            row["configuration"]["model"]["artifactID"]
            for row in official["results"]
        }
        community_ids = {
            row["configuration"]["model"]["artifactID"]
            for row in community["results"]
        }
        self.assertTrue(app_ready_ids.isdisjoint(official_ids))
        self.assertTrue(app_ready_ids.issubset(community_ids))
        self.assertTrue(watchlist_ids.isdisjoint(official_ids | community_ids))

    def test_site_exposes_a_separate_non_ranking_catalog(self) -> None:
        index = (ROOT / "index.html").read_text()
        app = (ROOT / "site" / "app.js").read_text()
        self.assertIn('data-mode="catalog"', index)
        self.assertIn("models/power-test-catalog.json", app)
        self.assertIn("These are not rankings", app)
        self.assertIn("No performance claims", app)
        self.assertIn("Not App-ready", app)
        self.assertIn("openModelWatchlist", app)

    def test_candidate_source_and_contributor_guide_are_pinned(self) -> None:
        source_commit = "9ad1e4507bdc8e5d2a3f75387f3af86675bf69ab"
        self.assertEqual(self.catalog["referenceApp"]["sourceCommit"], source_commit)
        guide = (ROOT / "contributor-kit" / "test-recommended-model.md").read_text()
        self.assertIn(source_commit, guide)
        self.assertIn("Export Raw JSON", guide)
        self.assertIn("create_suite_b_power_submission.py", guide)
        self.assertIn("do not manufacture JSON", guide)


if __name__ == "__main__":
    unittest.main()
