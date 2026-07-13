from __future__ import annotations
import base64, hashlib, json, unittest
from scripts.validate_suite_b_submission import validate
from tests.test_suite_b_result_bundle import bundle

def submission() -> dict:
    result = bundle("b-pipe-001-sustained-generation")
    result.update({"resultID": "result-1", "model": {"artifactID": "artifact"}, "device": {"machineIdentifier": "iPhone15,3"}})
    raw = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    return {"schemaVersion": "suite-b-community-submission-0.1", "submissionID": "submission-1", "createdAt": "2026-07-11T00:00:00Z", "currentTrustLevel": "draft", "requestedTrustLevel": "community-submitted", "validationStatus": "unvalidated", "contributor": {"displayName": "contributor"}, "declarations": {"reviewedResult": True, "confirmsNoPersonalData": True, "agreesToRepositoryLicense": True}, "privacy": {"excludedIdentifiers": ["apple-id", "serial-number", "udid", "user-documents", "personal-prompts"]}, "result": {"schemaVersion": result["schemaVersion"], "resultID": result["resultID"], "workloadID": result["workload"]["id"], "artifactID": "artifact", "machineIdentifier": "iPhone15,3", "encoding": "base64-json", "digestAlgorithm": "sha256", "sha256": hashlib.sha256(raw).hexdigest(), "bundleBase64": base64.b64encode(raw).decode()}}

class SubmissionTests(unittest.TestCase):
    def test_valid_draft_submission(self): self.assertEqual(validate(submission()), [])
    def test_app_cannot_self_assign_verified(self):
        value = submission(); value["currentTrustLevel"] = "verified"
        self.assertIn("App submission must start as draft", validate(value))
    def test_tampered_result_fails_digest(self):
        value = submission(); value["result"]["sha256"] = "0" * 64
        self.assertIn("embedded result SHA-256 mismatch", validate(value))
    def test_all_declarations_are_required(self):
        value = submission(); value["declarations"]["reviewedResult"] = False
        self.assertIn("declarations.reviewedResult must be true", validate(value))

if __name__ == "__main__": unittest.main()
