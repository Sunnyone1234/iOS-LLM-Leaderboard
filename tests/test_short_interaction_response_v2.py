from __future__ import annotations

import unittest

from scripts.validate_short_interaction_response_v2 import assess
from scripts.validate_short_interaction_response_v2 import load_policy


class ShortInteractionResponseV2Tests(unittest.TestCase):
    def test_policy_is_versioned_draft_and_does_not_gate_performance(self) -> None:
        policy = load_policy()
        self.assertEqual(policy["policyID"], "short-interaction-response-v2")
        self.assertEqual(policy["policyVersion"], "2.0.0-draft.1")
        self.assertFalse(policy["rankingEffects"]["measurementEligibility"])
        self.assertFalse(policy["rankingEffects"]["performanceRankingEligibility"])
        self.assertTrue(policy["rankingEffects"]["recommendationEligibility"])

    def test_safe_wording_is_verified(self) -> None:
        result = assess(
            "Your note is safe on this iPhone. It will sync when connectivity returns."
        )
        self.assertEqual(result["status"], "verified")

    def test_secure_wording_is_verified(self) -> None:
        result = assess(
            "Your note is securely stored on this device. It will sync when connectivity returns."
        )
        self.assertEqual(result["status"], "verified")

    def test_saved_and_upload_wording_is_verified(self) -> None:
        result = assess(
            "The note was saved locally. It will upload automatically once you are back online."
        )
        self.assertEqual(result["status"], "verified")

    def test_missing_local_persistence_claim_is_not_verified(self) -> None:
        result = assess("Your note will sync when the device is online again.")
        self.assertEqual(result["status"], "not_verified")

    def test_unrecognized_synonym_is_not_a_semantic_failure(self) -> None:
        result = assess(
            "Your note remains intact on this device. It will sync when connectivity returns."
        )
        self.assertEqual(result["status"], "not_verified")
        self.assertEqual(result["reasonCodes"], ["behavior_not_verified"])

    def test_local_safety_contradiction_is_detected(self) -> None:
        result = assess(
            "Your note is not safe on this device. It will sync when connectivity returns."
        )
        self.assertEqual(result["status"], "contradicted")

    def test_sync_contradiction_is_detected(self) -> None:
        result = assess("Your note is safe locally, but it will never sync online.")
        self.assertEqual(result["status"], "contradicted")

    def test_more_than_two_sentences_is_not_verified(self) -> None:
        result = assess(
            "Your note is safe locally. The network is offline. It will sync when connectivity returns."
        )
        self.assertEqual(result["status"], "not_verified")


if __name__ == "__main__":
    unittest.main()
