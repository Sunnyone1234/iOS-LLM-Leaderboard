from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.create_suite_b_power_submission import create_package
from scripts.validate_suite_b_power_reviews import validate_reviews
from scripts.validate_suite_b_power_submission import validate_package
from scripts.validate_suite_b_power_submission import validate_path
from tests.test_suite_b_power_result import refresh_summary, valid_result


ROOT = Path(__file__).resolve().parents[1]
SUBMISSION_A = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
SUBMISSION_B = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
REVIEW_A = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
REVIEW_B = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
REVIEW_REPRODUCTION = "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"


def write_package(
    root: Path,
    submission_id: str = SUBMISSION_A,
    contributor: str = "contributor-a",
    result: dict | None = None,
) -> Path:
    result = copy.deepcopy(result or valid_result())
    package = root / submission_id
    package.mkdir(parents=True)
    result_bytes = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode()
    (package / "result.json").write_bytes(result_bytes)
    manifest = {
        "schemaVersion": "suite-b-power-submission-1.0.0-rc.1",
        "submissionID": submission_id,
        "createdAt": "2026-07-13T13:00:00Z",
        "benchmarkRelease": {"id": "suite-b-power", "version": "1.0.0-rc.1"},
        "state": "draft",
        "requestedEvidenceLevel": "community-submitted",
        "contributor": {"githubHandle": contributor},
        "conflictOfInterest": {
            "category": "none",
            "statement": "No conflict of interest disclosed.",
        },
        "declarations": {
            "ranOnPhysicalDevice": True,
            "authorizedToSubmit": True,
            "reviewedPublicMetadata": True,
            "rawResultUnmodified": True,
            "containsNoPersonalData": True,
            "acceptsCCBY40": True,
            "understandsNoRankingGuarantee": True,
        },
        "result": {
            "path": "result.json",
            "sha256": hashlib.sha256(result_bytes).hexdigest(),
            "schemaVersion": result["schemaVersion"],
            "resultID": result["resultID"],
            "workloadID": result["execution"]["workloadID"],
            "artifactID": result["model"]["artifactID"],
            "artifactRevision": result["model"]["artifactRevision"],
            "runtimeName": result["runtime"]["name"],
            "runtimeVersion": result["runtime"]["version"],
            "machineIdentifier": result["device"]["machineIdentifier"],
        },
    }
    (package / "submission.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    return package


def review_record(
    package: Path,
    review_id: str,
    reviewed_at: str,
    review_type: str = "initial-review",
    previous: str = "unreviewed",
    assigned: str = "community-submitted",
    supporting: list[str] | None = None,
) -> dict:
    manifest_bytes = (package / "submission.json").read_bytes()
    result_bytes = (package / "result.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    result = json.loads(result_bytes)
    return {
        "schemaVersion": "suite-b-power-review-1.0.0-rc.1",
        "reviewID": review_id,
        "reviewedAt": reviewed_at,
        "reviewer": {"githubHandle": "maintainer"},
        "reviewType": review_type,
        "submissionID": manifest["submissionID"],
        "submissionManifestSHA256": hashlib.sha256(manifest_bytes).hexdigest(),
        "resultID": result["resultID"],
        "resultSHA256": hashlib.sha256(result_bytes).hexdigest(),
        "previousEvidenceLevel": previous,
        "assignedEvidenceLevel": assigned,
        "supportingSubmissionIDs": supporting or [],
        "checks": {
            "packageIntegrity": True,
            "resultStructuralValidity": True,
            "resultProtocolConformance": True,
            "contributorDeclarations": True,
            "privacyReview": True,
            "conflictDisclosureReview": True,
        },
        "publication": {
            "releaseOfficial": False,
            "rankingAuthorized": False,
            "defaultLeaderboardEligible": False,
            "reasonCodes": [
                "release_candidate_not_official",
                "ranking_not_authorized",
            ],
        },
    }


def write_review(root: Path, value: dict) -> None:
    (root / f"{value['reviewID']}.json").write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n"
    )


class PowerSubmissionTests(unittest.TestCase):
    def test_publication_candidate_pins_governance_without_authorizing_release(self) -> None:
        candidate = json.loads((
            ROOT
            / "benchmarks/suite-b-on-device-performance/releases"
            / "suite-b-power-1.0.0-rc.1-publication-candidate.json"
        ).read_text())
        self.assertEqual(candidate["status"], "maintainer-review-required")
        self.assertFalse(candidate["officialResultEligible"])
        self.assertFalse(candidate["rankingAuthorized"])
        self.assertFalse(candidate["publicationAuthorized"])
        self.assertFalse(candidate["tagAuthorized"])
        frozen = candidate["frozenReleaseManifest"]
        self.assertEqual(
            hashlib.sha256((ROOT / frozen["path"]).read_bytes()).hexdigest(),
            frozen["sha256"],
        )
        verification = candidate["physicalDeviceVerification"]
        self.assertEqual(
            hashlib.sha256((ROOT / verification["checksumManifestPath"]).read_bytes()).hexdigest(),
            verification["checksumManifestSHA256"],
        )
        for asset in candidate["pinnedAssets"]:
            self.assertEqual(
                hashlib.sha256((ROOT / asset["path"]).read_bytes()).hexdigest(),
                asset["sha256"],
                asset["path"],
            )

    def test_creator_preserves_exact_result_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result_path = root / "app-export.json"
            result_bytes = (json.dumps(valid_result(), indent=4) + "\n").encode()
            result_path.write_bytes(result_bytes)
            package = create_package(
                result_path=result_path,
                output_root=root / "draft",
                contributor="contributor-a",
                conflict_category="none",
                conflict_statement="No conflict of interest disclosed.",
                declarations_accepted=True,
                submission_id=SUBMISSION_A,
                created_at="2026-07-13T13:00:00Z",
            )
            self.assertEqual((package / "result.json").read_bytes(), result_bytes)
            self.assertEqual(validate_package(package)["overallStatus"], "validWithWarnings")

    def test_creator_requires_explicit_declaration_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result_path = root / "app-export.json"
            result_path.write_text(json.dumps(valid_result()))
            with self.assertRaisesRegex(ValueError, "explicitly accepted"):
                create_package(
                    result_path=result_path,
                    output_root=root / "draft",
                    contributor="contributor-a",
                    conflict_category="none",
                    conflict_statement="No conflict of interest disclosed.",
                    declarations_accepted=False,
                )

    def test_valid_package_remains_unreviewed_and_unranked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = write_package(Path(temporary))
            report = validate_package(package)
            self.assertEqual(report["overallStatus"], "validWithWarnings")
            self.assertEqual(report["assignedEvidenceLevel"], "unreviewed")
            self.assertFalse(report["rankingEligibility"]["eligible"])
            self.assertTrue(report["powerResultValidation"]["structuralValidity"]["valid"])
            self.assertTrue(report["powerResultValidation"]["protocolConformance"]["valid"])

    def test_metric_ineligible_result_is_still_valid_submission_evidence(self) -> None:
        result = valid_result("b-ux-001-short-interaction")
        for attempt in result["attempts"]:
            attempt["generatedText"] = "Your note is safe on this iPhone and will sync when connected."
            attempt["responseConformance"] = {
                "status": "fail",
                "reasonCodes": ["response_conformance_failed"],
            }
            attempt["derivedMetrics"] = {
                key: None for key in attempt["derivedMetrics"]
            }
        refresh_summary(result)
        with tempfile.TemporaryDirectory() as temporary:
            report = validate_package(write_package(Path(temporary), result=result))
            self.assertEqual(report["overallStatus"], "validWithWarnings")
            self.assertFalse(
                report["powerResultValidation"]["metricEligibility"]
                ["decode_tokens_per_second@1"]["eligible"]
            )

    def test_result_tampering_breaks_package_integrity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = write_package(Path(temporary))
            result = json.loads((package / "result.json").read_text())
            result["resultID"] = "99999999-9999-4999-8999-999999999999"
            (package / "result.json").write_text(json.dumps(result) + "\n")
            report = validate_package(package)
            self.assertEqual(report["overallStatus"], "invalid")
            self.assertFalse(report["packageIntegrity"]["valid"])

    def test_declarations_and_package_contents_are_strict(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            package = write_package(Path(temporary))
            manifest = json.loads((package / "submission.json").read_text())
            manifest["declarations"]["containsNoPersonalData"] = False
            (package / "submission.json").write_text(json.dumps(manifest) + "\n")
            (package / "private.log").write_text("not allowed")
            report = validate_package(package)
            self.assertEqual(report["overallStatus"], "invalid")
            self.assertIn("contributor declarations are incomplete", report["errors"])
            self.assertTrue(any("unexpected package files" in error for error in report["errors"]))

    def test_intake_rejects_unrecognized_directories_and_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "incomplete-package").mkdir()
            (root / "unexpected.log").write_text("not accepted")
            report = validate_path(root)
            self.assertFalse(report["valid"])
            self.assertEqual(len(report["entries"]), 2)
            self.assertTrue(all(entry["overallStatus"] == "invalid" for entry in report["entries"]))

    def test_package_rejects_symlinked_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package = write_package(root)
            external = root / "external-result.json"
            external.write_bytes((package / "result.json").read_bytes())
            (package / "result.json").unlink()
            (package / "result.json").symlink_to(external)
            report = validate_package(package)
            self.assertEqual(report["overallStatus"], "invalid")
            self.assertTrue(any("regular file" in error for error in report["errors"]))


class PowerReviewTests(unittest.TestCase):
    def test_review_intake_rejects_unrecognized_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            submissions = root / "draft"
            reviews = root / "reviews"
            submissions.mkdir(); reviews.mkdir()
            (reviews / "private.log").write_text("not accepted")
            report = validate_reviews(submissions, reviews)
            self.assertFalse(report["valid"])
            self.assertTrue(any("unexpected review entry" in error for error in report["errors"]))

    def test_initial_review_grants_only_community_submitted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            submissions = root / "draft"
            reviews = root / "reviews"
            submissions.mkdir(); reviews.mkdir()
            package = write_package(submissions)
            write_review(
                reviews,
                review_record(package, REVIEW_A, "2026-07-13T13:01:00Z"),
            )
            report = validate_reviews(submissions, reviews)
            self.assertTrue(report["valid"])
            self.assertEqual(report["evidenceLevels"][SUBMISSION_A], "community-submitted")
            self.assertFalse(report["rankingChanged"])

    def test_reproduction_requires_compatible_independent_accepted_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            submissions = root / "draft"
            reviews = root / "reviews"
            submissions.mkdir(); reviews.mkdir()
            first_result = valid_result()
            second_result = copy.deepcopy(first_result)
            second_result["resultID"] = "33333333-3333-4333-8333-333333333333"
            second_result["execution"]["sessionID"] = "44444444-4444-4444-8444-444444444444"
            first = write_package(submissions, SUBMISSION_A, "contributor-a", first_result)
            second = write_package(submissions, SUBMISSION_B, "contributor-b", second_result)
            write_review(reviews, review_record(first, REVIEW_A, "2026-07-13T13:01:00Z"))
            write_review(reviews, review_record(second, REVIEW_B, "2026-07-13T13:02:00Z"))
            write_review(
                reviews,
                review_record(
                    first,
                    REVIEW_REPRODUCTION,
                    "2026-07-13T13:03:00Z",
                    review_type="reproduction-review",
                    previous="community-submitted",
                    assigned="reproduced",
                    supporting=[SUBMISSION_B],
                ),
            )
            report = validate_reviews(submissions, reviews)
            self.assertTrue(report["valid"])
            self.assertEqual(report["evidenceLevels"][SUBMISSION_A], "reproduced")

    def test_reproduction_rejects_same_contributor(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            submissions = root / "draft"
            reviews = root / "reviews"
            submissions.mkdir(); reviews.mkdir()
            first_result = valid_result()
            second_result = copy.deepcopy(first_result)
            second_result["resultID"] = "33333333-3333-4333-8333-333333333333"
            second_result["execution"]["sessionID"] = "44444444-4444-4444-8444-444444444444"
            first = write_package(submissions, SUBMISSION_A, "same-user", first_result)
            second = write_package(submissions, SUBMISSION_B, "same-user", second_result)
            write_review(reviews, review_record(first, REVIEW_A, "2026-07-13T13:01:00Z"))
            write_review(reviews, review_record(second, REVIEW_B, "2026-07-13T13:02:00Z"))
            write_review(
                reviews,
                review_record(
                    first,
                    REVIEW_REPRODUCTION,
                    "2026-07-13T13:03:00Z",
                    review_type="reproduction-review",
                    previous="community-submitted",
                    assigned="reproduced",
                    supporting=[SUBMISSION_B],
                ),
            )
            report = validate_reviews(submissions, reviews)
            self.assertFalse(report["valid"])
            self.assertTrue(any(
                "not contributor-independent" in error
                for entry in report["entries"] for error in entry["errors"]
            ))


if __name__ == "__main__":
    unittest.main()
