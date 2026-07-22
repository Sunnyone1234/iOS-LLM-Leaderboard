#!/usr/bin/env python3
"""Versioned Power CLI adapter for compatibility policy 1.1.2."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import generate_power_community_ranking_1_1_2 as ranking
from scripts import validate_suite_b_power_1_1_compatible_result_1_1_2 as compatible
from scripts.validate_suite_b_power_1_1_submission_1_1_2 import (
    validate_package,
    validate_path,
)


_BASE_PATH = Path(__file__).with_name("power.py")
_SPEC = importlib.util.spec_from_file_location(
    "_power_1_1_1_cli_for_1_1_2",
    _BASE_PATH,
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load Power CLI: {_BASE_PATH}")
base = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(base)

base.ranking = ranking
base.compatible = compatible
base.validate_package = validate_package
base.validate_path = validate_path

create_package = base.create_package


if __name__ == "__main__":
    raise SystemExit(base.main())
