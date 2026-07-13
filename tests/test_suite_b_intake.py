from __future__ import annotations
import json, tempfile, unittest
from pathlib import Path
from scripts.promote_suite_b_submission import make_review
from scripts.validate_suite_b_intake import validate_paths
from scripts.validate_suite_b_reviews import validate_review
from tests.test_suite_b_submission import submission

class IntakeTests(unittest.TestCase):
    def write_submission(self, directory: Path, value: dict | None = None) -> Path:
        value = value or submission(); path = directory / f"{value['submissionID']}.json"; path.write_text(json.dumps(value, sort_keys=True)); return path

    def test_structural_intake_does_not_change_trust(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = validate_paths([self.write_submission(Path(temporary))])
        self.assertTrue(report["valid"]); self.assertFalse(report["trustLevelChanged"]); self.assertFalse(report["defaultLeaderboardChanged"])

    def test_filename_must_equal_submission_id(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "wrong.json"; path.write_text(json.dumps(submission()))
            report = validate_paths([path])
        self.assertFalse(report["valid"]); self.assertIn("filename must equal submissionID", report["entries"][0]["errors"])

    def test_duplicate_result_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary); first = submission(); second = submission(); second["submissionID"] = "second"
            report = validate_paths([self.write_submission(directory, first), self.write_submission(directory, second)])
        self.assertFalse(report["valid"]); self.assertTrue(any("duplicate embedded resultID" in error for entry in report["entries"] for error in entry["errors"]))

    def test_promotion_is_limited_to_community_submitted(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_submission(Path(temporary)); review = make_review(path, "maintainer")
            self.assertEqual(validate_review(review, path), [])
        self.assertEqual(review["trustLevel"], "community-submitted"); self.assertFalse(review["verified"]); self.assertFalse(review["defaultLeaderboardEligible"])

    def test_review_detects_changed_submission(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_submission(Path(temporary)); review = make_review(path, "maintainer"); path.write_text(path.read_text() + "\n")
            self.assertIn("submissionSHA256 mismatch", validate_review(review, path))

if __name__ == "__main__": unittest.main()
