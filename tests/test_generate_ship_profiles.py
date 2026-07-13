from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.generate_ship_profiles import DEFAULT_OUTPUT
from scripts.generate_ship_profiles import DEFAULT_POWER
from scripts.generate_ship_profiles import build_dataset
from scripts.generate_ship_profiles import write_outputs


ROOT = Path(__file__).resolve().parents[1]


class ShipProfileGenerationTests(unittest.TestCase):
    def test_profiles_reuse_published_power_without_a_score(self) -> None:
        dataset = build_dataset()
        self.assertEqual(dataset["shipRelease"]["version"], "1.0.0-rc.1")
        self.assertEqual(dataset["sourcePowerRelease"]["version"], "1.0.0")
        self.assertEqual(dataset["profileCount"], 3)
        self.assertFalse(dataset["hasDeploymentScore"])
        self.assertEqual(sum(item["evidence"]["sourceResultCount"] for item in dataset["profiles"]), 6)
        self.assertEqual(sum(item["evidence"]["activePowerResultCount"] for item in dataset["profiles"]), 5)

    def test_unknown_claims_are_not_promoted_to_support(self) -> None:
        dataset = build_dataset()
        required_unknown = {
            "offline-execution",
            "generation-cancellation",
            "bundled-model-distribution",
            "minimum-supported-device",
            "app-store-readiness",
            "privacy-compliance",
        }
        for profile in dataset["profiles"]:
            claims = {item["id"]: item["status"] for item in profile["deploymentClaims"]}
            self.assertTrue(required_unknown.issubset(claims))
            self.assertTrue(all(claims[claim_id] == "unknown" for claim_id in required_unknown))
            self.assertIsNone(profile["observedConstraints"]["minimumSupportedDevice"])

    def test_source_power_data_is_not_mutated(self) -> None:
        source = json.loads(DEFAULT_POWER.read_text())
        before = copy.deepcopy(source)
        build_dataset()
        self.assertEqual(source, before)

    def test_generated_outputs_are_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "ship"
            write_outputs(output)
            for name in ("deployment-profiles.json", "PROFILES.md", "README.md", "SHA256SUMS"):
                self.assertEqual((output / name).read_bytes(), (DEFAULT_OUTPUT / name).read_bytes(), name)

    def test_tampered_power_publication_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "power.json"
            data = json.loads(DEFAULT_POWER.read_text())
            data["publication"]["rankingAuthorized"] = False
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "ranking is not authorized"):
                build_dataset(path)

    def test_recipe_runtime_identity_is_frozen(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "power.json"
            data = json.loads(DEFAULT_POWER.read_text())
            for row in data["results"]:
                row["configuration"]["runtime"]["version"] = "3.31.5"
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "unexpected tested runtime identity"):
                build_dataset(path)

    def test_recipe_uses_all_exact_tested_artifact_revisions(self) -> None:
        recipe = (ROOT / "examples/mlx-swift/PinnedMLXModel.swift").read_text()
        for profile in build_dataset()["profiles"]:
            model = profile["configuration"]["model"]
            self.assertIn(model["artifactID"], recipe)
            self.assertIn(model["artifactRevision"], recipe)
        self.assertIn("useLatest: false", recipe)


if __name__ == "__main__":
    unittest.main()
