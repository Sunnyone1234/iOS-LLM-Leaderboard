#!/usr/bin/env python3
"""Classify a trusted Power submission using compatibility policy 1.1.2."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import generate_power_community_ranking_1_1_2 as ranking
from scripts.validate_suite_b_power_1_1_submission_1_1_2 import validate_package


_BASE_PATH = Path(__file__).with_name("triage_power_submission_pr.py")
_SPEC = importlib.util.spec_from_file_location(
    "_power_1_1_1_triage_for_1_1_2",
    _BASE_PATH,
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load submission triage: {_BASE_PATH}")
base = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(base)


base.ranking = ranking
base.validate_package = validate_package
classify = base.classify


if __name__ == "__main__":
    raise SystemExit(base.main())
