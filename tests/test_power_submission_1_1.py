from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.power import create_package
from scripts.validate_suite_b_power_1_1_submission import validate_package


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = (
    ROOT
    / "results/suite-b-power-1.1.0-rc.1/device-verification/raw/"
    "2026-07-15T15-25-48Z_b-ux-001-short-interaction_"
    "mlx-community-qwen3-0.6b-4bit_iphone15-3_21b5f28f.json"
)


class PowerSubmission11Tests(unittest.TestCase):
    def create(self, root: Path, *, thermal: str = "none") -> Path:
        return create_package(
            FIXTURE,
            root,
            "ExampleContributor",
            declarations_accepted=True,
            thermal_assistance=thermal,
            submission_id="11111111-2222-4333-8444-555555555555",
            created_at="2026-07-15T16:00:00Z",
        )

    def test_current_package_preserves_raw_bytes_and_validates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = self.create(Path(temporary))
            self.assertEqual((package / "result.json").read_bytes(), FIXTURE.read_bytes())
            manifest = json.loads((package / "submission.json").read_text())
            self.assertEqual(manifest["benchmarkRelease"]["version"], "1.1.0")
            self.assertEqual(
                manifest["result"]["schemaVersion"],
                "suite-b-power-result-1.1.0-rc.1",
            )
            report = validate_package(package)
            self.assertNotEqual(report["overallStatus"], "invalid")
            self.assertTrue(report["ordinaryLiveRankingEligibility"]["eligible"])
            self.assertTrue(
                report["powerResultValidation"]["performanceRankingEligibility"]["eligible"]
            )

    def test_assisted_environment_is_retained_but_not_ordinary_ranked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = self.create(Path(temporary), thermal="deliberate-cooling")
            report = validate_package(package)
            self.assertNotEqual(report["overallStatus"], "invalid")
            self.assertFalse(report["ordinaryLiveRankingEligibility"]["eligible"])
            self.assertIn(
                "thermal_assistance_not_unassisted",
                report["ordinaryLiveRankingEligibility"]["reasonCodes"],
            )

    def test_declarations_must_be_explicitly_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "accept-declarations"):
                create_package(
                    FIXTURE,
                    Path(temporary),
                    "ExampleContributor",
                    declarations_accepted=False,
                )


if __name__ == "__main__":
    unittest.main()
