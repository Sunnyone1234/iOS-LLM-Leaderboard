#!/usr/bin/env python3
"""Run a non-normative GitHub Models experiment for Short Interaction text."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
DEFAULT_SYNTHETIC_CASES = HERE / "cases.jsonl"
DEFAULT_REAL_CASES = HERE / "real_cases.jsonl"
DEFAULT_MODEL = "openai/gpt-4.1-mini"
API_URL = "https://models.github.ai/inference/chat/completions"
CATALOG_URL = "https://models.github.ai/catalog/models"
API_VERSION = "2026-03-10"
EXPERIMENT_ID = "github-models-short-interaction"
EXPERIMENT_VERSION = "0.1.0"
VALID_DECISIONS = frozenset({"verified", "not_verified", "contradicted"})
VALID_CLAIM_STATES = frozenset({"supported", "not_supported", "contradicted"})
VALID_FORMAT_STATES = frozenset({"conformant", "nonconformant"})

SYSTEM_PROMPT = """You are a benchmark response evaluator, not a helpful assistant.
Judge only what each candidate response explicitly communicates. Do not repair it, infer
unstated implementation facts, or reward fluent wording by itself.

Evaluate two semantic requirements independently:
1. localPersistence: the response states that the note is retained, stored, saved, safe,
   secure, or otherwise remains on this iPhone/device while connectivity is unavailable.
   A statement that the note is merely safe, with no local device implication, is not enough.
2. deferredSync: the response states that the note will sync or upload after connectivity,
   internet, network service, Wi-Fi, or an online connection returns.

For each requirement return:
- supported: explicitly communicated, including a clear paraphrase;
- not_supported: absent, vague, merely possible, or missing the required condition;
- contradicted: explicitly denied or negated.

semanticDecision is contradicted if either requirement is contradicted, verified if both
are supported, and not_verified otherwise.

Evaluate format separately. formatCompliance is conformant only when the candidate itself
is a direct user-facing answer of at most two sentences, with no meta-introduction such as
"here is a message". Quotation marks do not matter. A short reassurance within those two
sentences is allowed.

behaviorDecision is contradicted when semanticDecision is contradicted; verified only when
semanticDecision is verified and formatCompliance is conformant; otherwise not_verified.

