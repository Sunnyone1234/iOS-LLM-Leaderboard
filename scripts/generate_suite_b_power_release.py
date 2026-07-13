#!/usr/bin/env python3
"""Build the Power 1.0 leaderboard candidate from immutable RC1 evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from scripts.validate_suite_b_power_result import validate as validate_power_result
except ModuleNotFoundError:
    from validate_suite_b_power_result import validate as validate_power_result


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RELEASE = (
    ROOT
    / "benchmarks/suite-b-on-device-performance/releases/suite-b-power-1.0.0.json"
)
DEFAULT_ADOPTION = ROOT / "results/suite-b-power-1.0/evidence-adoption.json"
DEFAULT_OUTPUT = ROOT / "results/suite-b-power-1.0"

PRIMARY_METRICS = {
    "b-ux-001-short-interaction": (
        "first_renderable_proxy_ttft_ms@1",
        "medianFirstRenderableProxyTTFTMilliseconds",
    ),
    "b-pipe-001-sustained-generation": (
        "decode_tokens_per_second@1",
        "medianDecodeTokensPerSecond",
    ),
}

SIZE_CLASSES = {
    "Qwen/Qwen3-0.6B": "small-0.6b",
    "Qwen/Qwen3-1.7B": "small-1.7b",
    "Qwen/Qwen3-4B": "small-4b",
}


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
    require(release.get("releaseVersion") == "1.0.0", "unexpected final release version")
    require(
        release.get("contractAdoption", {}).get("method")
        == "exact-release-candidate-adoption-without-rerun",
        "release does not declare exact RC adoption",
    )
    require(
        release.get("contractAdoption", {}).get("newExecutionRequired") is False,
        "release unexpectedly requires a new execution",
    )
    require(
        release.get("contractAdoption", {}).get("rawEvidenceMutationAllowed") is False,
        "release permits raw-evidence mutation",
    )
    evidence = release.get("evidenceAdoption", {})
    require((ROOT / evidence.get("path", "")) == adoption_path, "evidence path mismatch")
    require(sha256(adoption_path) == evidence.get("sha256"), "evidence manifest digest mismatch")
    for asset in release.get("pinnedAssets", []):
        path = ROOT / asset.get("path", "")
        require(path.is_file(), f"missing pinned release asset: {asset.get('path')}")
        require(sha256(path) == asset.get("sha256"), f"pinned asset digest mismatch: {asset.get('path')}")
    return release


def verify_entries(adoption: dict[str, Any]) -> list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]]:
    require(
        adoption.get("publicationRelease") == {"id": "suite-b-power", "version": "1.0.0"},
        "adoption publication identity mismatch",
    )
    require(
        adoption.get("sourceEvidenceRelease")
        == {"id": "suite-b-power", "version": "1.0.0-rc.1"},
        "adoption source identity mismatch",
    )
    decision = adoption.get("decision", {})
    require(decision.get("referenceAppChanged") is False, "reference App changed")
    require(decision.get("protocolSemanticsChanged") is False, "protocol semantics changed")
    require(decision.get("newExecutionRequired") is False, "adoption requires rerun")
    require(decision.get("rawEvidenceMutationAllowed") is False, "adoption permits evidence mutation")
    entries = adoption.get("entries", [])
    require(isinstance(entries, list) and len(entries) == 6, "adoption must bind exactly six results")
    result_ids: set[str] = set()
    sessions: set[str] = set()
    verified: list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]] = []
    for entry in entries:
        raw_path = ROOT / entry.get("rawPath", "")
        validation_path = ROOT / entry.get("validationPath", "")
        require(raw_path.is_file(), f"missing raw evidence: {entry.get('rawPath')}")
        require(validation_path.is_file(), f"missing validation evidence: {entry.get('validationPath')}")
        require(sha256(raw_path) == entry.get("rawSHA256"), f"raw digest mismatch: {raw_path}")
        require(
            sha256(validation_path) == entry.get("validationSHA256"),
            f"validation digest mismatch: {validation_path}",
        )
        raw = load_json(raw_path)
        stored_validation = load_json(validation_path)
        recalculated = validate_power_result(raw)
        require(stored_validation == recalculated, f"stored validation is stale: {validation_path}")
        require(recalculated.get("structuralValidity", {}).get("valid") is True, "invalid result structure")
        require(recalculated.get("protocolConformance", {}).get("valid") is True, "invalid protocol evidence")
        require(raw.get("resultID") == entry.get("resultID"), "result ID mismatch")
        require(raw.get("execution", {}).get("sessionID") == entry.get("sessionID"), "session ID mismatch")
        require(raw.get("execution", {}).get("workloadID") == entry.get("workloadID"), "workload ID mismatch")
        require(raw.get("model", {}).get("artifactID") == entry.get("artifactID"), "artifact ID mismatch")
        require(
            raw.get("model", {}).get("artifactRevision") == entry.get("artifactRevision"),
            "artifact revision mismatch",
        )
        require(
            raw.get("benchmarkRelease", {}).get("version") == "1.0.0-rc.1",
            "source result was relabeled instead of adopted",
        )
        execution = raw.get("execution", {})
        require(
            (execution.get("appVersion"), execution.get("appBuild"), execution.get("appSourceCommit"))
            == ("0.8.0", "10", "2f105ff463bc9b281b19655ba711b1ca7dee8759"),
            "reference App identity mismatch",
        )
        primary = recalculated.get("metricEligibility", {}).get(entry.get("primaryMetricID"), {})
        require(primary.get("eligible") is entry.get("primaryMetricEligible"), "primary eligibility mismatch")
        result_id = entry["resultID"]
        session_id = entry["sessionID"]
        require(result_id not in result_ids, "duplicate result ID")
        require(session_id not in sessions, "duplicate session ID")
        result_ids.add(result_id)
        sessions.add(session_id)
        verified.append((entry, raw, recalculated))
    return verified


def normalize_row(
    entry: dict[str, Any],
    raw: dict[str, Any],
    report: dict[str, Any],
    release: dict[str, Any],
    adoption: dict[str, Any],
) -> dict[str, Any]:
    workload_id = raw["execution"]["workloadID"]
    primary_metric, primary_field = PRIMARY_METRICS[workload_id]
    primary_decision = report["metricEligibility"][primary_metric]
    declarations_confirmed = (
        adoption.get("contributor", {}).get("declarationsStatus") == "confirmed"
    )
    publication_active = bool(
        release.get("officialResultEligible")
        and release.get("rankingAuthorized")
        and release.get("publicationAuthorized")
        and declarations_confirmed
    )
    active = bool(primary_decision["eligible"] and publication_active)
    reasons: list[str] = []
    if not primary_decision["eligible"]:
        reasons.extend(primary_decision.get("reasonCodes", []))
    if not release.get("publicationAuthorized"):
        reasons.append("final_publication_approval_pending")
    if adoption.get("contributor", {}).get("declarationsStatus") != "confirmed":
        reasons.append("contributor_declarations_pending")

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
    metrics = raw["summary"]["metrics"]
    measured = raw["attempts"][1:]
    limitations = [
        "source-evidence-identity-remains-1.0.0-rc.1",
        "adopted-without-rerun-because-app-and-protocol-are-unchanged",
        "single-device-single-runtime-verification",
        "five-measured-attempts-are-not-a-general-thermal-proof",
    ]
    if workload_id == "b-ux-001-short-interaction":
        limitations.append("first-renderable-proxy-is-not-screen-render-latency")
    if not primary_decision["eligible"]:
        limitations.extend(primary_decision.get("reasonCodes", []))

    return {
        "resultID": raw["resultID"],
        "createdAt": raw["createdAt"],
        "benchmarkRelease": {"id": "suite-b-power", "version": "1.0.0"},
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
            "finalThermalState": raw["environment"]["thermalStateAtSessionEnd"],
            "completedMeasuredAttempts": sum(a.get("outcome") == "completed" for a in measured),
            "failedMeasuredAttempts": sum(a.get("outcome") == "failed" for a in measured),
            "notRunMeasuredAttempts": sum(a.get("outcome") == "notRun" for a in measured),
        },
        "metricEligibility": report["metricEligibility"],
        "primaryMetric": {
            "id": primary_metric,
            "summaryField": primary_field,
            "value": metrics.get(primary_field),
            "eligible": primary_decision["eligible"],
            "reasonCodes": primary_decision.get("reasonCodes", []),
        },
        "evidence": {
            "level": (
                adoption["contributor"]["proposedEvidenceLevel"]
                if declarations_confirmed
                else "unreviewed"
            ),
            "proposedLevel": adoption["contributor"]["proposedEvidenceLevel"],
            "adoptionStatus": entry["adoptionStatus"],
            "sourceResultUnmodified": True,
        },
        "rankingEligibility": {
            "candidateEligible": primary_decision["eligible"],
            "active": active,
            "reasonCodes": list(dict.fromkeys(reasons)),
        },
        "source": {
            "rawPath": entry["rawPath"],
            "rawSHA256": entry["rawSHA256"],
            "validationPath": entry["validationPath"],
            "validationSHA256": entry["validationSHA256"],
        },
        "limitations": list(dict.fromkeys(limitations)),
    }


def render_leaderboard(dataset: dict[str, Any]) -> str:
    publication = dataset["publication"]
    active = bool(
        publication["officialResultEligible"]
        and publication["rankingAuthorized"]
        and publication["publicationAuthorized"]
        and dataset["activeRankedResultCount"] > 0
    )
    title = "Power Benchmark 1.0" if active else "Power Benchmark 1.0 Final Review Candidate"
    lines = [
        f"# {title}",
        "",
        "This leaderboard is generated only from the six immutable F5 physical-device results.",
        "The source JSON remains `suite-b-power@1.0.0-rc.1`; Power 1.0 adopts it by hash because the App and protocol semantics are unchanged.",
        "",
    ]
    if not active:
        lines.extend([
            "> Final publication and ranking are not active until the maintainer approves the complete package.",
            "",
        ])
    sections = [
        (
            "Responsiveness",
            "b-ux-001-short-interaction",
            "medianFirstRenderableProxyTTFTMilliseconds",
            False,
            "Proxy TTFT",
        ),
        (
            "Sustained generation",
            "b-pipe-001-sustained-generation",
            "medianDecodeTokensPerSecond",
            True,
            "Decode",
        ),
    ]
    for label, workload, field, reverse, metric_label in sections:
        rows = [
            row for row in dataset["results"]
            if row["workload"]["id"] == workload and row["rankingEligibility"]["candidateEligible"]
        ]
        rows.sort(key=lambda row: row["summary"][field], reverse=reverse)
        lines.extend([
            f"## {label}",
            "",
            f"| Rank | Model | Quant | {metric_label} | Pipeline TTFT | Prefill | Peak memory | Device | Evidence |",
            "| ---: | --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
        ])
        for rank, row in enumerate(rows, 1):
            summary = row["summary"]
            primary = summary[field]
            primary_text = f"{primary:.2f} {'tok/s' if reverse else 'ms'}"
            raw_path = "../../" + row["source"]["rawPath"]
            lines.append(
                f"| {rank} | {row['configuration']['model']['displayName']} | "
                f"{row['configuration']['model']['quantization']} | {primary_text} | "
                f"{summary['medianPipelineTTFTMilliseconds']:.2f} ms | "
                f"{summary['medianPrefillTokensPerSecond']:.2f} tok/s | "
                f"{summary['medianPeakMemoryMiB']:.0f} MiB | "
                f"{row['configuration']['device']['machineIdentifier']} | "
                f"[{row['resultID'][:8]}]({raw_path}) |"
            )
        lines.append("")
    excluded = [row for row in dataset["results"] if not row["rankingEligibility"]["candidateEligible"]]
    lines.extend([
        "## Retained but not ranked",
        "",
        "| Model | Workload | Reason | Raw evidence |",
        "| --- | --- | --- | --- |",
    ])
    for row in excluded:
        reasons = ", ".join(row["primaryMetric"]["reasonCodes"])
        raw_path = "../../" + row["source"]["rawPath"]
        lines.append(
            f"| {row['configuration']['model']['displayName']} | {row['workload']['id']} | "
            f"{reasons} | [{row['resultID'][:8]}]({raw_path}) |"
        )
    lines.extend(["", "No Power or Ship aggregate score is defined.", ""])
    return "\n".join(lines)


def render_release_notes(dataset: dict[str, Any], adoption: dict[str, Any]) -> str:
    publication = dataset["publication"]
    active = bool(
        publication["officialResultEligible"]
        and publication["rankingAuthorized"]
        and publication["publicationAuthorized"]
        and dataset["activeRankedResultCount"] > 0
        and adoption["contributor"]["declarationsStatus"] == "confirmed"
    )
    status = (
        "This is the published Power Benchmark 1.0 package. Official ranking is active within each workload."
        if active
        else "This is a final review candidate. Publishing, tagging, and official ranking remain disabled until explicit final approval."
    )
    decision_lines = (
        [
            "## Activation record",
            "",
            "The maintainer declarations and official-result, ranking, and publication authorizations are recorded in the final manifests.",
            "",
        ]
        if active
        else [
            "## Required final decisions",
            "",
            "- confirm the contributor declarations for the six maintainer-run results;",
            "- approve the final publication manifest;",
            "- authorize official-result and ranking flags; and",
            "- authorize the GitHub Release and version tag.",
            "",
        ]
    )
    return "\n".join([
        "# Power Benchmark 1.0 Final Package Notes",
        "",
        "## Status",
        "",
        status,
        "",
        "## No-rerun adoption",
        "",
        "Power 1.0 adopts the exact six F5 result files produced by App 0.8.0 build 10.",
        "The App, workload prompts, timing boundaries, metric formulas, eligibility rules, result schema, and validator are unchanged from RC1.",
        "Raw result identities and bytes remain `1.0.0-rc.1`; the final publication layer binds them by result ID and SHA-256 instead of rewriting them.",
        "",
        "## Candidate ranking coverage",
        "",
        f"- {dataset['resultCount']} retained physical-device results;",
        f"- {dataset['candidateRankedResultCount']} primary-metric-eligible result rows;",
        f"- {dataset['configurationCount']} exact model artifacts;",
        "- one iPhone15,3, one iOS build, and one MLX Swift LM runtime; and",
        "- one retained Short Interaction response-ineligible row.",
        "",
    ] + decision_lines + [
        "Ship deployment profiles and integration recipes follow after the Power 1.0 publication.",
        "",
    ])


def build_dataset(release_path: Path, adoption_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    release = verify_release(release_path, adoption_path)
    adoption = load_json(adoption_path)
    verified = verify_entries(adoption)
    rows = [normalize_row(entry, raw, report, release, adoption) for entry, raw, report in verified]
    rows.sort(key=lambda row: (row["configuration"]["model"]["artifactID"], row["workload"]["id"]))
    candidate_ranked = sum(row["rankingEligibility"]["candidateEligible"] for row in rows)
    active_ranked = sum(row["rankingEligibility"]["active"] for row in rows)
    return {
        "schemaVersion": "suite-b-power-leaderboard-1.0",
        "generatedAt": release["preparedAt"],
        "benchmarkRelease": {"id": release["releaseID"], "version": release["releaseVersion"]},
        "sourceEvidenceRelease": adoption["sourceEvidenceRelease"],
        "publication": {
            "status": release["status"],
            "officialResultEligible": release["officialResultEligible"],
            "rankingAuthorized": release["rankingAuthorized"],
            "publicationAuthorized": release["publicationAuthorized"],
            "tagAuthorized": release["tagAuthorized"],
        },
        "resultCount": len(rows),
        "candidateRankedResultCount": candidate_ranked,
        "activeRankedResultCount": active_ranked,
        "configurationCount": len({row["configuration"]["model"]["artifactID"] for row in rows}),
        "results": rows,
    }, adoption


def write_outputs(output: Path, release_path: Path, adoption_path: Path) -> dict[str, Any]:
    dataset, adoption = build_dataset(release_path, adoption_path)
    output.mkdir(parents=True, exist_ok=True)
    normalized = output / "normalized-results.json"
    leaderboard = output / "LEADERBOARD.md"
    notes = output / "RELEASE-NOTES.md"
    readme = output / "README.md"
    normalized.write_text(json.dumps(dataset, indent=2, sort_keys=True) + "\n")
    leaderboard.write_text(render_leaderboard(dataset))
    notes.write_text(render_release_notes(dataset, adoption))
    active = bool(
        dataset["publication"]["officialResultEligible"]
        and dataset["publication"]["rankingAuthorized"]
        and dataset["publication"]["publicationAuthorized"]
        and dataset["activeRankedResultCount"] > 0
    )
    status = (
        "These files form the published Power Benchmark 1.0 package and activate the workload-specific official ranking."
        if active
        else "Until the final publication flags are approved, these files are a review candidate and do not activate an official ranking or release tag."
    )
    readme.write_text(
        "# Power Benchmark 1.0\n\n"
        "This directory is generated from immutable F5 RC1 evidence through the "
        "hash-bound no-rerun adoption manifest.\n\n"
        f"{status}\n\n"
        "Regenerate and verify from the repository root:\n\n"
        "```bash\n"
        "python3 scripts/generate_suite_b_power_release.py\n"
        "shasum -a 256 -c results/suite-b-power-1.0/SHA256SUMS\n"
        "```\n"
    )
    checksum_paths = [
        ("results/suite-b-power-1.0/evidence-adoption.json", adoption_path),
        ("results/suite-b-power-1.0/normalized-results.json", normalized),
        ("results/suite-b-power-1.0/LEADERBOARD.md", leaderboard),
        ("results/suite-b-power-1.0/RELEASE-NOTES.md", notes),
        ("results/suite-b-power-1.0/README.md", readme),
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
        f"{dataset['candidateRankedResultCount']} candidate-ranked; "
        f"{dataset['activeRankedResultCount']} active-ranked"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
