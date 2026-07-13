#!/usr/bin/env python3
"""Create a maintainer review record for Community Submitted status."""
from __future__ import annotations
import argparse, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
try:
    from scripts.validate_suite_b_submission import validate as validate_submission
except ModuleNotFoundError:
    from validate_suite_b_submission import validate as validate_submission

def make_review(path: Path, reviewer: str) -> dict:
    raw = path.read_bytes(); data = json.loads(raw); errors = validate_submission(data)
    if errors: raise ValueError("; ".join(errors))
    reviewer = reviewer.strip()
    if not reviewer: raise ValueError("reviewer is required")
    return {"schemaVersion": "suite-b-community-review-0.1", "submissionID": data["submissionID"], "submissionSHA256": hashlib.sha256(raw).hexdigest(), "resultID": data["result"]["resultID"], "reviewer": reviewer, "reviewedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "previousTrustLevel": "draft", "trustLevel": "community-submitted", "structuralValidationPassed": True, "reproduced": False, "verified": False, "maintainerReference": False, "defaultLeaderboardEligible": False}

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", required=True, type=Path)
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try: review = make_review(args.submission, args.reviewer)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(error); return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n")
    print(args.output)
    return 0
if __name__ == "__main__": raise SystemExit(main())