Return one evaluation for every supplied caseID, in the same order. Evidence fields must be
short exact excerpts from the candidate, or an empty string when the claim is unsupported.
Do not include Markdown or any text outside the JSON object."""


def load_cases(path: Path) -> list[dict[str, str]]:
    cases: list[dict[str, str]] = []
    seen: set[str] = set()
    for line_number, raw_line in enumerate(path.read_text().splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            value = json.loads(raw_line)
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid JSON on line {line_number}: {error}") from error
        if not isinstance(value, dict):
            raise ValueError(f"line {line_number} must contain a JSON object")
        case_id = value.get("caseID")
        response = value.get("response")
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError(f"line {line_number} has an invalid caseID")
        if not isinstance(response, str) or not response.strip():
            raise ValueError(f"line {line_number} has an invalid response")
        if case_id in seen:
            raise ValueError(f"duplicate caseID: {case_id}")
        seen.add(case_id)
        expected_semantic = value.get("expectedSemantic", value.get("expected"))
        expected_behavior = value.get("expectedBehavior", value.get("expected"))
        if expected_semantic not in VALID_DECISIONS:
            raise ValueError(f"line {line_number} has invalid expectedSemantic")
        if expected_behavior not in VALID_DECISIONS:
            raise ValueError(f"line {line_number} has invalid expectedBehavior")
        cases.append(
            {
                "caseID": case_id,
                "response": response,
                "expectedSemantic": expected_semantic,
                "expectedBehavior": expected_behavior,
                "focus": str(value.get("focus", "unspecified")),
                "source": str(value.get("source", path.name)),
            }
        )
    if not cases:
        raise ValueError("experiment corpus is empty")
    return cases


def build_user_prompt(cases: list[dict[str, str]]) -> str:
    payload = {
        "task": "Evaluate the supplied Short Interaction candidate responses.",
        "cases": [
            {"caseID": case["caseID"], "response": case["response"]}
            for case in cases
        ],
        "requiredOutput": {
            "evaluations": [
                {
                    "caseID": "string",
                    "localPersistence": "supported | not_supported | contradicted",
                    "localEvidence": "exact excerpt or empty string",
                    "deferredSync": "supported | not_supported | contradicted",
                    "syncEvidence": "exact excerpt or empty string",
                    "formatCompliance": "conformant | nonconformant",
                    "semanticDecision": "verified | not_verified | contradicted",
                    "behaviorDecision": "verified | not_verified | contradicted",
                    "reason": "one concise sentence",
                }
            ]
        },
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def resolve_token() -> str:
    for name in ("GITHUB_TOKEN", "GH_TOKEN"):
        value = os.environ.get(name)
        if value:
            return value
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as error:
        raise RuntimeError(
            "GitHub authentication unavailable; login with gh or set GITHUB_TOKEN"
        ) from error
    token = result.stdout.strip()
    if not token:
        raise RuntimeError("GitHub authentication returned an empty token")
    return token


def _request_json(
    url: str,
    token: str,
    *,
    payload: dict[str, Any] | None = None,
    timeout: int = 90,
) -> dict[str, Any] | list[Any]:
    data = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(
        url,
        data=data,
        method="GET" if payload is None else "POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "ios-llm-leaderboard-github-models-experiment",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")[:1000]
        raise RuntimeError(f"GitHub Models HTTP {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"GitHub Models request failed: {error.reason}") from error


def fetch_catalog_model(token: str, model_id: str, timeout: int) -> dict[str, Any]:
    catalog = _request_json(CATALOG_URL, token, timeout=timeout)
    if not isinstance(catalog, list):
        raise RuntimeError("GitHub Models catalog returned an unexpected document")
    for model in catalog:
        if isinstance(model, dict) and model.get("id") == model_id:
            return {
                key: model.get(key)
                for key in (
                    "id",
                    "name",
                    "publisher",
                    "registry",
                    "version",
                    "rate_limit_tier",
                    "capabilities",
                    "limits",
                )
            }
    raise RuntimeError(f"model is not present in the GitHub Models catalog: {model_id}")


def validate_evaluations(
    value: Any, cases: list[dict[str, str]]
) -> list[dict[str, str]]:
    if not isinstance(value, dict) or not isinstance(value.get("evaluations"), list):
        raise ValueError("model output must contain an evaluations array")
    evaluations = value["evaluations"]
    expected_ids = [case["caseID"] for case in cases]
    actual_ids = [item.get("caseID") if isinstance(item, dict) else None for item in evaluations]
    if actual_ids != expected_ids:
        raise ValueError("model output caseIDs are missing, duplicated, or out of order")
    required_strings = {
        "localEvidence",
        "syncEvidence",
        "reason",
    }
    normalized: list[dict[str, str]] = []
    for item in evaluations:
        if item.get("localPersistence") not in VALID_CLAIM_STATES:
            raise ValueError(f"invalid localPersistence for {item.get('caseID')}")
        if item.get("deferredSync") not in VALID_CLAIM_STATES:
            raise ValueError(f"invalid deferredSync for {item.get('caseID')}")
        if item.get("formatCompliance") not in VALID_FORMAT_STATES:
            raise ValueError(f"invalid formatCompliance for {item.get('caseID')}")
        if item.get("semanticDecision") not in VALID_DECISIONS:
            raise ValueError(f"invalid semanticDecision for {item.get('caseID')}")
        if item.get("behaviorDecision") not in VALID_DECISIONS:
            raise ValueError(f"invalid behaviorDecision for {item.get('caseID')}")
        if any(not isinstance(item.get(key), str) for key in required_strings):
            raise ValueError(f"evidence or reason is invalid for {item.get('caseID')}")
        normalized.append({key: str(value) for key, value in item.items()})
    return normalized


def run_inference(
    token: str,
    model_id: str,
    cases: list[dict[str, str]],
    *,
    seed: int,
    timeout: int,
) -> tuple[list[dict[str, str]], dict[str, Any], str]:
    user_prompt = build_user_prompt(cases)
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0,
        "seed": seed,
        "max_tokens": 6000,
        "response_format": {"type": "json_object"},
        "stream": False,
    }
    response = _request_json(API_URL, token, payload=payload, timeout=timeout)
    if not isinstance(response, dict):
        raise RuntimeError("GitHub Models inference returned an unexpected document")
    try:
        content = response["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
        raise RuntimeError("GitHub Models did not return valid JSON content") from error
    evaluations = validate_evaluations(parsed, cases)
    provider = {
        key: response.get(key)
        for key in ("id", "model", "created", "system_fingerprint", "usage")
        if key in response
    }
    return evaluations, provider, user_prompt


def build_report(
    cases_path: Path,
    cases: list[dict[str, str]],
    evaluations: list[dict[str, str]],
    *,
    model: dict[str, Any],
    provider: dict[str, Any],
    user_prompt: str,
    seed: int,
) -> dict[str, Any]:
    semantic_correct = 0
    behavior_correct = 0
    semantic_confusion: Counter[str] = Counter()
    behavior_confusion: Counter[str] = Counter()
    rows: list[dict[str, Any]] = []
    for case, evaluation in zip(cases, evaluations, strict=True):
        expected_semantic = case["expectedSemantic"]
        expected_behavior = case["expectedBehavior"]
        actual_semantic = evaluation["semanticDecision"]
        actual_behavior = evaluation["behaviorDecision"]
        semantic_match = expected_semantic == actual_semantic
        behavior_match = expected_behavior == actual_behavior
        semantic_correct += semantic_match
        behavior_correct += behavior_match
        semantic_confusion[f"{expected_semantic}->{actual_semantic}"] += 1
        behavior_confusion[f"{expected_behavior}->{actual_behavior}"] += 1
        rows.append(
            {
                **case,
                "evaluation": evaluation,
                "semanticMatchesExpected": semantic_match,
                "behaviorMatchesExpected": behavior_match,
            }
        )
    total = len(rows)
    return {
        "schemaVersion": "github-models-short-interaction-experiment-report-1",
        "status": "experimental-non-normative",
        "experiment": {"id": EXPERIMENT_ID, "version": EXPERIMENT_VERSION},
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "request": {
            "apiVersion": API_VERSION,
            "temperature": 0,
            "seed": seed,
            "determinismGuaranteed": False,
            "systemPromptSHA256": hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest(),
            "userPromptSHA256": hashlib.sha256(user_prompt.encode()).hexdigest(),
        },
        "providerResponse": provider,
        "corpus": {
            "path": str(cases_path),
            "sha256": hashlib.sha256(cases_path.read_bytes()).hexdigest(),
            "caseCount": total,
        },
        "summary": {
            "semantic": {
                "correct": semantic_correct,
                "total": total,
                "accuracy": round(semantic_correct / total, 6),
                "confusion": dict(sorted(semantic_confusion.items())),
            },
            "behavior": {
                "correct": behavior_correct,
                "total": total,
                "accuracy": round(behavior_correct / total, 6),
                "confusion": dict(sorted(behavior_confusion.items())),
            },
        },
        "cases": rows,
    }


def write_json(value: dict[str, Any], output: Path | None) -> None:
    payload = json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if output:
        output.write_text(payload)
    else:
        print(payload, end="")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_SYNTHETIC_CASES)
    parser.add_argument("--real-cases", action="store_true")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    cases_path = DEFAULT_REAL_CASES if args.real_cases else args.cases
    cases = load_cases(cases_path)
    user_prompt = build_user_prompt(cases)
    if args.dry_run:
        write_json(
            {
                "status": "plan-only-no-inference",
                "experiment": f"{EXPERIMENT_ID}@{EXPERIMENT_VERSION}",
                "model": args.model,
                "caseCount": len(cases),
                "caseSHA256": hashlib.sha256(cases_path.read_bytes()).hexdigest(),
                "systemPromptSHA256": hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest(),
                "userPromptSHA256": hashlib.sha256(user_prompt.encode()).hexdigest(),
            },
            args.output,
        )
        return 0

    token = resolve_token()
    catalog_model = fetch_catalog_model(token, args.model, args.timeout)
    evaluations, provider, user_prompt = run_inference(
        token,
        args.model,
        cases,
        seed=args.seed,
        timeout=args.timeout,
    )
    report = build_report(
        cases_path,
        cases,
        evaluations,
        model=catalog_model,
        provider=provider,
        user_prompt=user_prompt,
        seed=args.seed,
    )
    write_json(report, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
