#!/usr/bin/env python3
"""Generate the Power 2 certification App catalog from pinned candidate data."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
NEXT_PATH = ROOT / "products" / "power" / "next.json"
OUTPUT_PATH = ROOT / "apps" / "ios" / "Power2CandidateCatalog.generated.swift"


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repo_path(relative_path: str) -> Path:
    pure_path = PurePosixPath(relative_path)
    if pure_path.is_absolute() or ".." in pure_path.parts:
        raise ValueError(f"unsafe repository path: {relative_path}")
    path = (ROOT / pure_path).resolve()
    path.relative_to(ROOT.resolve())
    return path


def _reference(value: Any, label: str) -> tuple[Path, dict[str, Any]]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    relative_path = value.get("path")
    digest = value.get("sha256")
    if not isinstance(relative_path, str) or not relative_path:
        raise ValueError(f"{label} has no path")
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise ValueError(f"{label} has an invalid SHA-256")
    path = _repo_path(relative_path)
    if _sha256(path) != digest:
        raise ValueError(f"{label} digest mismatch: {relative_path}")
    return path, value


def _swift_string(value: str) -> str:
    if any(ord(character) > 0x7F for character in value):
        raise ValueError("generated Swift identity strings must be ASCII")
    return json.dumps(value)


def _data_base64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def _asset_by_path(
    assets: list[Any],
    relative_path: str,
    role: str,
) -> dict[str, Any]:
    matches = [
        asset
        for asset in assets
        if isinstance(asset, dict)
        and asset.get("path") == relative_path
        and asset.get("role") == role
    ]
    if len(matches) != 1:
        raise ValueError(
            f"program manifest must pin exactly one {role}: {relative_path}"
        )
    _reference(matches[0], f"program {role}")
    return matches[0]


def _load_catalog() -> dict[str, Any]:
    candidate = _load_json(NEXT_PATH)
    state = candidate.get("state")
    app_release = candidate.get("appRelease")
    if (
        candidate.get("schemaVersion") != "power-release-plan-1.0.0"
        or state not in (
            "runner-certification-required",
            "app-release-rehearsal-required",
            "activated",
        )
        or candidate.get("publicIntakeOpen") is not False
        or (
            state == "activated"
            and not isinstance(app_release, dict)
        )
        or (
            state != "activated"
            and app_release is not None
        )
    ):
        raise ValueError(
            "App catalog accepts only a closed or completed release plan"
        )

    stack_path, _ = _reference(
        candidate.get("measurementStack"),
        "candidate measurement stack",
    )
    stack = _load_json(stack_path)
    program_path, program_reference = _reference(
        stack.get("program"),
        "measurement stack program",
    )
    target_path, target_reference = _reference(
        stack.get("target"),
        "measurement stack target",
    )
    runner_path, runner_reference = _reference(
        candidate.get("runnerComponents"),
        "candidate runner",
    )
    program_manifest = _load_json(program_path)
    target_manifest = _load_json(target_path)
    runner_manifest = _load_json(runner_path)

    if program_manifest.get("status") != "migration-draft":
        raise ValueError("program is not a migration draft")
    if target_manifest.get("status") != "migration-draft":
        raise ValueError("target is not a migration draft")
    if (
        runner_manifest.get("schemaVersion")
        != "power-runner-component-manifest-1.0.0"
    ):
        raise ValueError("runner candidate manifest is unsupported")
    if state == "runner-certification-required":
        certificate_id = candidate.get(
            "runnerCertificationCandidateID"
        )
    else:
        certificate_path, certificate_reference = _reference(
            candidate.get("runnerCertificate"),
            "issued Runner certificate",
        )
        certificate = _load_json(certificate_path)
        if (
            stack.get("runnerCertificate") != certificate_reference
            or certificate.get("state") != "active"
            or certificate.get("runnerComponents")
            != candidate.get("runnerComponents")
        ):
            raise ValueError(
                "issued Runner certificate is inconsistent with the stack"
            )
        certificate_id = certificate.get("certificateID")
    if not isinstance(certificate_id, str) or not certificate_id:
        raise ValueError("next release has no Runner certificate ID")

    assets = program_manifest.get("assets")
    if not isinstance(assets, list):
        raise ValueError("program manifest has no assets")
    contract_assets = [
        asset
        for asset in assets
        if isinstance(asset, dict) and asset.get("role") == "program-contract"
    ]
    if len(contract_assets) != 1:
        raise ValueError("program manifest must pin one contract")
    contract_path, _ = _reference(
        contract_assets[0],
        "program contract",
    )
    contract = _load_json(contract_path)

    workloads: list[dict[str, Any]] = []
    for index, workload_reference in enumerate(contract.get("workloads", [])):
        if not isinstance(workload_reference, dict):
            raise ValueError(f"invalid workload reference {index}")
        workload_relative_path = workload_reference.get("path")
        if not isinstance(workload_relative_path, str):
            raise ValueError(f"workload reference {index} has no path")
        workload_asset = _asset_by_path(
            assets,
            workload_relative_path,
            "workload",
        )
        workload_path = _repo_path(workload_relative_path)
        workload = _load_json(workload_path)
        fixture = workload.get("fixture")
        if not isinstance(fixture, dict):
            raise ValueError(f"workload {index} has no fixture")
        fixture_relative_path = fixture.get("path")
        if not isinstance(fixture_relative_path, str):
            raise ValueError(f"workload {index} fixture has no path")
        fixture_asset = _asset_by_path(
            assets,
            fixture_relative_path,
            "fixture",
        )
        if fixture.get("sha256") != fixture_asset.get("sha256"):
            raise ValueError(f"workload {index} fixture digest mismatch")
        if workload.get("workloadID") != workload_reference.get("id"):
            raise ValueError(f"workload {index} ID mismatch")
        if workload.get("workloadVersion") != workload_reference.get("version"):
            raise ValueError(f"workload {index} version mismatch")
        workloads.append(
            {
                "id": workload["workloadID"],
                "title": workload["title"],
                "sha256": workload_asset["sha256"],
                "workloadData": _data_base64(workload_path),
                "fixtureData": _data_base64(
                    _repo_path(fixture_relative_path)
                ),
            }
        )
    if not workloads:
        raise ValueError("program contract has no workloads")

    models_value = stack.get("models")
    if not isinstance(models_value, dict):
        raise ValueError("measurement stack has no model registry")
    registry_path, _ = _reference(
        models_value.get("registry"),
        "measurement stack model registry",
    )
    registry = _load_json(registry_path)
    models: list[dict[str, Any]] = []
    for index, entry in enumerate(registry.get("entries", [])):
        manifest_path, entry_reference = _reference(
            entry,
            f"model registry entry {index}",
        )
        manifest = _load_json(manifest_path)
        if manifest.get("status") != "rerun-candidate":
            raise ValueError(f"model entry {index} is not a rerun candidate")
        runtime = manifest.get("runtimeCompatibility")
        if not isinstance(runtime, dict):
            raise ValueError(f"model entry {index} has no runtime compatibility")
        eos_tokens = runtime.get("extraEndOfSequenceTokens")
        if not isinstance(eos_tokens, list) or not all(
            isinstance(token, str) for token in eos_tokens
        ):
            raise ValueError(f"model entry {index} has invalid EOS tokens")
        models.append(
            {
                "id": manifest["registryEntryID"],
                "displayName": manifest["displayName"],
                "registryEntrySHA256": entry_reference["sha256"],
                "artifactID": manifest["artifactID"],
                "artifactRevision": manifest["artifactRevision"],
                "parameterCount": manifest["parameterCount"],
                "quantization": manifest["quantization"],
                "format": manifest["format"],
                "extraEndOfSequenceTokens": eos_tokens,
            }
        )
    if not models:
        raise ValueError("model registry has no rerun candidates")

    return {
        "program": program_reference,
        "target": target_reference,
        "runner": runner_reference,
        "runnerCertificateID": certificate_id,
        "models": models,
        "workloads": workloads,
    }


def _render_model(model: dict[str, Any]) -> str:
    tokens = ", ".join(
        _swift_string(token)
        for token in model["extraEndOfSequenceTokens"]
    )
    return f"""        .init(
            id: {_swift_string(model["id"])},
            displayName: {_swift_string(model["displayName"])},
            identity: .init(
                registryEntryID: {_swift_string(model["id"])},
                registryEntrySHA256: {_swift_string(model["registryEntrySHA256"])},
                artifactID: {_swift_string(model["artifactID"])},
                artifactRevision: {_swift_string(model["artifactRevision"])},
                parameterCount: {model["parameterCount"]},
                quantization: {_swift_string(model["quantization"])},
                format: {_swift_string(model["format"])}
            ),
            extraEndOfSequenceTokens: [{tokens}]
        )"""


def _render_workload(workload: dict[str, Any]) -> str:
    return f"""        .init(
            id: {_swift_string(workload["id"])},
            title: {_swift_string(workload["title"])},
            sha256: {_swift_string(workload["sha256"])},
            workloadDataBase64: {_swift_string(workload["workloadData"])},
            fixtureDataBase64: {_swift_string(workload["fixtureData"])}
        )"""


def render_swift() -> str:
    catalog = _load_catalog()
    program = catalog["program"]
    target = catalog["target"]
    runner = catalog["runner"]
    models = ",\n".join(_render_model(model) for model in catalog["models"])
    workloads = ",\n".join(
        _render_workload(workload) for workload in catalog["workloads"]
    )
    certificate_id = catalog["runnerCertificateID"]
    return f"""// Generated by scripts/generate_power2_app_catalog.py.
