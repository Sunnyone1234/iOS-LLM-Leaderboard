from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("github_models_experiment", HERE / "evaluate.py")
assert SPEC and SPEC.loader
EXPERIMENT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXPERIMENT)


class GitHubModelsShortInteractionExperimentTests(unittest.TestCase):
    def test_synthetic_corpus_is_balanced(self) -> None:
        cases = EXPERIMENT.load_cases(EXPERIMENT.DEFAULT_SYNTHETIC_CASES)
        counts = {
            label: sum(case["expectedBehavior"] == label for case in cases)
            for label in EXPERIMENT.VALID_DECISIONS
        }
        self.assertEqual(counts, {"verified": 6, "not_verified": 6, "contradicted": 6})

    def test_prompt_does_not_leak_expected_labels_or_sources(self) -> None:
        cases = EXPERIMENT.load_cases(EXPERIMENT.DEFAULT_REAL_CASES)
        prompt = EXPERIMENT.build_user_prompt(cases)
        payload = json.loads(prompt)
        self.assertNotIn("expectedSemantic", prompt)
        self.assertNotIn("expectedBehavior", prompt)
        self.assertNotIn("submissions/suite-b", prompt)
        self.assertEqual(len(payload["cases"]), len(cases))

    def test_validation_rejects_reordered_cases(self) -> None:
        cases = EXPERIMENT.load_cases(EXPERIMENT.DEFAULT_REAL_CASES)[:2]
        evaluations = [self.evaluation(case["caseID"]) for case in reversed(cases)]
        with self.assertRaisesRegex(ValueError, "out of order"):
            EXPERIMENT.validate_evaluations({"evaluations": evaluations}, cases)

    def test_report_separates_semantic_and_behavior_accuracy(self) -> None:
        cases = EXPERIMENT.load_cases(EXPERIMENT.DEFAULT_REAL_CASES)
        evaluations = []
        for case in cases:
            evaluation = self.evaluation(case["caseID"])
            evaluation["semanticDecision"] = case["expectedSemantic"]
            evaluation["behaviorDecision"] = case["expectedBehavior"]
            evaluations.append(evaluation)
        report = EXPERIMENT.build_report(
            EXPERIMENT.DEFAULT_REAL_CASES,
            cases,
            evaluations,
            model={"id": "test/model", "version": "test"},
            provider={},
            user_prompt="test",
            seed=42,
        )
        self.assertEqual(report["summary"]["semantic"]["accuracy"], 1.0)
        self.assertEqual(report["summary"]["behavior"]["accuracy"], 1.0)
        self.assertEqual(report["status"], "experimental-non-normative")

    @staticmethod
    def evaluation(case_id: str) -> dict[str, str]:
        return {
            "caseID": case_id,
            "localPersistence": "supported",
            "localEvidence": "saved locally",
            "deferredSync": "supported",
            "syncEvidence": "sync after reconnecting",
            "formatCompliance": "conformant",
            "semanticDecision": "verified",
            "behaviorDecision": "verified",
            "reason": "Both requirements are explicit.",
        }


if __name__ == "__main__":
    unittest.main()
