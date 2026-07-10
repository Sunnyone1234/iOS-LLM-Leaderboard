#!/usr/bin/env python3
"""Validate a Draft Suite B community submission and its embedded result."""
from __future__ import annotations
import base64, hashlib, json, sys
from pathlib import Path
from typing import Any
try:
    from scripts.validate_suite_b_result_bundle import validate as validate_result
except ModuleNotFoundError:
    from validate_suite_b_result_bundle import validate as validate_result

EXCLUDED = {"apple-id", "serial-number", "udid", "user-documents", "personal-prompts"}

def validate(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schemaVersion") != "suite-b-community-submission-0.1": errors.append("unsupported schemaVersion")
    if data.get("currentTrustLevel") != "draft": errors.append("App submission must start as draft")
    if data.get("requestedTrustLevel") != "community-submitted": errors.append("requested trust level must be community-submitted")
    if data.get("validationStatus") != "unvalidated": errors.append("App submission must be unvalidated")
    if not str(data.get("contributor", {}).get("displayName", "")).strip(): errors.append("contributor display name is required")
    declarations = data.get("declarations", {})
    for key in ("reviewedResult", "confirmsNoPersonalData", "agreesToRepositoryLicense"):
        if declarations.get(key) is not True: errors.append(f"declarations.{key} must be true")
    if not EXCLUDED.issubset(set(data.get("privacy", {}).get("excludedIdentifiers", []))): errors.append("privacy exclusion inventory is incomplete")
    result = data.get("result", {})
    if result.get("encoding") != "base64-json" or result.get("digestAlgorithm") != "sha256": errors.append("unsupported result encoding or digest")
    try: raw = base64.b64decode(result.get("bundleBase64", ""), validate=True)
    except (ValueError, TypeError): return errors + ["result bundleBase64 is invalid"]
    if hashlib.sha256(raw).hexdigest() != result.get("sha256"): errors.append("embedded result SHA-256 mismatch")
    try: embedded = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError): return errors + ["embedded result is not valid JSON"]
    for outer, inner in (("schemaVersion", embedded.get("schemaVersion")), ("resultID", embedded.get("resultID")), ("workloadID", embedded.get("workload", {}).get("id")), ("artifactID", embedded.get("model", {}).get("artifactID")), ("machineIdentifier", embedded.get("device", {}).get("machineIdentifier"))):
        if result.get(outer) != inner: errors.append(f"result.{outer} does not match embedded result")
    errors.extend(f"embedded result: {error}" for error in validate_result(embedded))
    return errors

def main() -> int:
    if len(sys.argv) != 2: return 2
    path = Path(sys.argv[1])
    try: errors = validate(json.loads(path.read_text()))
    except (OSError, json.JSONDecodeError) as error: errors = [str(error)]
    if errors:
        for error in errors: print(f"{path}: {error}", file=sys.stderr)
        return 1
    print(f"{path}: valid Draft Suite B community submission")
    return 0
if __name__ == "__main__": raise SystemExit(main())