// The catalog is for a closed Certification or Official release rehearsal.

import Foundation
import PowerEvidence
import PowerMLXRuntime
import PowerTextProgram

struct Power2CandidateModelDefinition: Identifiable, Sendable {{
    let id: String
    let displayName: String
    let identity: PowerModelIdentity
    let extraEndOfSequenceTokens: [String]

    func descriptor() throws -> PowerMLXModelDescriptor {{
        try .init(
            artifactID: identity.artifactID,
            artifactRevision: identity.artifactRevision,
            extraEndOfSequenceTokens: Set(extraEndOfSequenceTokens)
        )
    }}
}}

struct Power2CandidateWorkloadDefinition: Identifiable, Sendable {{
    let id: String
    let title: String
    let sha256: String
    let workloadDataBase64: String
    let fixtureDataBase64: String

    func workload() throws -> PowerTextWorkload {{
        guard let data = Data(base64Encoded: workloadDataBase64) else {{
            throw Power2CandidateCatalogError.invalidGeneratedData
        }}
        return try PowerTextWorkload.decode(data)
    }}

    func fixture() throws -> String {{
        guard
            let data = Data(base64Encoded: fixtureDataBase64),
            let value = String(data: data, encoding: .utf8)
        else {{
            throw Power2CandidateCatalogError.invalidGeneratedData
        }}
        return value
    }}
}}

enum Power2CandidateCatalogError: Error {{
    case invalidGeneratedData
}}

enum Power2CandidateCatalog {{
    static let program = PowerVersionedIdentity(
        id: {_swift_string(program["id"])},
        version: {_swift_string(program["version"])},
        manifestSHA256: {_swift_string(program["sha256"])}
    )
    static let target = PowerVersionedIdentity(
        id: {_swift_string(target["id"])},
        version: {_swift_string(target["version"])},
        manifestSHA256: {_swift_string(target["sha256"])}
    )
    static let runnerCertificateID = {_swift_string(certificate_id)}

    static let models: [Power2CandidateModelDefinition] = [
{models}
    ]

    static let workloads: [Power2CandidateWorkloadDefinition] = [
{workloads}
    ]
}}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail instead of rewriting a stale generated Swift catalog",
    )
    args = parser.parse_args(argv)
    try:
        expected = render_swift()
    except (KeyError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if args.check:
        try:
            actual = OUTPUT_PATH.read_text(encoding="utf-8")
        except OSError:
            actual = ""
        if actual != expected:
            print(
                "error: apps/ios/Power2CandidateCatalog.generated.swift "
                "is stale",
                file=sys.stderr,
            )
            return 1
        return 0

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(expected, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
