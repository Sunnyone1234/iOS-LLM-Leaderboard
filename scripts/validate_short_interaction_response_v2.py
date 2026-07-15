#!/usr/bin/env python3
"""Evaluate Short Interaction text with the versioned v2 behavior policy."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = (
    ROOT
    / "benchmarks/suite-b-on-device-performance/policies/short-interaction-response-v2.json"
)


@lru_cache(maxsize=1)
def load_policy() -> dict[str, Any]:
    policy = json.loads(POLICY_PATH.read_text())
    if policy.get("policyID") != "short-interaction-response-v2":
        raise ValueError("short-interaction response policy identity mismatch")
    if policy.get("status") != "draft":
        raise ValueError("v2 behavior policy must remain draft until approved")
    return policy


def normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def _contains_any_phrase(value: str, phrases: list[str]) -> bool:
    return any(phrase in value for phrase in phrases)


def _has_any(tokens: set[str], terms: list[str]) -> bool:
    return not tokens.isdisjoint(terms)


def assess(text: Any) -> dict[str, Any]:
    policy = load_policy()
    if not isinstance(text, str):
        return _decision(policy, "not_verified")
    value = normalize(text)
    if not value:
        return _decision(policy, "not_verified")
    sentence_count = len(
        [part for part in re.split(r"[.!?]+", value) if part.strip()]
    )
    if sentence_count > policy["maximumSentences"]:
        return _decision(policy, "not_verified")

    local = policy["localPersistence"]
    sync = policy["deferredSync"]
    if _contains_any_phrase(value, local["contradictionPhrases"]) or _contains_any_phrase(
        value, sync["contradictionPhrases"]
    ):
        return _decision(policy, "contradicted")

    tokens = set(re.findall(r"[^\W_]+", value, flags=re.UNICODE))
    verified = (
        _has_any(tokens, local["claimTerms"])
        and _has_any(tokens, local["locationTerms"])
        and _has_any(tokens, sync["actionTerms"])
        and _has_any(tokens, sync["connectivityTerms"])
        and _has_any(tokens, sync["conditionTerms"])
    )
    return _decision(policy, "verified" if verified else "not_verified")


def _decision(policy: dict[str, Any], status: str) -> dict[str, Any]:
    reason = {
        "verified": [],
        "not_verified": ["behavior_not_verified"],
        "contradicted": ["behavior_contradicted"],
    }[status]
    return {
        "applicable": True,
        "policyID": policy["policyID"],
        "policyVersion": policy["policyVersion"],
        "status": status,
        "reasonCodes": reason,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", nargs="?")
    parser.add_argument("--file", type=Path)
    args = parser.parse_args(argv)
    if (args.text is None) == (args.file is None):
        parser.error("provide exactly one of text or --file")
    text = args.file.read_text() if args.file else args.text
    decision = assess(text)
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0 if decision["status"] == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
