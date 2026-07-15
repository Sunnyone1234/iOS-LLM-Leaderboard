from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from scripts.generate_suite_b_power_1_1_release import DEFAULT_ADOPTION
from scripts.generate_suite_b_power_1_1_release import DEFAULT_OUTPUT
from scripts.generate_suite_b_power_1_1_release import DEFAULT_RELEASE
from scripts.generate_suite_b_power_1_1_release import build_dataset
from scripts.generate_suite_b_power_1_1_release import load_json
from scripts.generate_suite_b_power_1_1_release import verify_activation
from scripts.generate_suite_b_power_1_1_release import verify_entries
from scripts.generate_suite_b_power_1_1_release import write_outputs


class PowerOneOneReleaseGenerationTests(unittest.TestCase):
    def test_candidate_preserves_rc_identity_and_disables_public_ranks(self) -> None:
        dataset, adoption = build_dataset()

        self.assertEqual(dataset["benchmarkRelease"]["version"], "1.1.0")
        self.assertEqual(dataset["sourceEvidenceRelease"]["version"], "1.1.0-rc.1")
        self.assertEqual(dataset["resultCount"], 6)
        self.assertEqual(dataset["performanceEligibleResultCount"], 6)
        self.assertEqual(dataset["recommendationEligibleResultCount"], 5)
        self.assertEqual(dataset["activeRankedResultCount"], 0)
        self.assertFalse(dataset["publication"]["active"])
        self.assertEqual(adoption["decision"]["status"], "final-review-pending")
        for row in dataset["results"]:
            self.assertEqual(row["sourceEvidenceRelease"]["version"], "1.1.0-rc.1")
            self.assertTrue(row["evidence"]["sourceResultUnmodified"])
            self.assertEqual(row["evidence"]["level"], "unreviewed")
            self.assertFalse(row["rankingEligibility"]["active"])
            self.assertIsNone(row["rankingEligibility"]["performanceRank"])

    def test_behavior_not_verified_only_blocks_recommendation(self) -> None:
        dataset, _ = build_dataset()
        row = next(
            item
            for item in dataset["results"]
            if item["resultID"] == "21B5F28F-DA9C-4381-87BA-DBFFEB1D8A84"
        )

        self.assertTrue(row["rankingEligibility"]["measuredPerformance"]["eligible"])
        self.assertFalse(row["rankingEligibility"]["recommendation"]["eligible"])
        self.assertEqual(row["behaviorConformance"]["status"], "not_verified")

    def test_generated_candidate_outputs_are_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "power"
            write_outputs(output, DEFAULT_RELEASE, DEFAULT_ADOPTION)
            for name in (
                "normalized-results.json",
                "LEADERBOARD.md",
                "RELEASE-NOTES.md",
                "README.md",
                "SHA256SUMS",
            ):
                self.assertEqual(
                    (output / name).read_bytes(),
                    (DEFAULT_OUTPUT / name).read_bytes(),
                    name,
                )

    def test_tampered_entry_is_rejected(self) -> None:
        adoption = copy.deepcopy(load_json(DEFAULT_ADOPTION))
        adoption["entries"][0]["resultID"] = "99999999-9999-4999-8999-999999999999"

        with self.assertRaisesRegex(ValueError, "result ID mismatch"):
            verify_entries(adoption)

    def test_activation_requires_confirmed_declarations(self) -> None:
        release = copy.deepcopy(load_json(DEFAULT_RELEASE))
        adoption = load_json(DEFAULT_ADOPTION)
        release.update(
            {
                "officialResultEligible": True,
                "rankingAuthorized": True,
                "publicationAuthorized": True,
                "tagAuthorized": True,
                "status": "published",
            }
        )

        with self.assertRaisesRegex(ValueError, "adoption is not approved"):
            verify_activation(release, adoption)


if __name__ == "__main__":
    unittest.main()
