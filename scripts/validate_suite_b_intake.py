#!/usr/bin/env python3
"""Batch-validate Draft Suite B submissions and emit an intake report."""
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
try:
    from scripts.validate_suite_b_submission import validate as validate_submission
except ModuleNotFoundError:
    from validate_suite_b_submission import validate as validate_submission

def validate_paths(paths: list[Path]) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    submission_ids: set[str] = set()
    result_ids: set[str] = set()
    for path in sorted(paths):
        errors: list[str] = []
        try: data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            data = {}; errors.append(str(error))
        errors.extend(validate_submission(data))
        submission_id = data.get("submissionID")
        result_id = data.get("result", {}).get("resultID")
        if isinstance(submission_id, str):
            if path.stem != submission_id: errors.append("filename must equal submissionID")
            if submission_id in submission_ids: errors.append("duplicate submissionID")
            submission_ids.add(submission_id)
        if isinstance(result_id, str):
            if result_id in result_ids: errors.append("duplicate embedded resultID")
            result_ids.add(result_id)
        entries.append({"path": path.as_posix(), "submissionID": submission_id, "resultID": result_id, "status": "structurally-valid" if not errors else "rejected", "errors": errors})
    return {"schemaVersion": "suite-b-intake-report-0.1", "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "trustLevelChanged": False, "defaultLeaderboardChanged": False, "valid": all(not entry["errors"] for entry in entries), "entries": entries}

def discover(path: Path) -> list[Path]:
    return sorted(path.glob("*.json")) if path.is_dir() else [path]

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = validate_paths(discover(args.path))
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report: args.report.write_text(rendered)
    print(rendered, end="")
    return 0 if report["valid"] else 1
if __name__ == "__main__": raise SystemExit(main())

