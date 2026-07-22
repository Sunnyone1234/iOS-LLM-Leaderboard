#!/usr/bin/env python3
"""Generate the live Power ranking from official and merged community evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

try:
    from scripts.consume_suite_b_power_1_1_report import verify_pair as verify_final_pair
    from scripts import validate_suite_b_power_1_1_rc1_result as power11
    from scripts.validate_suite_b_power_1_1_compatible_result import validate as validate_power_1_1_result
    from scripts.validate_suite_b_power_1_1_submission import validate_package as validate_power_1_1_package
    from scripts.validate_suite_b_power_result import validate as validate_power_result
    from scripts.validate_suite_b_power_reviews import validate_reviews
    from scripts.validate_suite_b_power_submission import validate_package
except ModuleNotFoundError:
    from consume_suite_b_power_1_1_report import verify_pair as verify_final_pair
    import validate_suite_b_power_1_1_rc1_result as power11
    from validate_suite_b_power_1_1_compatible_result import validate as validate_power_1_1_result
    from validate_suite_b_power_1_1_submission import validate_package as validate_power_1_1_package
    from validate_suite_b_power_result import validate as validate_power_result
    from validate_suite_b_power_reviews import validate_reviews
    from validate_suite_b_power_submission import validate_package


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OFFICIAL = ROOT / "results/suite-b-power-1.1/normalized-results.json"
DEFAULT_ADOPTION = ROOT / "results/suite-b-power-1.1/evidence-adoption.json"
DEFAULT_CURRENT_SUBMISSIONS = ROOT / "submissions/suite-b/power-1.1.0/draft"
DEFAULT_LEGACY_SUBMISSIONS = ROOT / "submissions/suite-b/power-1.0.0-rc.1/draft"
DEFAULT_OUTPUT = ROOT / "results/suite-b-power-community"

PRIMARY_METRICS = {
    "b-ux-001-short-interaction": (
        "first_renderable_proxy_ttft_ms@1",
        "medianFirstRenderableProxyTTFTMilliseconds",
        False,
    ),
    "b-pipe-001-sustained-generation": (
        "decode_tokens_per_second@1",
        "medianDecodeTokensPerSecond",
        True,
    ),
}

SUMMARY_FIELDS = (
    "medianFirstRenderableProxyTTFTMilliseconds",
    "medianPipelineTTFTMilliseconds",
    "medianRequestCompletionMilliseconds",
    "medianPrefillTokensPerSecond",
    "medianDecodeTokensPerSecond",
    "medianProcessPhysicalFootprintMiB",
    "decodeFirstToLastPercentChange",
)

SUMMARY_METRIC_ELIGIBILITY = {
    "medianFirstRenderableProxyTTFTMilliseconds": "first_renderable_proxy_ttft_ms@1",
    "medianPipelineTTFTMilliseconds": "pipeline_ttft_ms@1",
    "medianPrefillTokensPerSecond": "prefill_tokens_per_second@1",
    "medianDecodeTokensPerSecond": "decode_tokens_per_second@1",
    "medianProcessPhysicalFootprintMiB": "process_physical_footprint_mib@1",
    "decodeFirstToLastPercentChange": "decode_first_to_last_percent_change@1",
}

THERMAL_ORDER = {
    "nominal": 0,
    "fair": 1,
    "serious": 2,
    "critical": 3,
    "unknown": 4,
}

HIGH_VARIATION_MAD_PERCENT = 10.0
LEGACY_METRIC_RECALCULATION_ID = "power-1.1-legacy-raw-evidence-recalculation-v1"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def result_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def recalculate_legacy_metrics(
    result: dict[str, Any],
    validation: dict[str, Any],
    raw_sha256: str,
) -> dict[str, Any] | None:
    """Recover performance metrics that the legacy App nulled after a text check.

    Power 1.1 separates measured performance from behavior recommendation. Some
    Power 1.0 Short Interaction exports retained complete token, timing, memory,
    and renderability evidence but wrote null derived metrics when the old
    literal response check failed. This interpretation never changes the raw
    result. It only derives metrics from that hash-bound evidence using the
    Power 1.1 calculation boundary.
    """
    if result.get("schemaVersion") != "suite-b-power-result-1.0.0-rc.1":
        return None
    execution = result.get("execution", {})
    workload_id = execution.get("workloadID")
    if workload_id != "b-ux-001-short-interaction":
        return None
    if not validation.get("structuralValidity", {}).get("valid"):
        return None
    if not validation.get("protocolConformance", {}).get("valid"):
        return None
    primary = validation.get("metricEligibility", {}).get(
        "first_renderable_proxy_ttft_ms@1", {}
    )
    if primary.get("eligible"):
        return None
    measured_attempts = [
        attempt for attempt in result.get("attempts", [])
        if attempt.get("role") == "measured"
    ]
    if not measured_attempts or not any(
        attempt.get("responseConformance", {}).get("status") == "fail"
        for attempt in measured_attempts
    ):
        return None

    errors: list[str] = []
    reasons: list[str] = []
    attempt_values: list[dict[str, float | None]] = []
    for position, attempt in enumerate(result.get("attempts", [])):
        attempt_values.append(
            power11._attempt_values(
                attempt,
                workload_id,
                errors,
                reasons,
                f"attempts[{position}]",
            )
        )
    if errors:
        return None

    minimum = result.get("configuration", {}).get(
        "minimumMetricEligibleMeasuredAttempts", 3
    )
    if not isinstance(minimum, int) or minimum < 1:
        return None
    measured_pairs = [
        (attempt, values_by_metric)
        for attempt, values_by_metric in zip(
            result.get("attempts", []), attempt_values
        )
        if attempt.get("role") == "measured"
    ]
    summary: dict[str, float | None] = {}
    eligibility: dict[str, dict[str, Any]] = {}
    for metric_id, summary_field in power11.SUMMARY_METRICS.items():
        if metric_id not in power11.WORKLOADS[workload_id]["metrics"]:
            continue
        values = [
            values_by_metric[metric_id]
            for attempt, values_by_metric in measured_pairs
            if attempt.get("outcome") == "completed"
            and values_by_metric.get(metric_id) is not None
        ]
        eligible = len(values) >= minimum
        summary[summary_field] = statistics.median(values) if eligible else None
        eligibility[metric_id] = {
            "eligible": eligible,
            "eligibleMeasuredAttempts": len(values),
            "reasonCodes": [] if eligible else ["insufficient_metric_eligible_attempts"],
        }

    if not eligibility.get("first_renderable_proxy_ttft_ms@1", {}).get("eligible"):
        return None
    return {
        "id": LEGACY_METRIC_RECALCULATION_ID,
        "sourceResultSHA256": raw_sha256,
        "sourceSchemaVersion": result["schemaVersion"],
        "performancePolicyVersion": "1.1.0",
        "behaviorAffectsPerformanceMetrics": False,
        "summary": summary,
        "metricEligibility": eligibility,
    }


def comparison_identity(result: dict[str, Any]) -> dict[str, Any]:
    """Return the exact test cell used for community contributor counting."""
    execution = result["execution"]
    model = result["model"]
    device = result["device"]
    return {
        "sourceEvidenceRelease": result["benchmarkRelease"],
        "workload": {
            "id": execution["workloadID"],
            "version": execution["workloadVersion"],
            "category": execution["workloadCategory"],
            "fixtureSHA256": execution["fixtureSHA256"],
            "measurementModeID": execution["measurementModeID"],
        },
        "runner": {
            "id": execution["runnerID"],
            "version": execution["runnerVersion"],
            "appVersion": execution["appVersion"],
            "appBuild": execution["appBuild"],
            "appSourceCommit": execution["appSourceCommit"],
        },
        "generation": result["configuration"],
        "model": {
            "artifactID": model["artifactID"],
            "artifactRevision": model["artifactRevision"],
            "artifactContentHash": model["artifactContentHash"],
            "quantization": model["quantization"],
            "modelFormat": model["modelFormat"],
            "tokenizerIdentity": model["tokenizerIdentity"],
        },
        "runtime": result["runtime"],
        "device": {
            "machineIdentifier": device["machineIdentifier"],
            "physicalMemoryBytes": device["physicalMemoryBytes"],
            "systemName": device["systemName"],
            "systemVersion": device["systemVersion"],
            "systemBuild": device["systemBuild"],
        },
    }


def make_contribution(
    *,
    contributor: str,
    result: dict[str, Any],
    raw_path: str,
    raw_sha256: str,
    source_kind: str,
    evidence_level: str,
    submission_id: str | None = None,
    ordinary_live_ranking_allowed: bool = True,
    ordinary_live_ranking_reason: str | None = None,
) -> dict[str, Any]:
    runner_compatibility = None
    if result.get("schemaVersion") == "suite-b-power-result-1.1.0-rc.1":
        compatible_report = validate_power_1_1_result(result, raw_sha256)
        if not compatible_report.get("valid"):
            reasons = compatible_report.get("runnerCompatibility", {}).get(
                "reasonCodes", []
            )
            detail = ", ".join(reasons) if reasons else "validation failed"
            raise ValueError(
                f"incompatible Power 1.1 result ({detail}): {raw_path}"
            )
        runner_compatibility = compatible_report["runnerCompatibility"]
        report = compatible_report["powerResultValidation"]
    else:
        report = validate_power_result(result)
    if not report.get("structuralValidity", {}).get("valid"):
        raise ValueError(f"structurally invalid Power result: {raw_path}")
    if not report.get("protocolConformance", {}).get("valid"):
        raise ValueError(f"non-conformant Power result: {raw_path}")
    identity = comparison_identity(result)
    metric_interpretation = recalculate_legacy_metrics(
        result, report, raw_sha256
    )
    return {
        "comparisonID": canonical_sha256(identity),
        "comparisonIdentity": identity,
        "contributor": contributor,
        "contributorKey": contributor.casefold(),
        "submissionID": submission_id,
        "sourceKind": source_kind,
        "evidenceLevel": evidence_level,
        "resultID": result["resultID"],
        "sessionID": result["execution"]["sessionID"],
        "createdAt": result["createdAt"],
        "rawPath": raw_path,
        "rawSHA256": raw_sha256,
        "result": result,
        "validation": report,
        "runnerCompatibility": runner_compatibility,
        "metricInterpretation": metric_interpretation,
        "ordinaryLiveRankingAllowed": ordinary_live_ranking_allowed,
        "ordinaryLiveRankingReason": ordinary_live_ranking_reason,
    }


def contribution_metric_value(
    contribution: dict[str, Any], field: str
) -> float | int | None:
    interpretation = contribution.get("metricInterpretation")
    if interpretation and field in interpretation.get("summary", {}):
        return interpretation["summary"][field]
    return contribution["result"]["summary"]["metrics"].get(field)


def contribution_metric_eligibility(
    contribution: dict[str, Any], metric_id: str
) -> dict[str, Any]:
    interpretation = contribution.get("metricInterpretation")
    if interpretation and metric_id in interpretation.get("metricEligibility", {}):
        return interpretation["metricEligibility"][metric_id]
    return contribution["validation"]["metricEligibility"].get(metric_id, {})


def load_official_contributions(
    official_path: Path = DEFAULT_OFFICIAL,
    adoption_path: Path = DEFAULT_ADOPTION,
) -> list[dict[str, Any]]:
    official = load_json(official_path)
    adoption = load_json(adoption_path)
    contributor = adoption.get("contributor", {}).get("githubHandle")
    if not isinstance(contributor, str) or not contributor:
        raise ValueError("official adoption does not identify its contributor")
    evidence_level = adoption.get("contributor", {}).get("evidenceLevel")
    if evidence_level != "maintainer-reference":
        raise ValueError("official adoption is not maintainer-reference evidence")
    contributions: list[dict[str, Any]] = []
    for row in official.get("results", []):
        raw_path = ROOT / row.get("source", {}).get("rawPath", "")
        validation_path = ROOT / row.get("source", {}).get("finalValidationPath", "")
        if not raw_path.is_file():
            raise ValueError(f"official raw result is missing: {raw_path}")
        if not validation_path.is_file():
            raise ValueError(f"official final validation is missing: {validation_path}")
        expected_sha = row.get("source", {}).get("rawSHA256")
        actual_sha = result_sha256(raw_path)
        if expected_sha != actual_sha:
            raise ValueError(f"official raw result digest mismatch: {raw_path}")
        expected_validation_sha = row.get("source", {}).get("finalValidationSHA256")
        if expected_validation_sha != result_sha256(validation_path):
            raise ValueError(f"official final validation digest mismatch: {validation_path}")
        raw_bytes = raw_path.read_bytes()
        result = json.loads(raw_bytes)
        report = load_json(validation_path)
        errors = verify_final_pair(raw_bytes, result, report)
        if errors:
            raise ValueError("invalid official result/report pair: " + "; ".join(errors))
        identity = comparison_identity(result)
        contributions.append({
            "comparisonID": canonical_sha256(identity),
            "comparisonIdentity": identity,
            "contributor": contributor,
            "contributorKey": contributor.casefold(),
            "submissionID": None,
            "sourceKind": "maintainer-reference",
            "evidenceLevel": evidence_level,
            "resultID": result["resultID"],
            "sessionID": result["execution"]["sessionID"],
            "createdAt": result["createdAt"],
            "rawPath": raw_path.relative_to(ROOT).as_posix(),
            "rawSHA256": actual_sha,
            "result": result,
            "validation": report,
            "ordinaryLiveRankingAllowed": True,
            "ordinaryLiveRankingReason": None,
        })
    return contributions


def load_review_levels(submissions_path: Path, reviews_path: Path) -> dict[str, str]:
    """Read hash-bound review history without changing the frozen contract."""
    report = validate_reviews(submissions_path, reviews_path)
    if not report.get("valid"):
        raise ValueError("Power review history is invalid")
    return dict(report.get("evidenceLevels", {}))


def load_legacy_community_contributions(
    submissions_path: Path = DEFAULT_LEGACY_SUBMISSIONS,
    reviews_path: Path | None = None,
) -> list[dict[str, Any]]:
    reviews_path = reviews_path or submissions_path.parent / "reviews"
    review_levels = load_review_levels(submissions_path, reviews_path)
    contributions: list[dict[str, Any]] = []
    for package in sorted(path for path in submissions_path.iterdir() if path.is_dir()):
        report = validate_package(package)
        if report.get("overallStatus") == "invalid":
            raise ValueError(f"invalid merged community package: {package}")
        manifest = load_json(package / "submission.json")
        result_path = package / "result.json"
        result = load_json(result_path)
        submission_id = manifest["submissionID"]
        contributions.append(make_contribution(
            contributor=manifest["contributor"]["githubHandle"],
            result=result,
            raw_path=display_path(result_path),
            raw_sha256=result_sha256(result_path),
            source_kind="community-submission",
            evidence_level=review_levels.get(submission_id, "unreviewed"),
            submission_id=submission_id,
        ))
    return contributions


def load_current_community_contributions(
    submissions_path: Path = DEFAULT_CURRENT_SUBMISSIONS,
) -> list[dict[str, Any]]:
    contributions: list[dict[str, Any]] = []
    for package in sorted(path for path in submissions_path.iterdir() if path.is_dir()):
        report = validate_power_1_1_package(package)
        if report.get("overallStatus") == "invalid":
            raise ValueError(f"invalid merged Power 1.1 community package: {package}")
        manifest = load_json(package / "submission.json")
        result_path = package / "result.json"
        result = load_json(result_path)
        ordinary = report["ordinaryLiveRankingEligibility"]["eligible"]
        reasons = report["ordinaryLiveRankingEligibility"].get("reasonCodes", [])
        contributions.append(make_contribution(
            contributor=manifest["contributor"]["githubHandle"],
            result=result,
            raw_path=display_path(result_path),
            raw_sha256=result_sha256(result_path),
            source_kind="community-submission",
            evidence_level="unreviewed",
            submission_id=manifest["submissionID"],
            ordinary_live_ranking_allowed=ordinary,
            ordinary_live_ranking_reason=(", ".join(reasons) if reasons else None),
        ))
    return contributions


# Compatibility alias for callers that still refer to the historical intake.
load_community_contributions = load_legacy_community_contributions


def ensure_unique_evidence(contributions: Iterable[dict[str, Any]]) -> None:
    fields = ("rawSHA256", "resultID", "sessionID")
    seen: dict[str, dict[str, str]] = {field: {} for field in fields}
    for contribution in contributions:
        for field in fields:
            value = contribution[field]
            previous = seen[field].get(value)
            if previous is not None:
                raise ValueError(
                    f"duplicate {field} across evidence: {previous} and {contribution['rawPath']}"
                )
            seen[field][value] = contribution["rawPath"]


def median(values: Iterable[float | int | None]) -> float | None:
    present = [float(value) for value in values if value is not None]
    return statistics.median(present) if present else None


def contributor_weighted_metric(
    contributions: list[dict[str, Any]],
    field: str,
) -> tuple[float | None, list[float]]:
    by_contributor: dict[str, list[float]] = defaultdict(list)
    for contribution in contributions:
        value = contribution_metric_value(contribution, field)
        if value is not None:
            by_contributor[contribution["contributorKey"]].append(float(value))
    contributor_medians = [
        statistics.median(values) for _, values in sorted(by_contributor.items())
    ]
    return median(contributor_medians), contributor_medians


def ineligibility_reason_codes(
    contributions: list[dict[str, Any]], primary_metric_id: str
) -> list[str]:
    """Keep a compact explanation for why an exact cell has no ranked metric."""
    reasons = {"no_metric_eligible_contribution"}
    for item in contributions:
        if not item.get("ordinaryLiveRankingAllowed", True):
            reasons.add("ordinary_live_ranking_not_allowed")

        metric = contribution_metric_eligibility(item, primary_metric_id)
        if not metric.get("eligible"):
            reasons.update(metric.get("reasonCodes", []))

        for attempt in item["result"].get("attempts", []):
            if attempt.get("role") != "measured":
                continue
            response = attempt.get("responseConformance", {})
            if response.get("status") not in (None, "pass"):
                reasons.update(
                    response.get("reasonCodes", ["response_conformance_not_passed"])
                )
            if attempt.get("outcome") not in (None, "completed"):
                reasons.update(attempt.get("reasonCodes", []))
    return sorted(reasons)


def relative_mad_percent(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    center = statistics.median(values)
    if center == 0:
        return 0.0 if all(value == 0 for value in values) else None
    mad = statistics.median(abs(value - center) for value in values)
    return mad / abs(center) * 100


def parameter_size_class(model: dict[str, Any]) -> str:
    known = {
        "Qwen/Qwen3-0.6B": "small-0.6b",
        "Qwen/Qwen3-1.7B": "small-1.7b",
        "Qwen/Qwen3-4B": "small-4b",
        "meta-llama/Llama-3.2-1B-Instruct": "small-1b",
        "google/gemma-3-1b-it": "small-1b",
        "ibm-granite/granite-3.3-2b-instruct": "medium-2b",
        "HuggingFaceTB/SmolLM3-3B": "medium-3b",
    }
    return known.get(model.get("baseModelID"), "unclassified")


def build_cell(contributions: list[dict[str, Any]]) -> dict[str, Any]:
    representative = sorted(
        contributions,
        key=lambda item: (item["createdAt"], item["rawPath"]),
    )[0]
    result = representative["result"]
    execution = result["execution"]
    model = dict(result["model"])
    model["parameterSizeClass"] = parameter_size_class(model)
    device = dict(result["device"])
    device.update({
        "appVersion": execution["appVersion"],
        "appBuild": execution["appBuild"],
        "appSourceCommit": execution["appSourceCommit"],
    })

    contributor_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for contribution in contributions:
        contributor_groups[contribution["contributorKey"]].append(contribution)
    contributor_names = [
        sorted(group, key=lambda item: (item["createdAt"], item["rawPath"]))[0]["contributor"]
        for _, group in sorted(contributor_groups.items())
    ]

    summary: dict[str, Any] = {}
    for field in SUMMARY_FIELDS:
        eligibility_id = SUMMARY_METRIC_ELIGIBILITY.get(field)
        metric_contributions = (
            [
                item for item in contributions
                if item.get("ordinaryLiveRankingAllowed", True)
                and contribution_metric_eligibility(item, eligibility_id).get("eligible")
            ]
            if eligibility_id
            else contributions
        )
        value, _ = contributor_weighted_metric(metric_contributions, field)
        output_field = (
            "medianPeakMemoryMiB"
            if field == "medianProcessPhysicalFootprintMiB"
            else field
        )
        summary[output_field] = value
    summary["finalThermalState"] = max(
        (item["result"]["environment"]["thermalStateAtSessionEnd"] for item in contributions),
        key=lambda value: THERMAL_ORDER.get(value, THERMAL_ORDER["unknown"]),
    )
    measured = [attempt for item in contributions for attempt in item["result"]["attempts"][1:]]
    summary.update({
        "completedMeasuredAttempts": sum(item.get("outcome") == "completed" for item in measured),
        "failedMeasuredAttempts": sum(item.get("outcome") == "failed" for item in measured),
        "notRunMeasuredAttempts": sum(item.get("outcome") == "notRun" for item in measured),
    })

    workload_id = execution["workloadID"]
    primary_metric_id, primary_field, _ = PRIMARY_METRICS[workload_id]
    eligible = [
        item for item in contributions
        if item.get("ordinaryLiveRankingAllowed", True)
        and contribution_metric_eligibility(item, primary_metric_id).get("eligible")
    ]
    primary_value, primary_contributor_values = contributor_weighted_metric(eligible, primary_field)
    primary_variation = relative_mad_percent(primary_contributor_values)
    eligible_contributor_count = len({item["contributorKey"] for item in eligible})
    contributor_count = len(contributor_groups)

    evidence = []
    for item in sorted(contributions, key=lambda value: (value["createdAt"], value["rawPath"])):
        evidence_item = {
            "contributor": item["contributor"],
            "submissionID": item["submissionID"],
            "sourceKind": item["sourceKind"],
            "evidenceLevel": item["evidenceLevel"],
            "resultID": item["resultID"],
            "sessionID": item["sessionID"],
            "createdAt": item["createdAt"],
            "rawPath": item["rawPath"],
            "rawSHA256": item["rawSHA256"],
            "primaryMetricEligible": item in eligible,
        }
        if not item.get("ordinaryLiveRankingAllowed", True):
            evidence_item["ordinaryLiveRankingAllowed"] = False
            evidence_item["ordinaryLiveRankingReason"] = item.get(
                "ordinaryLiveRankingReason"
            )
        if item.get("metricInterpretation"):
            evidence_item["metricInterpretation"] = {
                key: item["metricInterpretation"][key]
                for key in (
                    "id",
                    "sourceResultSHA256",
                    "performancePolicyVersion",
                    "behaviorAffectsPerformanceMetrics",
                )
            }
        if item.get("runnerCompatibility"):
            evidence_item["runnerCompatibility"] = {
                key: item["runnerCompatibility"].get(key)
                for key in ("approvalID", "matchType")
            }
        evidence.append(evidence_item)

    return {
        "comparisonID": representative["comparisonID"],
        "comparisonIdentity": representative["comparisonIdentity"],
        "benchmarkRelease": {"id": "suite-b-power", "version": "1.1.0"},
        "sourceEvidenceRelease": result["benchmarkRelease"],
        "workload": {
            "id": workload_id,
            "version": execution["workloadVersion"],
            "category": execution["workloadCategory"],
            "fixtureSHA256": execution["fixtureSHA256"],
            "measurementModeID": execution["measurementModeID"],
        },
        "configuration": {
            "model": model,
            "runtime": result["runtime"],
            "device": device,
            "generation": result["configuration"],
        },
        "summary": summary,
        "primaryMetric": {
            "id": primary_metric_id,
            "summaryField": primary_field,
            "value": primary_value,
            "eligible": primary_value is not None,
        },
        "rankingEligibility": {
            "candidateEligible": primary_value is not None,
            "active": primary_value is not None,
            "reasonCodes": (
                []
                if primary_value is not None
                else ineligibility_reason_codes(contributions, primary_metric_id)
            ),
        },
        "community": {
            "status": (
                "reproduced"
                if eligible_contributor_count >= 2
                else "single-contributor"
            ),
            "aggregateStatus": (
                "community-aggregate"
                if eligible_contributor_count >= 3
                else "provisional"
            ),
            "contributorCount": contributor_count,
            "eligibleContributorCount": eligible_contributor_count,
            "runCount": len(contributions),
            "eligibleRunCount": len(eligible),
            "contributors": contributor_names,
            "primaryMetricVariation": {
                "method": "contributor-weighted-median-absolute-deviation-percent",
                "value": primary_variation,
                "high": bool(
                    primary_variation is not None
                    and primary_variation > HIGH_VARIATION_MAD_PERCENT
                ),
                "warningThreshold": HIGH_VARIATION_MAD_PERCENT,
                "affectsEligibility": False,
            },
        },
        "evidence": evidence,
    }


def aggregate_contributions(contributions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ensure_unique_evidence(contributions)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for contribution in contributions:
        grouped[contribution["comparisonID"]].append(contribution)
    cells = [build_cell(items) for _, items in sorted(grouped.items())]
    cells.sort(key=lambda row: (
        row["workload"]["id"],
        row["configuration"]["device"]["machineIdentifier"],
        row["configuration"]["model"]["artifactID"],
        row["configuration"]["runtime"]["name"],
    ))
    return cells


def os_minor_family(version: Any) -> str:
    """Return the display family that may combine patch releases only."""
    parts = re.findall(r"\d+", str(version))
    return ".".join(parts[:2]) if len(parts) >= 2 else str(version)


def _numeric_version(value: Any) -> tuple[int, ...]:
    parts = re.findall(r"\d+", str(value))
    return tuple(int(part) for part in parts) if parts else (0,)


def _current_display_key(cell: dict[str, Any]) -> tuple[Any, ...]:
    """Group display-equivalent cells without weakening exact evidence identity."""
    identity = cell["comparisonIdentity"]
    model = identity["model"]
    runtime = identity["runtime"]
    device = identity["device"]
    workload = identity["workload"]
    return (
        workload["id"],
        canonical_sha256(identity["generation"]),
        model["artifactID"],
        model["artifactRevision"],
        model["artifactContentHash"],
        model["quantization"],
        model["tokenizerIdentity"],
        runtime["name"],
        runtime["backend"],
        device["machineIdentifier"],
        device["physicalMemoryBytes"],
        os_minor_family(device["systemVersion"]),
    )


def _current_display_preference(cell: dict[str, Any]) -> tuple[Any, ...]:
    """Prefer the newest App baseline and patch build inside one display family."""
    runner = cell["comparisonIdentity"]["runner"]
    device = cell["comparisonIdentity"]["device"]
    latest_evidence = max(
        (str(item["createdAt"]) for item in cell["evidence"]),
        default="",
    )
    return (
        _numeric_version(runner["appVersion"]),
        _numeric_version(runner["appBuild"]),
        _numeric_version(device["systemVersion"]),
        str(device["systemBuild"]),
        latest_evidence,
        cell["comparisonID"],
    )


def current_display_cells(
    cells: Iterable[dict[str, Any]],
    workload_id: str | None = None,
) -> list[dict[str, Any]]:
    """Select one current cell per model/device/runtime/iOS-minor display family.

    Exact cells and their complete OS builds remain untouched in the dataset.
    This function is only for the model-centered default leaderboard.
    """
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for cell in cells:
        if workload_id is None or cell["workload"]["id"] == workload_id:
            grouped[_current_display_key(cell)].append(cell)
    selected = [
        max(group, key=_current_display_preference)
        for _, group in sorted(grouped.items())
    ]
    selected.sort(key=lambda row: (
        row["workload"]["id"],
        row["configuration"]["device"]["machineIdentifier"],
        row["configuration"]["model"]["artifactID"],
        row["configuration"]["runtime"]["name"],
    ))
    return selected


def build_dataset(
    official_path: Path = DEFAULT_OFFICIAL,
    adoption_path: Path = DEFAULT_ADOPTION,
    current_submissions_path: Path = DEFAULT_CURRENT_SUBMISSIONS,
    legacy_submissions_path: Path = DEFAULT_LEGACY_SUBMISSIONS,
    reviews_path: Path | None = None,
) -> dict[str, Any]:
    official = load_json(official_path)
    contributions = load_official_contributions(official_path, adoption_path)
    contributions.extend(load_current_community_contributions(current_submissions_path))
    contributions.extend(
        load_legacy_community_contributions(legacy_submissions_path, reviews_path)
    )
    cells = aggregate_contributions(contributions)
    ranked = [cell for cell in cells if cell["rankingEligibility"]["active"]]
    community_runs = sum(item["sourceKind"] == "community-submission" for item in contributions)
    contributors = {item["contributorKey"] for item in contributions}
    return {
        "schemaVersion": "suite-b-power-community-ranking-1.1",
        "generatedAt": max(
            [str(official.get("generatedAt", ""))]
            + [item["createdAt"] for item in contributions]
        ),
        "benchmarkRelease": {"id": "suite-b-power", "version": "1.1.0"},
        "sourceEvidenceRelease": official["sourceEvidenceRelease"],
        "policy": {
            "comparison": "exact-comparison-identity-v1",
            "independentContributor": "case-insensitive-github-handle-per-comparison-cell",
            "contributorWeighting": "median-per-contributor-then-median-across-contributors",
            "reproducedMinimumContributors": 2,
            "aggregateMinimumContributors": 3,
            "highVariationMADPercent": HIGH_VARIATION_MAD_PERCENT,
            "highVariationAffectsEligibility": False,
            "appAttestRequired": False,
            "legacyMetricRecalculation": LEGACY_METRIC_RECALCULATION_ID,
        },
        "officialReferenceResultCount": sum(
            item["sourceKind"] == "maintainer-reference" for item in contributions
        ),
        "communityResultCount": community_runs,
        "resultCount": len(contributions),
        "cellCount": len(cells),
        "activeRankedCellCount": len(ranked),
        "contributorCount": len(contributors),
        "reproducedCellCount": sum(
            cell["community"]["status"] == "reproduced" for cell in cells
        ),
        "aggregateCellCount": sum(
            cell["community"]["aggregateStatus"] == "community-aggregate" for cell in cells
        ),
        "results": cells,
    }


def render_leaderboard(dataset: dict[str, Any]) -> str:
    lines = [
        "# Power Community Live Ranking",
        "",
        "This live view combines the immutable Power 1.1 Maintainer Reference results with valid merged community submissions.",
        "A GitHub account counts once per exact comparison cell and may contribute independently to any number of different cells.",
        "The default table shows the newest App baseline inside each model, device, runtime, and iOS minor family. Exact patch builds and older App baselines remain in normalized evidence and coverage history.",
        "For legacy Short Interaction exports that retained complete raw timing evidence but nulled derived metrics after the old text check, Power 1.1 recalculates performance without changing the source result or using behavior status as a performance gate.",
        "",
    ]
    sections = (
        ("Responsiveness", "b-ux-001-short-interaction", "medianFirstRenderableProxyTTFTMilliseconds", False, "Proxy TTFT"),
        ("Sustained generation", "b-pipe-001-sustained-generation", "medianDecodeTokensPerSecond", True, "Decode"),
    )
    for label, workload, field, reverse, metric_label in sections:
        current = current_display_cells(dataset["results"], workload)
        rows = [row for row in current if row["rankingEligibility"]["active"]]
        unranked = [row for row in current if not row["rankingEligibility"]["active"]]
        rows.sort(key=lambda row: row["summary"][field], reverse=reverse)
        lines.extend([
            f"## {label}",
            "",
            f"Current display: {len(current)} model configurations; {len(rows)} ranked; {len(unranked)} retained without a rank.",
            "",
            f"| Rank | Model | Quant | {metric_label} | App | iOS | Device | Contributors | Runs | Status | Variation |",
            "| ---: | --- | --- | ---: | --- | --- | --- | ---: | ---: | --- | ---: |",
        ])
        for rank, row in enumerate(rows, 1):
            metric = row["summary"][field]
            metric_text = f"{metric:.2f} {'tok/s' if reverse else 'ms'}"
            community = row["community"]
            variation = community["primaryMetricVariation"]["value"]
            variation_text = "—" if variation is None else f"{variation:.2f}%"
            status = (
                "Reproduced"
                if community["status"] == "reproduced"
                else "Single contributor"
            )
            if community["primaryMetricVariation"]["high"]:
                status += " · High variation"
            lines.append(
                f"| {rank} | {row['configuration']['model']['displayName']} | "
                f"{row['configuration']['model']['quantization']} | {metric_text} | "
                f"{row['configuration']['device']['appVersion']} | "
                f"{row['configuration']['device']['systemVersion']} | "
                f"{row['configuration']['device']['machineIdentifier']} | "
                f"{community['eligibleContributorCount']} | {community['runCount']} | {status} | "
                f"{variation_text} |"
            )
        lines.append("")
        if unranked:
            unranked.sort(key=lambda row: row["configuration"]["model"]["displayName"].casefold())
            lines.extend([
                "### Current configurations without a rank",
                "",
                f"These exact cells are retained, but no metric-eligible {metric_label} is available.",
                "",
                "| Model | Quant | App | iOS | Device | Reason |",
                "| --- | --- | --- | --- | --- | --- |",
            ])
            for row in unranked:
                lines.append(
                    f"| {row['configuration']['model']['displayName']} | "
                    f"{row['configuration']['model']['quantization']} | "
                    f"{row['configuration']['device']['appVersion']} | "
                    f"{row['configuration']['device']['systemVersion']} | "
                    f"{row['configuration']['device']['machineIdentifier']} | "
                    f"No metric-eligible {metric_label} |"
                )
            lines.append("")
    lines.extend([
        "Power 1.0 and every historical community result remain immutable. This file is a reproducible live derivative of Power 1.1 plus retained merged community evidence; every legacy metric interpretation is bound to the source result SHA-256.",
        "",
    ])
    return "\n".join(lines)


def render_coverage(dataset: dict[str, Any]) -> str:
    lines = [
        "# Power Evidence Coverage",
        "",
        "This report is derived only from retained Power evidence. It does not create placeholder devices, measurements, or benchmark results.",
        "A cell reaches the live `Reproduced` display at two independent metric-eligible GitHub contributors.",
        "",
        f"- Exact comparison cells: {dataset['cellCount']}",
        f"- Reproduced cells: {dataset['reproducedCellCount']}",
        f"- Cells still needing independent reproduction: {dataset['cellCount'] - dataset['reproducedCellCount']}",
        "",
        "| Workload | Model | Quant | Device | Eligible contributors | Retained runs | Coverage status |",
        "| --- | --- | --- | --- | ---: | ---: | --- |",
    ]
    for row in dataset["results"]:
        community = row["community"]
        eligible = community["eligibleContributorCount"]
        remaining = max(0, 2 - eligible)
        status = "Reproduced" if remaining == 0 else f"Needs {remaining} more"
        lines.append(
            f"| {row['workload']['id']} | "
            f"{row['configuration']['model']['displayName']} | "
            f"{row['configuration']['model']['quantization']} | "
            f"{row['configuration']['device']['displayName']} | "
            f"{eligible} | {community['runCount']} | {status} |"
        )
    lines.extend([
        "",
        "An accepted result from a new physical iPhone creates additional device coverage. It is not compared inside an existing exact cell unless every comparison-identity field matches.",
        "",
        "See the [Power 1.1 contributor quickstart](../../contributor-kit/power-1.1-quickstart.md) to contribute genuine physical-device evidence.",
        "",
    ])
    return "\n".join(lines)


def write_outputs(
    output: Path = DEFAULT_OUTPUT,
    official_path: Path = DEFAULT_OFFICIAL,
    adoption_path: Path = DEFAULT_ADOPTION,
    current_submissions_path: Path = DEFAULT_CURRENT_SUBMISSIONS,
    legacy_submissions_path: Path = DEFAULT_LEGACY_SUBMISSIONS,
    reviews_path: Path | None = None,
) -> dict[str, Any]:
    dataset = build_dataset(
        official_path=official_path,
        adoption_path=adoption_path,
        current_submissions_path=current_submissions_path,
        legacy_submissions_path=legacy_submissions_path,
        reviews_path=reviews_path,
    )
    output.mkdir(parents=True, exist_ok=True)
    (output / "normalized-results.json").write_text(
        json.dumps(dataset, indent=2, sort_keys=True) + "\n"
    )
    (output / "LEADERBOARD.md").write_text(render_leaderboard(dataset))
    (output / "COVERAGE.md").write_text(render_coverage(dataset))
    return dataset


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--official", type=Path, default=DEFAULT_OFFICIAL)
    parser.add_argument("--adoption", type=Path, default=DEFAULT_ADOPTION)
    parser.add_argument(
        "--current-submissions", type=Path, default=DEFAULT_CURRENT_SUBMISSIONS
    )
    parser.add_argument(
        "--legacy-submissions", type=Path, default=DEFAULT_LEGACY_SUBMISSIONS
    )
    parser.add_argument("--reviews", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        dataset = write_outputs(
            output=args.output,
            official_path=args.official,
            adoption_path=args.adoption,
            current_submissions_path=args.current_submissions,
            legacy_submissions_path=args.legacy_submissions,
            reviews_path=args.reviews,
        )
    except (OSError, json.JSONDecodeError, KeyError, ValueError) as error:
        print(f"error: {error}")
        return 1
    print(
        f"wrote {dataset['cellCount']} comparison cells from "
        f"{dataset['resultCount']} results and {dataset['contributorCount']} contributors"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
