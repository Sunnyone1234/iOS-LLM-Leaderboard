#!/usr/bin/env python3
"""Generate the Power ranking using compatibility policy 1.1.4."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_suite_b_power_1_1_compatible_result_1_1_4 import (
    validate as validate_power_1_1_result,
)
from scripts.validate_suite_b_power_1_1_submission_1_1_4 import (
    validate_package as validate_power_1_1_package,
)


_BASE_PATH = Path(__file__).with_name("generate_power_community_ranking.py")
_SPEC = importlib.util.spec_from_file_location(
    "_power_1_1_1_ranking_for_1_1_4",
    _BASE_PATH,
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load ranking generator: {_BASE_PATH}")
base = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(base)


base.validate_power_1_1_result = validate_power_1_1_result
base.validate_power_1_1_package = validate_power_1_1_package

DEFAULT_CURRENT_SUBMISSIONS = base.DEFAULT_CURRENT_SUBMISSIONS
DEFAULT_OUTPUT = base.DEFAULT_OUTPUT
build_dataset = base.build_dataset
make_contribution = base.make_contribution
write_outputs = base.write_outputs


if __name__ == "__main__":
    raise SystemExit(base.main())
