#!/usr/bin/env python3
"""Validate Power 1.1 submission packages under policy 1.1.4."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import validate_suite_b_power_1_1_compatible_result_1_1_4 as compatible


_BASE_PATH = Path(__file__).with_name(
    "validate_suite_b_power_1_1_submission.py"
)
_SPEC = importlib.util.spec_from_file_location(
    "_power_1_1_1_submission_for_1_1_4",
    _BASE_PATH,
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load submission validator: {_BASE_PATH}")
base = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(base)


base.compatible = compatible
_validate_package_1_1_1 = base.validate_package
_validate_path_1_1_1 = base.validate_path


def _upgrade_report(report: dict[str, Any]) -> dict[str, Any]:
    report["schemaVersion"] = (
        "suite-b-power-submission-validation-report-1.1.4"
    )
    report["benchmarkRelease"]["version"] = "1.1.4"
    report["validator"]["version"] = "1.1.4"
    report["errors"] = [
        error.replace(
            "compatibility policy 1.1.1",
            "compatibility policy 1.1.4",
        )
        for error in report.get("errors", [])
    ]
    return report


def validate_package(package: Path) -> dict[str, Any]:
    return _upgrade_report(_validate_package_1_1_1(package))


base.validate_package = validate_package


def validate_path(path: Path) -> dict[str, Any]:
    report = _validate_path_1_1_1(path)
    report["schemaVersion"] = "suite-b-power-intake-report-1.1.4"
    report["benchmarkRelease"]["version"] = "1.1.4"
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    report = validate_path(args.path)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered)
    print(rendered, end="")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
