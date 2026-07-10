#!/usr/bin/env python3
"""Validate Community Submitted review records against immutable Draft files."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

def validate_review(review: dict, submission_path: Path) -> list[str]:
    errors: list[str] = []
    try: raw = submission_path.read_bytes(); submission = json.loads(raw)
    except (OSError, json.JSONDecodeError) as error: return [str(error)]
    constants = {"schemaVersion": "suite-b-community-review-0.1", "previousTrustLevel": "draft", "trustLevel": "community-submitted", "structuralValidationPassed": True, "reproduced": False, "verified": False, "maintainerReference": False, "defaultLeaderboardEligible": False}
    for key, expected in constants.items():
        if review.get(key) != expected: errors.append(f"{key} must be {expected!r}")
    if review.get("submissionID") != submission.get("submissionID"): errors.append("submissionID mismatch")
    if review.get("resultID") != submission.get("result", {}).get("resultID"): errors.append("resultID mismatch")
    if review.get("submissionSHA256") != hashlib.sha256(raw).hexdigest(): errors.append("submissionSHA256 mismatch")
    if not str(review.get("reviewer", "")).strip(): errors.append("reviewer is required")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--submissions", type=Path, required=True); parser.add_argument("--reviews", type=Path, required=True); args = parser.parse_args()
    failed = False
    for path in sorted(args.reviews.glob("*.json")):
        try: review = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as error: print(f"{path}: {error}"); failed = True; continue
        submission = args.submissions / f"{review.get('submissionID')}.json"
        errors = validate_review(review, submission)
        if errors:
            failed = True
            for error in errors: print(f"{path}: {error}")
        else: print(f"{path}: valid Community Submitted review")
    return 1 if failed else 0
if __name__ == "__main__": raise SystemExit(main())

