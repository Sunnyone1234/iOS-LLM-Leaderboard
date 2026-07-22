#!/usr/bin/env python3
"""Validate Power 1.1 results under compatibility policy 1.1.2."""

from __future__ import annotations

import importlib.util
from pathlib import Path


_BASE_PATH = Path(__file__).with_name(
    "validate_suite_b_power_1_1_compatible_result.py"
)
_SPEC = importlib.util.spec_from_file_location(
    "_power_1_1_1_compatible_result_for_1_1_2",
    _BASE_PATH,
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load compatibility validator: {_BASE_PATH}")
base = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(base)


SUITE = base.ROOT / "benchmarks" / "suite-b-on-device-performance"
base.POLICY_PATH = SUITE / "power-1.1-compatible-runners-1.1.2.json"
base.POLICY_SCHEMA_PATH = (
    base.ROOT / "schemas" / "suite-b-power-compatible-runners-1.1.2.schema.json"
)
base.RELEASE_MANIFEST_PATH = (
    SUITE / "releases" / "suite-b-power-1.1.2.json"
)
base.REPORT_SCHEMA_VERSION = (
    "suite-b-power-compatible-result-validation-1.1.2"
)
base.POLICY_VERSION = "1.1.2"
base.POLICY_RELEASE_VERSION = "1.1.2"

validate = base.validate
verify_compatibility_assets = base.verify_compatibility_assets


if __name__ == "__main__":
    raise SystemExit(base.main())
