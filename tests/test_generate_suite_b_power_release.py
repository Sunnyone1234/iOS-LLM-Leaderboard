from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.generate_suite_b_power_release import DEFAULT_ADOPTION
from scripts.generate_suite_b_power_release import DEFAULT_OUTPUT
from scripts.generate_suite_b_power_release import DEFAULT_RELEASE
from scripts.generate_suite_b_power_release import build_dataset
from scripts.generate_suite_b_power_release import load_json
from scripts.generate_suite_b_power_release import render_leaderboard
from scripts.generate_suite_b_power_release import render_release_notes
from scripts.generate_suite_b_power_release import verify_activation
from scripts.generate_suite_b_power_release import verify_entries
from scripts.generate_suite_b_power_release import write_outputs


ROOT = Path(__file__).resolve().parents[1]


class PowerReleaseGenerationTests(unittest.TestCase):
    def test_no_rerun_adoption_preserves_source_identity(self) -> None:
        dataset, adoption = build_dataset(DEFAULT_RELEASE, DEFAULT_ADOPTION)
        self.assertEqual(dataset["benchmarkRelease"]["version"], "1.0.0")
        self.assertEqual(dataset["sourceEvidenceRelease"]["version"], "1.0.0-rc.1")
        self.assertEqual(dataset["resultCount"], 6)
        self.assertEqual(dataset["candidateRankedResultCount"], 5)
        self.assertEqual(dataset["activeRankedResultCount"], 5)
        self.assertEqual(adoption["decision"]["method"], "exact-release-candidate-adoption-without-rerun")
        self.assertFalse(adoption["decision"]["referenceAppChanged"])
        self.assertFalse(adoption["decision"]["protocolSemanticsChanged"])
        self.assertFalse(adoption["decision"]["newExecutionRequired"])
        self.assertFalse(adoption["decision"]["rawEvidenceMutationAllowed"])
        for row in dataset["results"]:
            self.assertEqual(row["sourceEvidenceRelease"]["version"], "1.0.0-rc.1")
            self.assertTrue(row["evidence"]["sourceResultUnmodified"])
            self.assertEqual(row["evidence"]["level"], "maintainer-reference")
            self.assertEqual(row["evidence"]["proposedLevel"], "maintainer-reference")
            self.assertEqual(
                row["rankingEligibility"]["active"],
                row["rankingEligibility"]["candidateEligible"],
            )

    def test_ineligible_short_interaction_is_retained_not_ranked(self) -> None:
        dataset, _ = build_dataset(DEFAULT_RELEASE, DEFAULT_ADOPTION)
        row = next(
            item for item in dataset["results"]
            if item["resultID"] == "2C2F23B4-58FA-460E-9481-EB2D3837FDE2"
        )
        self.assertEqual(row["workload"]["id"], "b-ux-001-short-interaction")
        self.assertFalse(row["primaryMetric"]["eligible"])
        self.assertFalse(row["rankingEligibility"]["candidateEligible"])
        self.assertEqual(row["evidence"]["adoptionStatus"], "retained-ineligible-evidence")

    def test_generated_release_outputs_are_reproducible(self) -> None:
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
                self.assertEqual((output / name).read_bytes(), (DEFAULT_OUTPUT / name).read_bytes(), name)

    def test_tampered_adoption_identity_is_rejected(self) -> None:
        adoption = copy.deepcopy(load_json(DEFAULT_ADOPTION))
        adoption["entries"][0]["resultID"] = "99999999-9999-4999-8999-999999999999"
        with self.assertRaisesRegex(ValueError, "result ID mismatch"):
            verify_entries(adoption)

    def test_active_release_requires_all_seven_declarations(self) -> None:
        release = load_json(DEFAULT_RELEASE)
        adoption = copy.deepcopy(load_json(DEFAULT_ADOPTION))
        adoption["contributor"]["declarations"]["containsNoPersonalData"] = False
        with self.assertRaisesRegex(ValueError, "all seven contributor declarations"):
            verify_activation(release, adoption)

    def test_approved_package_renders_as_official_not_candidate(self) -> None:
        dataset, adoption = build_dataset(DEFAULT_RELEASE, DEFAULT_ADOPTION)
        dataset["publication"].update(
            {
                "officialResultEligible": True,
                "rankingAuthorized": True,
                "publicationAuthorized": True,
            }
        )
        dataset["activeRankedResultCount"] = 5
        adoption["contributor"]["declarationsStatus"] = "confirmed"
        self.assertEqual(render_leaderboard(dataset).splitlines()[0], "# Power Benchmark 1.0")
        notes = render_release_notes(dataset, adoption)
        self.assertIn("published Power Benchmark 1.0 package", notes)
        self.assertNotIn("Required final decisions", notes)

    def test_site_reads_power_1_data_and_defers_ship(self) -> None:
        app = (ROOT / "site/app.js").read_text()
        page = (ROOT / "index.html").read_text()
        self.assertIn('results/suite-b-power-1.0/normalized-results.json', app)
        self.assertNotIn("suite-b-pilot-v0.1/normalized-results.json", app)
        self.assertNotIn('data-mode="ship"', page)
        self.assertIn('<span id="release-label">Power 1.0</span>', page)


if __name__ == "__main__":
    unittest.main()
