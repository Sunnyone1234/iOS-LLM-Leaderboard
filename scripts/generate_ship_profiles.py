#!/usr/bin/env python3
"""Generate Ship RC1 deployment profiles from published Power 1.0 evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POWER = ROOT / "results/suite-b-power-1.0/normalized-results.json"
DEFAULT_OUTPUT = ROOT / "results/ship-1.0"
SHIP_RELEASE = {
    "id": "ship-deployment-profiles",
    "version": "1.0.0-rc.1",
    "status": "release-candidate",
}
RECIPE_PATH = "examples/mlx-swift/PinnedMLXModel.swift"
METHOD_PATH = "docs/ship-deployment-profiles.md"
EXPECTED_ARTIFACT_REVISIONS = {
    "mlx-community/Qwen3-0.6B-4bit": "73e3e38d981303bc594367cd910ea6eb48349da8",
    "mlx-community/Qwen3-1.7B-4bit": "3b1b1768f8f8cf8351c712464f906e86c2b8269e",
    "mlx-community/Qwen3-4B-3bit": "c4e8054c71facfa84f781cdb7c1ffab3f09f89bf",
}
EXPECTED_RUNTIME = {
    "backend": "MLX/Metal",
    "dependencyVersions": {
        "mlx-swift": "0.31.6@0bb916c67f4b9e5c682cbe02a42c701c93ab5021",
        "swift-huggingface": "swift-huggingface 0.9.0",
        "swift-transformers": "swift-transformers 1.3.0",
    },
    "name": "MLX Swift LM",
    "resolvedRevision": "bd4b7434e6bdb588c7ef55706ff8904cb7fd4c57",
    "version": "3.31.4",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def common_value(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    values = [row["configuration"][key] for row in rows]
    require(all(value == values[0] for value in values), f"inconsistent {key} identity")
    return values[0]


def raw_bundle(row: dict[str, Any]) -> dict[str, Any]:
    path = ROOT / row["source"]["rawPath"]
    require(path.is_file(), f"missing raw evidence: {path}")
    require(sha256(path) == row["source"]["rawSHA256"], f"raw evidence hash mismatch: {path}")
    raw = load_json(path)
    require(raw.get("resultID") == row["resultID"], "raw result identity mismatch")
    return raw


def claim(
    claim_id: str,
    label: str,
    status: str,
    statement: str,
    basis: list[str],
) -> dict[str, Any]:
    return {
        "id": claim_id,
        "label": label,
        "status": status,
        "statement": statement,
        "basis": basis,
    }


def build_claims(
    rows: list[dict[str, Any]],
    raw_by_result: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    active = [row for row in rows if row["rankingEligibility"]["active"]]
    require(active, "a Ship profile requires active Power evidence")

    for row in rows:
        raw = raw_by_result[row["resultID"]]
        preparation = raw.get("modelPreparation", {})
        require(preparation.get("artifactID") == row["configuration"]["model"]["artifactID"], "preparation artifact mismatch")
        require(preparation.get("artifactRevision") == row["configuration"]["model"]["artifactRevision"], "preparation revision mismatch")
        require(preparation.get("eligibleForPerformanceMeasurement") is True, "model preparation was not eligible")
        require(preparation.get("modelLoadCompleted") is True, "model load was not completed")
        require(preparation.get("downloadOccurredDuringSession") is False, "measurement session downloaded a model")

    for row in active:
        raw = raw_by_result[row["resultID"]]
        completed = [attempt for attempt in raw.get("attempts", []) if attempt.get("outcome") == "completed"]
        require(completed, "active Power evidence contains no completed attempts")
        require(all(attempt.get("tokenEvents") for attempt in completed), "completed attempt lacks token events")
        generation = row["configuration"]["generation"]
        require(generation.get("contextPolicy") == "fresh-conversation-per-attempt", "unexpected context policy")
        require(generation.get("kvCachePolicy") == "fresh-kv-cache-per-attempt", "unexpected KV-cache policy")

    result_paths = sorted(row["source"]["rawPath"] for row in rows)
    power_path = "results/suite-b-power-1.0/normalized-results.json"
    app_path = "ios-app/BenchmarkApp/MLXSwiftRuntime.swift"
    recipe_path = RECIPE_PATH
    return [
        claim(
            "physical-device-local-inference",
            "Physical-device local inference",
            "verified",
            "The pinned artifact loaded and produced completed inference attempts on the tested physical iPhone configuration.",
            [power_path, *result_paths],
        ),
        claim(
            "pinned-cached-artifact-load",
            "Pinned cached artifact load",
            "verified",
            "The exact artifact revision loaded from a verified pre-existing cache; no model download occurred during a measurement session.",
            result_paths,
        ),
        claim(
            "runtime-token-stream",
            "Runtime token stream",
            "verified",
            "Completed attempts retained ordered per-token runtime events. This is adapter evidence, not proof of screen-render behavior.",
            result_paths,
        ),
        claim(
            "fresh-attempt-context",
            "Fresh attempt context",
            "verified",
            "Power attempts completed with a fresh conversation and fresh KV cache per attempt.",
            [power_path, *result_paths],
        ),
        claim(
            "model-license-metadata",
            "Model license metadata",
            "verified",
            "The pinned profile records the publisher-provided license identifier and source URL. This is metadata, not legal advice.",
            [power_path],
        ),
        claim(
            "first-run-download-path",
            "First-run download path",
            "implementation-supported",
            "The reference implementation contains a revision-pinned download and cache-verification path, but first-run download was excluded from Power measurements.",
            [app_path, recipe_path],
        ),
        claim(
            "swift-integration-recipe",
            "Swift integration recipe",
            "implementation-supported",
            "A focused recipe mirrors the pinned loader and token-stream boundary used by the tested reference App.",
            [app_path, recipe_path],
        ),
        claim(
            "offline-execution",
            "Offline execution",
            "unknown",
            "Network state was not recorded during measured attempts, so fully offline operation is not claimed.",
            result_paths,
        ),
        claim(
            "generation-cancellation",
            "Generation cancellation",
            "unknown",
            "The published Power evidence does not include a cancelled attempt or a cancellation conformance test.",
            [power_path],
        ),
        claim(
            "bundled-model-distribution",
            "Bundled model distribution",
            "unknown",
            "The published evidence used a Hugging Face cache and does not test bundling model files inside an App distribution.",
            result_paths,
        ),
        claim(
            "minimum-supported-device",
            "Minimum supported device",
            "unknown",
            "Only the tested device is established; no minimum iPhone, iPad, RAM, or OS requirement is inferred.",
            [power_path],
        ),
        claim(
            "app-store-readiness",
            "App Store readiness",
            "unknown",
            "No App Store review, package-size acceptance, or distribution-readiness conclusion is part of this evidence.",
            [METHOD_PATH],
        ),
        claim(
            "privacy-compliance",
            "Privacy compliance",
            "unknown",
            "Local inference alone does not establish an app's data flows, disclosures, permissions, or privacy compliance.",
            [METHOD_PATH],
        ),
    ]


def workload_evidence(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "workloadID": row["workload"]["id"],
        "resultID": row["resultID"],
        "activeInOfficialRanking": row["rankingEligibility"]["active"],
        "primaryMetric": row["primaryMetric"],
        "summary": row["summary"],
        "rawPath": row["source"]["rawPath"],
        "rawSHA256": row["source"]["rawSHA256"],
        "reasonCodes": row["rankingEligibility"]["reasonCodes"],
    }


def profile_id(model: dict[str, Any], runtime: dict[str, Any], device: dict[str, Any]) -> str:
    artifact = model["artifactID"].split("/")[-1].lower().replace(".", "-")
    runtime_id = runtime["name"].lower().replace(" ", "-")
    device_id = device["machineIdentifier"].lower().replace(",", "-")
    return f"ship-{artifact}-{runtime_id}-{runtime['version']}-{device_id}"


def build_dataset(power_path: Path = DEFAULT_POWER) -> dict[str, Any]:
    power = load_json(power_path)
    require(power.get("benchmarkRelease") == {"id": "suite-b-power", "version": "1.0.0"}, "Ship RC1 requires Power 1.0")
    publication = power.get("publication", {})
    require(publication.get("officialResultEligible") is True, "Power results are not official")
    require(publication.get("rankingAuthorized") is True, "Power ranking is not authorized")
    require(publication.get("publicationAuthorized") is True, "Power publication is not authorized")
    rows = power.get("results")
    require(isinstance(rows, list) and len(rows) == 6, "expected the six-result Power 1.0 matrix")
    require(all(row.get("evidence", {}).get("level") == "maintainer-reference" for row in rows), "Ship RC1 requires Maintainer Reference evidence")

    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["configuration"]["model"]["artifactID"], []).append(row)
    require(set(grouped) == set(EXPECTED_ARTIFACT_REVISIONS), "unexpected tested model artifact set")

    profiles: list[dict[str, Any]] = []
    for artifact_id, group in sorted(grouped.items()):
        model = common_value(group, "model")
        runtime = common_value(group, "runtime")
        device = common_value(group, "device")
        require(
            model["artifactRevision"] == EXPECTED_ARTIFACT_REVISIONS[artifact_id],
            f"unexpected tested artifact revision: {artifact_id}",
        )
        require(runtime == EXPECTED_RUNTIME, "unexpected tested runtime identity")
        raw_by_result = {row["resultID"]: raw_bundle(row) for row in group}
        active = [row for row in group if row["rankingEligibility"]["active"]]
        memories = [row["summary"]["medianPeakMemoryMiB"] for row in active if row["summary"]["medianPeakMemoryMiB"] is not None]
        require(memories, f"no active memory evidence for {artifact_id}")
        profiles.append(
            {
                "profileID": profile_id(model, runtime, device),
                "configuration": {
                    "model": model,
                    "runtime": runtime,
                    "device": device,
                },
                "evidence": {
                    "level": "maintainer-reference",
                    "sourceResultIDs": sorted(row["resultID"] for row in group),
                    "activePowerResultIDs": sorted(row["resultID"] for row in active),
                    "sourceResultCount": len(group),
                    "activePowerResultCount": len(active),
                },
                "observedConstraints": {
                    "artifactRepositorySizeBytes": model["artifactRepositorySizeBytes"],
                    "maximumReportedMedianPeakMemoryMiB": max(memories),
                    "memoryDefinition": "maximum of eligible Power workload median TASK_VM_INFO.phys_footprint peaks; not a minimum-memory requirement",
                    "testedDeviceOnly": True,
                    "minimumSupportedDevice": None,
                },
                "powerEvidence": sorted(
                    (workload_evidence(row) for row in group),
                    key=lambda item: item["workloadID"],
                ),
                "deploymentClaims": build_claims(group, raw_by_result),
                "integrationRecipe": {
                    "runtime": "MLX Swift LM 3.31.4",
                    "path": RECIPE_PATH,
                    "readmePath": "examples/mlx-swift/README.md",
                },
                "limitations": [
                    "single-device-single-runtime-reference-profile",
                    "power-evidence-does-not-evaluate-response-quality",
                    "observed-memory-is-not-a-minimum-memory-requirement",
                    "offline-distribution-privacy-and-app-store-readiness-remain-unverified",
                    "license-metadata-requires-developer-review",
                ],
            }
        )

    return {
        "schemaVersion": "1.0.0-rc.1",
        "shipRelease": SHIP_RELEASE,
        "sourcePowerRelease": {
            "id": power["benchmarkRelease"]["id"],
            "version": power["benchmarkRelease"]["version"],
            "path": "results/suite-b-power-1.0/normalized-results.json",
        },
        "sourcePowerPublicationStatus": power["publication"]["status"],
        "profileCount": len(profiles),
        "hasDeploymentScore": False,
        "statusVocabulary": {
            "verified": "Directly supported by consistency-checked Power evidence or source metadata bound to that evidence.",
            "implementation-supported": "Present in the reviewed reference implementation or recipe, but not validated as a benchmark claim.",
            "unknown": "The current evidence does not establish the claim.",
        },
        "profiles": profiles,
    }


def markdown_escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def format_bytes(value: int) -> str:
    return f"{value / 1_000_000_000:.2f} GB"


def render_profiles(dataset: dict[str, Any]) -> str:
    lines = [
        "# Ship Deployment Profiles 1.0 RC1",
        "",
        "These profiles translate published Power 1.0 evidence into deployment guidance. They define no Ship score and make no App Store, privacy, offline, minimum-device, or legal conclusion.",
        "",
        "| Model | Exact tested profile | Artifact | Observed memory | Verified | Implementation-supported | Unknown | Evidence |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for profile in dataset["profiles"]:
        config = profile["configuration"]
        model = config["model"]
        runtime = config["runtime"]
        device = config["device"]
        counts = {status: 0 for status in ("verified", "implementation-supported", "unknown")}
        for item in profile["deploymentClaims"]:
            counts[item["status"]] += 1
        exact = (
            f"{model['artifactID']}@{model['artifactRevision'][:12]}; "
            f"{runtime['name']} {runtime['version']}; "
            f"{device['displayName']}; {device['systemName']} {device['systemVersion']} ({device['systemBuild']})"
        )
        memory = profile["observedConstraints"]["maximumReportedMedianPeakMemoryMiB"]
        lines.append(
            f"| {markdown_escape(model['displayName'])} ({markdown_escape(model['quantization'])}) "
            f"| {markdown_escape(exact)} | {format_bytes(model['artifactRepositorySizeBytes'])} "
            f"| {memory:.0f} MiB | {counts['verified']} | {counts['implementation-supported']} "
            f"| {counts['unknown']} | `{profile['profileID']}` |"
        )
    lines.extend(
        [
            "",
            "`Observed memory` is the largest eligible Power workload median peak for the profile. It is not a minimum RAM requirement.",
            "",
            "See [the method](../../docs/ship-deployment-profiles.md), [machine-readable profiles](deployment-profiles.json), and [the MLX Swift recipe](../../examples/mlx-swift/README.md).",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(
    output: Path = DEFAULT_OUTPUT,
    power_path: Path = DEFAULT_POWER,
) -> dict[str, Any]:
    dataset = build_dataset(power_path)
    output.mkdir(parents=True, exist_ok=True)
    profiles = output / "deployment-profiles.json"
    table = output / "PROFILES.md"
    readme = output / "README.md"
    profiles.write_text(json.dumps(dataset, indent=2, sort_keys=True) + "\n")
    table.write_text(render_profiles(dataset))
    readme.write_text(
        "# Ship Deployment Profiles 1.0 RC1\n\n"
        "This release candidate is generated from the published, immutable Power 1.0 evidence matrix. It adds deployment guidance and a tested-runtime integration recipe without changing Power results, protocols, schemas, workloads, rankings, or the benchmark App.\n\n"
        "Ship is profile-based and has no aggregate score. `Unknown` is preserved wherever the current evidence cannot support a claim.\n\n"
        "Regenerate and verify from the repository root:\n\n"
        "```bash\n"
        "python3 scripts/generate_ship_profiles.py\n"
        "shasum -a 256 -c results/ship-1.0/SHA256SUMS\n"
        "```\n"
    )
    checksum_paths = [
        ("results/ship-1.0/deployment-profiles.json", profiles),
        ("results/ship-1.0/PROFILES.md", table),
        ("results/ship-1.0/README.md", readme),
        ("docs/ship-deployment-profiles.md", ROOT / METHOD_PATH),
        (RECIPE_PATH, ROOT / RECIPE_PATH),
        ("examples/mlx-swift/README.md", ROOT / "examples/mlx-swift/README.md"),
        ("results/suite-b-power-1.0/normalized-results.json", power_path),
    ]
    (output / "SHA256SUMS").write_text(
        "".join(f"{sha256(path)}  {label}\n" for label, path in checksum_paths)
    )
    return dataset


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--power", type=Path, default=DEFAULT_POWER)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        dataset = write_outputs(args.output, args.power)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"error: {error}")
        return 1
    print(f"wrote {dataset['profileCount']} Ship deployment profiles; no score")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
