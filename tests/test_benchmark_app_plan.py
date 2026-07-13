from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from scripts.validate_result import validate


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "ios-app" / "benchmark-plans" / "suite-b-pilot-001.json"
UX_PLAN_PATH = ROOT / "ios-app" / "benchmark-plans" / "b-ux-001-short-interaction.json"
REGISTRY_PATH = ROOT / "ios-app" / "benchmark-plans" / "suite-b-workload-registry.json"
FIXTURE_PATH = (
    ROOT
    / "ios-app"
    / "fixtures"
    / "suite-b-pilot-001-framework-v1-placeholder.json"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class BenchmarkAppPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = load_json(PLAN_PATH)

    def test_pilot_cannot_be_treated_as_official(self) -> None:
        self.assertEqual(self.plan["plan_id"], "b-pipe-001-validation")
        self.assertEqual(self.plan["plan_version"], "0.2.0-pilot")
        self.assertEqual(self.plan["status"], "pilot-validated")
        self.assertFalse(self.plan["official_result_eligible"])

    def test_procedure_is_one_warmup_and_five_measured_runs(self) -> None:
        procedure = self.plan["procedure"]
        self.assertEqual(procedure["warmup_runs"], 1)
        self.assertEqual(procedure["measured_runs"], 5)
        self.assertTrue(procedure["retain_all_attempts"])
        self.assertTrue(procedure["exclude_warmup_from_summary"])

    def test_workload_hash_matches_prompt(self) -> None:
        workload = self.plan["workload"]
        prompt = ROOT / workload["prompt_path"]
        digest = hashlib.sha256(prompt.read_bytes()).hexdigest()
        self.assertEqual(digest, workload["prompt_sha256"])

    def test_model_and_runtime_are_immutably_identified(self) -> None:
        model = self.plan["model_profile"]
        runtime = self.plan["runtime_profile"]
        self.assertEqual(len(model["artifact_revision"]), 40)
        self.assertNotIn(runtime["package_version"], {None, "", "main", "latest"})

    def test_decode_is_the_only_primary_metric(self) -> None:
        measurements = self.plan["measurements"]
        self.assertEqual(
            measurements["primary_metric"], "decode_tokens_per_second"
        )
        self.assertIn(
            "prefill_tokens_per_second", measurements["secondary_metrics"]
        )
        self.assertIn("thermal_state", measurements["secondary_metrics"])

    def test_plan_uses_frozen_pipeline_workload_identity(self) -> None:
        workload = self.plan["workload"]
        self.assertEqual(workload["category"], "pipeline")
        self.assertEqual(workload["workload_id"], "b-pipe-001-sustained-generation")
        self.assertEqual(workload["workload_version"], "0.2.0-pilot")
        self.assertEqual(
            workload["v2_profile_mapping"],
            "b-pipe-001-sustained-generation@0.2.0-pilot",
        )

    def test_timing_boundary_is_pipeline_not_user_visible(self) -> None:
        mode = self.plan["measurement_mode"]
        self.assertEqual(
            mode["pipeline_ttft_start"],
            "after-chat-template-and-tokenization-immediately-before-generateTokensTask",
        )
        self.assertFalse(mode["user_visible_ttft_available"])
        self.assertEqual(
            mode["decode_formula"],
            "(raw_token_count-1)/(last_raw_token_time-first_raw_token_time)",
        )

    def test_generation_and_environment_requirements_are_explicit(self) -> None:
        generation = self.plan["generation"]
        environment = self.plan["environment_requirements"]
        self.assertEqual(generation["temperature"], 0.0)
        self.assertEqual(generation["kv_cache_policy"], "new-cache-for-each-generation")
        self.assertEqual(environment["initial_thermal_state"], "nominal")
        self.assertEqual(environment["low_power_mode"], "off")
        self.assertEqual(
            generation["thinking_mode"],
            "disabled-via-prompt-directive",
        )

    def test_framework_v1_fixture_is_a_valid_empty_placeholder(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        self.assertEqual(validate(fixture), [])
        self.assertEqual(fixture["provenance"]["source"], "demo-placeholder")
        self.assertTrue(all(value is None for value in fixture["metrics"].values()))
        self.assertEqual(fixture["suite_b_measurement"]["per_run_metrics"], [])


class ShortInteractionPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = load_json(UX_PLAN_PATH)

    def test_candidate_identity_and_prompt_hash_are_frozen(self) -> None:
        self.assertEqual(self.plan["plan_id"], "b-ux-001-validation")
        self.assertEqual(self.plan["status"], "pilot-validated")
        workload = self.plan["workload"]
        prompt = ROOT / workload["prompt_path"]
        self.assertEqual(
            hashlib.sha256(prompt.read_bytes()).hexdigest(),
            workload["prompt_sha256"],
        )

    def test_candidate_uses_visible_boundary_and_disables_thinking(self) -> None:
        self.assertEqual(self.plan["workload"]["output_token_limit"], 128)
        self.assertTrue(
            self.plan["measurement_mode"]["user_visible_ttft_available"]
        )
        self.assertEqual(
            self.plan["generation"]["thinking_mode"],
            "disabled-via-chat-template",
        )
        self.assertFalse(self.plan["generation"]["sampling_enabled"])


class SuiteBPlanRegistryTests(unittest.TestCase):
    def test_registry_versions_all_four_workloads(self) -> None:
        registry = load_json(REGISTRY_PATH)
        self.assertEqual(registry["schema_version"], "suite-b-plan-registry-0.2")
        plans = registry["plans"]
        self.assertEqual(len(plans), 4)
        self.assertEqual(len({plan["workload_id"] for plan in plans}), 4)
        self.assertTrue(all(plan["warmup_runs"] == 1 for plan in plans))
        self.assertTrue(all(plan["measured_runs"] == 5 for plan in plans))
        self.assertTrue(all(plan["thinking_mode"].startswith("disabled-") for plan in plans))
        self.assertTrue(all(plan["required_power_source"] == "unplugged" for plan in plans))
        self.assertTrue(all(plan["minimum_battery_level_percent"] == 50 for plan in plans))

    def test_point_series_targets_and_hashes_are_parallel(self) -> None:
        for plan in load_json(REGISTRY_PATH)["plans"]:
            targets, hashes = plan["target_input_tokens"], plan["fixture_sha256"]
            self.assertEqual(len(targets), len(hashes)) if targets else self.assertEqual(len(hashes), 1)
            self.assertTrue(all(len(digest) == 64 for digest in hashes))


if __name__ == "__main__":
    unittest.main()
