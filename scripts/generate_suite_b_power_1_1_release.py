#!/usr/bin/env python3
"""Generate the Power 1.1 final-review package from hash-bound RC1 evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from scripts import consume_suite_b_power_1_1_rc1_report as rc_consumer
    from scripts import consume_suite_b_power_1_1_report as final_consumer
    from scripts import validate_suite_b_power_1_1_final_result as final_validator
except ModuleNotFoundError:
    import consume_suite_b_power_1_1_rc1_report as rc_consumer
    import consume_suite_b_power_1_1_report as final_consumer
    import validate_suite_b_power_1_1_final_result as final_validator


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RELEASE = (
    ROOT
    / "benchmarks/suite-b-on-device-performance/releases/suite-b-power-1.1.0.json"
)
DEFAULT_ADOPTION = ROOT / "results/suite-b-power-1.1/evidence-adoption.json"
DEFAULT_OUTPUT = ROOT / "results/suite-b-power-1.1"

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

SIZE_CLASSES = {
    "Qwen/Qwen3-0.6B": "small-0.6b",
    "Qwen/Qwen3-1.7B": "small-1.7b",
    "Qwen/Qwen3-4B": "small-4b",
}

DECLARATION_KEYS = (
    "physicalDeviceRun",
    "authorizedToSubmit",
    "publicMetadataReviewed",
    "unmodifiedAppExport",
    "containsNoPersonalData",
    "ccBy4Contribution",
    "acceptanceVerificationRankingNotGuaranteed",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify_release(release_path: Path, adoption_path: Path) -> dict[str, Any]:
    release = load_json(release_path)
    require(release.get("releaseID") == "suite-b-power", "unexpected release ID")
    require(release.get("releaseVersion") == "1.1.0", "unexpected release version")
    contract = release.get("contractAdoption", {})
    require(
        contract.get("method")
        == "exact-release-candidate-adoption-with-final-revalidation",
        "release does not declare exact RC adoption",
    )
    require(contract.get("newExecutionRequired") is False, "release requires a rerun")
    require(
        contract.get("rawEvidenceMutationAllowed") is False,
        "release permits raw-evidence mutation",
    )
    evidence = release.get("evidence", {})
    require(
        ROOT / evidence.get("evidenceAdoptionPath", "") == adoption_path,
        "evidence adoption path mismatch",
    )
    require(
        sha256(adoption_path) == evidence.get("evidenceAdoptionSHA256"),
        "evidence adoption digest mismatch",
    )
    asset_errors = final_validator.verify_final_assets()
    require(not asset_errors, "; ".join(asset_errors))
    return release


def verify_activation(release: dict[str, Any], adoption: dict[str, Any]) -> bool:
    flags = tuple(
        release.get(key)
        for key in (
            "officialResultEligible",
            "rankingAuthorized",
            "publicationAuthorized",
            "tagAuthorized",
        )
    )
    if not any(flags):
        require(all(flag is False for flag in flags), "candidate flags must all be false")
        return False
    require(all(flag is True for flag in flags), "publication flags must activate together")
    require(release.get("status") == "published", "active release status must be published")
    decision = adoption.get("decision", {})
    contributor = adoption.get("contributor", {})
    require(decision.get("status") == "approved-for-publication", "adoption is not approved")
    require(
        decision.get("finalPublicationApprovalRequired") is False,
        "final publication approval is still required",
    )
    require(
        decision.get("approvedAt") == release.get("approvedAt"),
        "approval timestamps differ",
    )
    require(contributor.get("declarationsStatus") == "confirmed", "declarations are pending")
    require(contributor.get("evidenceLevel") == "maintainer-reference", "evidence level is pending")
    require(
        all(contributor.get("declarations", {}).get(key) is True for key in DECLARATION_KEYS),
        "all seven contributor declarations must be true",
    )
    conflict = contributor.get("conflictOfInterest", {})
    require(conflict.get("category") == "none", "conflict disclosure is not clear")
    require(
        conflict.get("statement") == "No conflict of interest disclosed.",
        "conflict disclosure statement mismatch",
    )
    thermal = contributor.get("thermalAssistance", {})
    require(thermal.get("category") == "none", "thermal-assistance disclosure is not clear")
    require(
        thermal.get("statement") == "No external thermal assistance was used.",
        "thermal-assistance statement mismatch",
    )
    require(release.get("activationRequirements") == [], "activation requirements remain open")
    activation = release.get("activationRecord", {})
    require(activation.get("officialResultCount") == 6, "official result count mismatch")
    require(activation.get("performanceRankedResultCount") == 6, "performance count mismatch")
    require(activation.get("recommendationEligibleResultCount") == 5, "recommendation count mismatch")
    return True


def verify_entries(
    adoption: dict[str, Any],
) -> list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]]:
    require(
        adoption.get("publicationRelease") == {"id": "suite-b-power", "version": "1.1.0"},
        "adoption publication identity mismatch",
    )
    require(
        adoption.get("sourceEvidenceRelease")
        == {"id": "suite-b-power", "version": "1.1.0-rc.1"},
        "adoption source identity mismatch",
    )
    decision = adoption.get("decision", {})
    require(decision.get("referenceAppChanged") is False, "reference App changed")
    require(decision.get("protocolSemanticsChanged") is False, "protocol semantics changed")
    require(decision.get("newExecutionRequired") is False, "adoption requires a rerun")
    require(decision.get("rawEvidenceMutationAllowed") is False, "adoption permits mutation")
    entries = adoption.get("entries", [])
    require(isinstance(entries, list) and len(entries) == 6, "adoption must bind six results")

    result_ids: set[str] = set()
    session_ids: set[str] = set()
    matrix: set[tuple[str, str]] = set()
    verified: list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]] = []
    for entry in entries:
        raw_path = ROOT / entry.get("rawPath", "")
        rc_path = ROOT / entry.get("rcValidationPath", "")
        final_path = ROOT / entry.get("finalValidationPath", "")
        for path, key in (
            (raw_path, "rawPath"),
            (rc_path, "rcValidationPath"),
            (final_path, "finalValidationPath"),
        ):
            require(path.is_file(), f"missing evidence for {key}: {entry.get(key)}")
        require(sha256(raw_path) == entry.get("rawSHA256"), "raw digest mismatch")
        require(sha256(rc_path) == entry.get("rcValidationSHA256"), "RC report digest mismatch")
        require(
            sha256(final_path) == entry.get("finalValidationSHA256"),
            "final report digest mismatch",
        )

        raw_bytes = raw_path.read_bytes()
        raw = json.loads(raw_bytes)
        rc_report = load_json(rc_path)
        final_report = load_json(final_path)
        rc_errors = rc_consumer.verify_pair(raw_bytes, raw, rc_report)
        require(not rc_errors, "invalid RC result/report pair: " + "; ".join(rc_errors))
        final_errors = final_consumer.verify_pair(raw_bytes, raw, final_report)
        require(not final_errors, "invalid final result/report pair: " + "; ".join(final_errors))

        execution = raw.get("execution", {})
        model = raw.get("model", {})
        require(raw.get("resultID") == entry.get("resultID"), "result ID mismatch")
        require(execution.get("sessionID") == entry.get("sessionID"), "session ID mismatch")
        require(execution.get("workloadID") == entry.get("workloadID"), "workload ID mismatch")
        require(model.get("artifactID") == entry.get("artifactID"), "artifact ID mismatch")
        require(model.get("artifactRevision") == entry.get("artifactRevision"), "revision mismatch")
        require(raw.get("schemaVersion") == "suite-b-power-result-1.1.0-rc.1", "schema mismatch")
        require(
            raw.get("benchmarkRelease", {}).get("version") == "1.1.0-rc.1",
            "source evidence was relabeled",
        )
        require(
            (execution.get("appVersion"), execution.get("appBuild"), execution.get("appSourceCommit"))
            == ("0.13.0", "16", "f5b863cc0ca4d82d987cd9779f8875939d7bf90c"),
            "reference App identity mismatch",
        )
        performance = final_report["performanceRankingEligibility"]["eligible"]
        recommendation = final_report["recommendationEligibility"]["eligible"]
        require(performance is entry.get("performanceRankingEligible"), "performance decision mismatch")
        require(recommendation is entry.get("recommendationEligible"), "recommendation decision mismatch")
        require(
            final_report["metricEligibility"][entry["primaryMetricID"]]["eligible"]
            is entry.get("primaryMetricEligible"),
            "primary metric decision mismatch",
        )

        result_id = entry["resultID"]
        session_id = entry["sessionID"]
        cell = (model["artifactID"], execution["workloadID"])
        require(result_id not in result_ids, "duplicate result ID")
        require(session_id not in session_ids, "duplicate session ID")
        require(cell not in matrix, "duplicate model/workload cell")
        result_ids.add(result_id)
        session_ids.add(session_id)
        matrix.add(cell)
        verified.append((entry, raw, final_report))

    require(len({artifact for artifact, _ in matrix}) == 3, "matrix must contain three artifacts")
    require(
        {workload for _, workload in matrix} == set(PRIMARY_METRICS),
        "matrix workload coverage mismatch",
    )
    return verified


def normalize_row(
    entry: dict[str, Any],
    raw: dict[str, Any],
    report: dict[str, Any],
    active: bool,
    evidence_level: str,
) -> dict[str, Any]:
    workload_id = raw["execution"]["workloadID"]
    metric_id, field, _ = PRIMARY_METRICS[workload_id]
    metrics = raw["summary"]["metrics"]
    model = dict(raw["model"])
    model["parameterSizeClass"] = SIZE_CLASSES.get(model.get("baseModelID"), "unclassified")
    execution = raw["execution"]
    device = dict(raw["device"])
    device.update(
        {
            "appVersion": execution["appVersion"],
            "appBuild": execution["appBuild"],
            "appSourceCommit": execution["appSourceCommit"],
        }
    )
    performance = report["performanceRankingEligibility"]
    recommendation = report["recommendationEligibility"]
    limitations = [
        "source-evidence-identity-remains-1.1.0-rc.1",
        "final-report-is-a-deterministic-revalidation-not-a-rerun",
        "single-device-single-runtime-verification",
        "five-measured-attempts-are-not-a-general-thermal-proof",
    ]
    if workload_id == "b-ux-001-short-interaction":
        limitations.append("first-renderable-proxy-is-not-screen-render-latency")
    if raw["environment"]["thermalStateAtSessionEnd"] == "serious":
        limitations.append("session-ended-at-serious-thermal-state")
    return {
        "resultID": raw["resultID"],
        "createdAt": raw["createdAt"],
        "benchmarkRelease": {"id": "suite-b-power", "version": "1.1.0"},
        "sourceEvidenceRelease": raw["benchmarkRelease"],
        "workload": {
            "id": workload_id,
            "version": execution["workloadVersion"],
            "category": execution["workloadCategory"],
            "fixtureSHA256": execution["fixtureSHA256"],
            "measurementModeID": execution["measurementModeID"],
        },
        "configuration": {
            "model": model,
            "runtime": raw["runtime"],
            "device": device,
            "generation": raw["configuration"],
        },
        "environment": raw["environment"],
        "summary": {
            "medianFirstRenderableProxyTTFTMilliseconds": metrics.get(
                "medianFirstRenderableProxyTTFTMilliseconds"
            ),
            "medianPipelineTTFTMilliseconds": metrics.get("medianPipelineTTFTMilliseconds"),
            "medianRequestCompletionMilliseconds": metrics.get(
                "medianRequestCompletionMilliseconds"
            ),
            "medianPrefillTokensPerSecond": metrics.get("medianPrefillTokensPerSecond"),
            "medianDecodeTokensPerSecond": metrics.get("medianDecodeTokensPerSecond"),
            "medianPeakMemoryMiB": metrics.get("medianProcessPhysicalFootprintMiB"),
            "decodeFirstToLastPercentChange": metrics.get("decodeFirstToLastPercentChange"),
            "terminalCounts": raw["summary"]["terminalCounts"],
        },
        "behaviorConformance": report["behaviorConformance"],
        "metricEligibility": report["metricEligibility"],
        "primaryMetric": {
            "id": metric_id,
            "summaryField": field,
            "value": metrics.get(field),
            "eligible": report["metricEligibility"][metric_id]["eligible"],
            "reasonCodes": report["metricEligibility"][metric_id]["reasonCodes"],
        },
        "rankingEligibility": {
            "measuredPerformance": performance,
            "recommendation": recommendation,
            "active": active and performance["eligible"],
            "performanceRank": None,
        },
        "evidence": {
            "level": evidence_level,
            "proposedLevel": "maintainer-reference",
            "adoptionStatus": entry["adoptionStatus"],
            "sourceResultUnmodified": True,
        },
        "source": {
            "rawPath": entry["rawPath"],
            "rawSHA256": entry["rawSHA256"],
            "rcValidationPath": entry["rcValidationPath"],
            "rcValidationSHA256": entry["rcValidationSHA256"],
            "finalValidationPath": entry["finalValidationPath"],
            "finalValidationSHA256": entry["finalValidationSHA256"],
        },
        "limitations": limitations,
    }


def assign_active_ranks(rows: list[dict[str, Any]], active: bool) -> None:
    if not active:
        return
    for workload_id, (_, field, reverse) in PRIMARY_METRICS.items():
        ranked = [
            row
            for row in rows
            if row["workload"]["id"] == workload_id
            and row["rankingEligibility"]["active"]
        ]
        ranked.sort(key=lambda row: row["summary"][field], reverse=reverse)
        for rank, row in enumerate(ranked, 1):
            row["rankingEligibility"]["performanceRank"] = rank


def build_dataset(
    release_path: Path = DEFAULT_RELEASE,
    adoption_path: Path = DEFAULT_ADOPTION,
) -> tuple[dict[str, Any], dict[str, Any]]:
    release = verify_release(release_path, adoption_path)
    adoption = load_json(adoption_path)
    active = verify_activation(release, adoption)
    verified = verify_entries(adoption)
    evidence_level = (
        "maintainer-reference"
        if adoption.get("contributor", {}).get("evidenceLevel") == "maintainer-reference"
        else "unreviewed"
    )
    rows = [
        normalize_row(entry, raw, report, active, evidence_level)
        for entry, raw, report in verified
    ]
    rows.sort(key=lambda row: (row["configuration"]["model"]["artifactID"], row["workload"]["id"]))
    assign_active_ranks(rows, active)
    return {
        "schemaVersion": "suite-b-power-leaderboard-1.1",
        "generatedAt": release["preparedAt"],
        "benchmarkRelease": {"id": "suite-b-power", "version": "1.1.0"},
        "sourceEvidenceRelease": adoption["sourceEvidenceRelease"],
        "publication": {
            "status": release["status"],
            "officialResultEligible": release["officialResultEligible"],
            "rankingAuthorized": release["rankingAuthorized"],
            "publicationAuthorized": release["publicationAuthorized"],
            "tagAuthorized": release["tagAuthorized"],
            "active": active,
        },
        "resultCount": len(rows),
        "performanceEligibleResultCount": sum(
            row["rankingEligibility"]["measuredPerformance"]["eligible"] for row in rows
        ),
        "recommendationEligibleResultCount": sum(
            row["rankingEligibility"]["recommendation"]["eligible"] for row in rows
        ),
        "activeRankedResultCount": sum(row["rankingEligibility"]["active"] for row in rows),
        "configurationCount": len({row["configuration"]["model"]["artifactID"] for row in rows}),
        "results": rows,
    }, adoption


def _candidate_sorted_rows(dataset: dict[str, Any], workload_id: str) -> list[dict[str, Any]]:
    _, field, reverse = PRIMARY_METRICS[workload_id]
    rows = [
        row
        for row in dataset["results"]
        if row["workload"]["id"] == workload_id
        and row["rankingEligibility"]["measuredPerformance"]["eligible"]
    ]
    return sorted(rows, key=lambda row: row["summary"][field], reverse=reverse)


def render_leaderboard(dataset: dict[str, Any]) -> str:
    active = dataset["publication"]["active"]
    title = "Power Benchmark 1.1" if active else "Power Benchmark 1.1 Final Review Candidate"
    lines = [
        f"# {title}",
        "",
        "Generated from six hash-bound physical-device results and deterministic final validation reports.",
        "Raw evidence remains labeled `suite-b-power@1.1.0-rc.1`; no result bytes were rewritten.",
        "",
    ]
    if not active:
        lines += [
            "> This is review material, not an official ranking. Public ranking remains disabled until explicit maintainer approval.",
            "",
        ]
    for heading, workload_id, metric_label in (
        ("Measured responsiveness", "b-ux-001-short-interaction", "Proxy TTFT"),
        ("Measured sustained generation", "b-pipe-001-sustained-generation", "Decode"),
    ):
        rows = _candidate_sorted_rows(dataset, workload_id)
        _, field, reverse = PRIMARY_METRICS[workload_id]
        first_column = "Rank" if active else "Review order"
        lines += [
            f"## {heading}",
            "",
            f"| {first_column} | Model | Quant | {metric_label} | Pipeline TTFT | Prefill | Peak memory | End thermal | Recommendation | Evidence |",
            "| ---: | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |",
        ]
        for order, row in enumerate(rows, 1):
            summary = row["summary"]
            primary = summary[field]
            primary_text = f"{primary:.2f} {'tok/s' if reverse else 'ms'}"
            raw_path = "../../" + row["source"]["rawPath"]
            recommendation = (
                "eligible"
                if row["rankingEligibility"]["recommendation"]["eligible"]
                else "not verified"
            )
            lines.append(
                f"| {order} | {row['configuration']['model']['displayName']} | "
                f"{row['configuration']['model']['quantization']} | {primary_text} | "
                f"{summary['medianPipelineTTFTMilliseconds']:.2f} ms | "
                f"{summary['medianPrefillTokensPerSecond']:.2f} tok/s | "
                f"{summary['medianPeakMemoryMiB']:.0f} MiB | "
                f"{row['environment']['thermalStateAtSessionEnd']} | {recommendation} | "
                f"[{row['resultID'][:8]}]({raw_path}) |"
            )
        lines.append("")
    lines += [
        "The measured-performance and recommendation views are separate.",
        "No combined Power score or Ship score is defined.",
        "",
    ]
    return "\n".join(lines)


def render_release_notes(dataset: dict[str, Any]) -> str:
    active = dataset["publication"]["active"]
    status = (
        "Power 1.1 is published and workload-specific measured-performance ranking is active."
        if active
        else "Power 1.1 is frozen for final review; publishing, tagging, and public ranking remain disabled."
    )
    return "\n".join(
        [
            "# Power Benchmark 1.1 Final Package Notes",
            "",
            "## Status",
            "",
            status,
            "",
            "## Evidence boundary",
            "",
            "- six unmodified Power 1.1 RC1 physical-device results;",
            "- six preserved RC validation reports;",
            "- six deterministic final validation reports;",
            "- three exact Qwen3 MLX artifacts across two frozen workloads; and",
            "- App 0.13.0 build 16 at source commit `f5b863c…`.",
            "",
            "## Eligibility",
            "",
            f"- {dataset['performanceEligibleResultCount']} measured-performance-eligible results;",
            f"- {dataset['recommendationEligibleResultCount']} recommendation-eligible results; and",
            "- one Short Interaction result retained as measured performance with behavior `not_verified`.",
            "",
            "The 1.7B and 4B sustained-generation sessions ended in the serious thermal state; those unfavorable observations are retained.",
            "No aggregate score or cross-device generalization is claimed.",
            "",
        ]
    )


def write_outputs(
    output: Path = DEFAULT_OUTPUT,
    release_path: Path = DEFAULT_RELEASE,
    adoption_path: Path = DEFAULT_ADOPTION,
) -> dict[str, Any]:
    dataset, _ = build_dataset(release_path, adoption_path)
    output.mkdir(parents=True, exist_ok=True)
    normalized = output / "normalized-results.json"
    leaderboard = output / "LEADERBOARD.md"
    notes = output / "RELEASE-NOTES.md"
    readme = output / "README.md"
    normalized.write_text(json.dumps(dataset, indent=2, sort_keys=True) + "\n")
    leaderboard.write_text(render_leaderboard(dataset))
    notes.write_text(render_release_notes(dataset))
    readme.write_text(
        "# Power Benchmark 1.1\n\n"
        "This directory is generated from immutable Power 1.1 RC1 evidence and "
        "hash-bound final validation reports.\n\n"
        + (
            "This is the published Power 1.1 package.\n\n"
            if dataset["publication"]["active"]
            else "This is a final review candidate and does not activate public ranking.\n\n"
        )
        + "Regenerate and verify from the repository root:\n\n"
        "```bash\n"
        "python3 scripts/generate_suite_b_power_1_1_release.py\n"
        "shasum -a 256 -c results/suite-b-power-1.1/SHA256SUMS\n"
        "```\n"
    )
    checksum_paths: list[tuple[str, Path]] = [
        (str(release_path.relative_to(ROOT)), release_path),
        (str(adoption_path.relative_to(ROOT)), adoption_path),
    ]
    for entry in load_json(adoption_path)["entries"]:
        path = ROOT / entry["finalValidationPath"]
        checksum_paths.append((entry["finalValidationPath"], path))
    checksum_paths += [
        ("results/suite-b-power-1.1/normalized-results.json", normalized),
        ("results/suite-b-power-1.1/LEADERBOARD.md", leaderboard),
        ("results/suite-b-power-1.1/RELEASE-NOTES.md", notes),
        ("results/suite-b-power-1.1/README.md", readme),
    ]
    (output / "SHA256SUMS").write_text(
        "".join(f"{sha256(path)}  {label}\n" for label, path in checksum_paths)
    )
    return dataset


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, default=DEFAULT_RELEASE)
    parser.add_argument("--adoption", type=Path, default=DEFAULT_ADOPTION)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        dataset = write_outputs(args.output, args.release, args.adoption)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"error: {error}")
        return 1
    print(
        f"wrote {dataset['resultCount']} results; "
        f"{dataset['performanceEligibleResultCount']} performance-eligible; "
        f"{dataset['recommendationEligibleResultCount']} recommendation-eligible; "
        f"{dataset['activeRankedResultCount']} active-ranked"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
