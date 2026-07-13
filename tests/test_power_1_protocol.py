from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "benchmarks" / "suite-b-on-device-performance"


class PowerOneProtocolFreezeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.protocol = json.loads((SUITE / "power-1.0-protocol.json").read_text())

    def test_release_candidate_is_non_official_and_exactly_two_workloads(self) -> None:
        self.assertEqual(self.protocol["protocol_version"], "1.0.0-rc.1")
        self.assertEqual(self.protocol["status"], "frozen-release-candidate")
        self.assertFalse(self.protocol["official_result_eligible"])
        self.assertEqual(
            [item["workload_id"] for item in self.protocol["workloads"]],
            ["b-ux-001-short-interaction", "b-pipe-001-sustained-generation"],
        )

    def test_frozen_fixture_hashes_match_repository_bytes(self) -> None:
        paths = {
            "b-ux-001-short-interaction": SUITE
            / "workloads/fixtures/b-ux-001-short-interaction-prompt.txt",
            "b-pipe-001-sustained-generation": ROOT
            / "ios-app/workloads/suite-b-pilot-001-prompt.txt",
        }
        for workload in self.protocol["workloads"]:
            digest = hashlib.sha256(paths[workload["workload_id"]].read_bytes()).hexdigest()
            self.assertEqual(digest, workload["fixture_sha256"])

    def test_attempt_and_aggregation_contract_is_frozen(self) -> None:
        self.assertEqual(
            self.protocol["attempt_outcomes"],
            ["completed", "failed", "cancelled", "outOfMemory", "notRun"],
        )
        self.assertEqual(self.protocol["procedure"]["warmup_attempts"], 1)
        self.assertEqual(self.protocol["procedure"]["measured_attempts"], 5)
        self.assertEqual(
            self.protocol["procedure"]["minimum_metric_eligible_measured_attempts"],
            3,
        )
        self.assertEqual(self.protocol["procedure"]["automatic_retries"], 0)
        self.assertEqual(self.protocol["procedure"]["aggregation"], "median")

    def test_only_short_interaction_ranks_first_renderable_proxy(self) -> None:
        workloads = {item["workload_id"]: item for item in self.protocol["workloads"]}
        metric = "first_renderable_proxy_ttft_ms@1"
        self.assertIn(metric, workloads["b-ux-001-short-interaction"]["ranked_metrics"])
        self.assertNotIn(
            metric,
            workloads["b-pipe-001-sustained-generation"]["ranked_metrics"],
        )

    def test_workload_generation_and_response_contracts_are_exact(self) -> None:
        workloads = {item["workload_id"]: item for item in self.protocol["workloads"]}
        ux = workloads["b-ux-001-short-interaction"]
        pipe = workloads["b-pipe-001-sustained-generation"]
        self.assertEqual(
            ux["generation_configuration"],
            {
                "top_p": 1,
                "top_k": 0,
                "seed": 0,
                "repetition_penalty": None,
                "thinking_mode": "disabled-via-chat-template",
                "chat_template_identity": "artifact-tokenizer-config-enable-thinking-false",
            },
        )
        self.assertEqual(pipe["generation_configuration"]["top_p"], None)
        self.assertEqual(pipe["generation_configuration"]["top_k"], None)
        self.assertEqual(
            ux["response_conformance"]["policy_version"],
            "short-interaction-response-v1",
        )
        self.assertEqual(ux["response_conformance"]["maximum_sentences"], 2)

    def test_power_degradation_metric_is_distinct_from_historical_pilot_id(self) -> None:
        metrics = (SUITE / "metrics.md").read_text()
        self.assertIn("decode_first_to_last_percent_change@1", metrics)
        self.assertIn("historical Pilot metric ID", metrics)
        self.assertIn("first_to_last_percent_change@1", metrics)


if __name__ == "__main__":
    unittest.main()
