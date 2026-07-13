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

    def test_catalog_contains_four_unique_unmeasured_candidates(self) -> None:
        models = self.catalog["models"]
        self.assertEqual([model["recommendedPriority"] for model in models], [1, 2, 3, 4])
        self.assertEqual(len({model["artifactID"] for model in models}), 4)
        self.assertTrue(all(model["physicalDeviceEvidenceStatus"] == "untested" for model in models))
        self.assertTrue(all(model["runtimeRegistryStatus"] == "registered-not-device-verified" for model in models))
        self.assertTrue(all(re.fullmatch(r"[0-9a-f]{40}", model["artifactRevision"]) for model in models))
        self.assertTrue(all(model["artifactRevision"] in model["sourceURL"] for model in models))
        for forbidden in ("ttft", "decodeTokensPerSecond", "prefillTokensPerSecond", "rank", "score"):
            self.assertNotIn(forbidden, CATALOG_PATH.read_text())

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
        self.assertEqual(project.count("MARKETING_VERSION = 0.9.0;"), 2)
        self.assertEqual(project.count("CURRENT_PROJECT_VERSION = 11;"), 2)

    def test_untested_candidates_are_absent_from_all_ranking_data(self) -> None:
        candidate_ids = {model["artifactID"] for model in self.catalog["models"]}
        for relative in (
            "results/suite-b-power-1.0/normalized-results.json",
            "results/suite-b-power-community/normalized-results.json",
        ):
            data = json.loads((ROOT / relative).read_text())
            ranked_ids = {
                row["configuration"]["model"]["artifactID"]
                for row in data["results"]
            }
            self.assertTrue(candidate_ids.isdisjoint(ranked_ids))

    def test_site_exposes_a_separate_non_ranking_catalog(self) -> None:
        index = (ROOT / "index.html").read_text()
        app = (ROOT / "site" / "app.js").read_text()
        self.assertIn('data-mode="catalog"', index)
        self.assertIn("models/power-test-catalog.json", app)
        self.assertIn("These are not rankings", app)
        self.assertIn("No performance claims", app)

    def test_candidate_source_is_null_only_until_the_feature_commit_is_pinned(self) -> None:
        source_commit = self.catalog["referenceApp"]["sourceCommit"]
        self.assertTrue(
            source_commit is None or re.fullmatch(r"[0-9a-f]{40}", source_commit)
        )


if __name__ == "__main__":
    unittest.main()
