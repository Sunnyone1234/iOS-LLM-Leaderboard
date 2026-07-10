from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.generate_leaderboard import is_publishable, render
from scripts.validate_result import validate


ROOT = Path(__file__).resolve().parents[1]


def load_fixture(name: str) -> dict:
    return json.loads((ROOT / "results" / name).read_text(encoding="utf-8"))


class ValidateResultTests(unittest.TestCase):
    def test_demo_model_result_is_valid_placeholder(self) -> None:
        self.assertEqual(validate(load_fixture("sample-result.json")), [])

    def test_demo_device_result_is_valid_placeholder(self) -> None:
        self.assertEqual(validate(load_fixture("sample-device-result.json")), [])

    def test_nested_real_result_is_valid(self) -> None:
        result = load_fixture("sample-result.json")
        result["result_id"] = "2026-07-10-suite-a-swift-codegen-001-example"
        result["model"]["model_name"] = "Example Model"
        result["model"]["provider"] = "Example Provider"
        result["execution"]["evaluator"] = "example"
        result["evaluation"]["score"] = 8
        result["evaluation"]["passed"] = True
        result["provenance"]["source"] = "maintainer-run"

        self.assertEqual(validate(result), [])

    def test_missing_nested_field_is_reported(self) -> None:
        result = load_fixture("sample-result.json")
        del result["task"]["task_id"]

        self.assertIn("missing required field: task.task_id", validate(result))

    def test_real_result_cannot_use_null_score(self) -> None:
        result = load_fixture("sample-result.json")
        result["provenance"]["source"] = "manual-submission"

        self.assertIn(
            "required field is null: evaluation.score",
            validate(result),
        )


class LeaderboardTests(unittest.TestCase):
    def test_placeholder_is_not_publishable(self) -> None:
        result = load_fixture("sample-result.json")
        self.assertFalse(is_publishable(result))

    def test_placeholder_is_excluded_from_render(self) -> None:
        rendered = render([load_fixture("sample-result.json")])
        self.assertIn("No eligible non-placeholder results", rendered)
        self.assertNotIn("DemoModel-A", rendered)

    def test_scored_and_measurement_suites_are_separate(self) -> None:
        scored = load_fixture("sample-result.json")
        scored["model"]["model_name"] = "Scored Model"
        scored["evaluation"]["score"] = 8
        scored["evaluation"]["passed"] = True
        scored["provenance"]["source"] = "maintainer-run"

        measured = load_fixture("sample-device-result.json")
        measured["model"]["model_name"] = "Measured Model"
        measured["model"]["quantization"] = "4-bit"
        measured["runtime"].update(
            {
                "runtime_name": "Example Runtime",
                "runtime_version": "1.0",
                "backend": "Example Backend",
                "model_format": "Example Format",
            }
        )
        measured["device"].update(
            {
                "device_name": "Example Device",
                "os_name": "iOS",
                "os_version": "26.0",
            }
        )
        measured["suite_b_measurement"].update(
            {
                "prompt_token_band": "64",
                "output_token_band": "128",
                "warmup_procedure": "one fixed warm-up",
                "measurement_procedure": "five measured runs",
                "measured_run_count": 5,
                "aggregation_method": "median",
                "cold_or_warm_start_state": "warm",
                "timing_boundaries": "submit to first token",
                "failed_or_interrupted_run_handling": "retain all attempts",
            }
        )
        measured["metrics"]["ttft_ms"] = 100
        measured["evaluation"]["score"] = 10
        measured["evaluation"]["passed"] = True
        measured["provenance"]["source"] = "maintainer-run"

        self.assertEqual(validate(scored), [])
        self.assertEqual(validate(measured), [])

        rendered = render([scored, measured])
        self.assertIn("Suite A: Swift Code Generation", rendered)
        self.assertIn("Suite B: On-device Performance", rendered)
        self.assertIn("Scored Model", rendered)
        self.assertIn("Measured Model", rendered)
        self.assertIn("Measurement rows are not ranked", rendered)


if __name__ == "__main__":
    unittest.main()
