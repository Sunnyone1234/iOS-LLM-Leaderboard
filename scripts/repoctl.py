#!/usr/bin/env python3
"""Repository control plane for versioned benchmark products.

Verification is always read-only. The explicit ``activate-power`` operation
reviews one exact Official result and stages the complete activation file set;
it writes only when ``--write`` is supplied.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
POWER_REGISTRY_PATH = "products/power/registry.json"
POWER_CURRENT_PATH = "products/power/current.json"

# Active Power 2.0 JSON may not dispatch to or derive identity from the retired
# Power major. Historical files remain elsewhere for audit only.
FORBIDDEN_ACTIVE_REFERENCE_FRAGMENTS = (
    "power-1.",
    "suite-b",
    "benchmarks/",
    "submissions/",
    "results/",
    "1.1.0-rc",
)


class VerificationError(ValueError):
    """Raised when a candidate stack is incomplete, inconsistent, or unsafe."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise VerificationError(f"missing JSON asset: {path}") from error
    except json.JSONDecodeError as error:
        raise VerificationError(f"invalid JSON in {path}: {error}") from error
    if not isinstance(value, dict):
        raise VerificationError(f"expected a JSON object: {path}")
    return value


def _repo_path(relative_path: str) -> Path:
    pure_path = PurePosixPath(relative_path)
    if pure_path.is_absolute() or ".." in pure_path.parts:
        raise VerificationError(f"unsafe repository path: {relative_path}")
    resolved = (ROOT / pure_path).resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as error:
        raise VerificationError(
            f"path escapes repository root: {relative_path}"
        ) from error
    return resolved


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_pinned_asset(reference: dict[str, Any], context: str) -> Path:
    relative_path = reference.get("path")
    expected_digest = reference.get("sha256")
    if not isinstance(relative_path, str) or not relative_path:
        raise VerificationError(f"{context} has no path")
    if (
        not isinstance(expected_digest, str)
        or len(expected_digest) != 64
        or any(character not in "0123456789abcdef" for character in expected_digest)
    ):
        raise VerificationError(f"{context} has an invalid SHA-256")

    path = _repo_path(relative_path)
    if not path.is_file():
        raise VerificationError(f"{context} does not exist: {relative_path}")
    actual_digest = _sha256(path)
    if actual_digest != expected_digest:
        raise VerificationError(
            f"{context} digest mismatch: expected {expected_digest}, "
            f"found {actual_digest}"
        )
    return path


def _walk_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_strings(child)


def _reject_legacy_references(
    documents: Iterable[tuple[str, dict[str, Any]]],
) -> None:
    for label, document in documents:
        for value in _walk_strings(document):
            lowered = value.lower()
            for fragment in FORBIDDEN_ACTIVE_REFERENCE_FRAGMENTS:
                if fragment in lowered:
                    raise VerificationError(
                        f"active Power 2.0 asset {label} references retired "
                        f"surface {fragment!r}: {value!r}"
                    )


def _verify_program_manifest(
    manifest_path: Path,
    manifest: dict[str, Any],
) -> tuple[list[tuple[str, dict[str, Any]]], int]:
    if manifest.get("noLegacyDependencies") is not True:
        raise VerificationError(
            "program manifest must declare noLegacyDependencies=true"
        )
    if manifest.get("publicIntakeOpen") is not False:
        raise VerificationError("draft program must keep public intake closed")

    assets = manifest.get("assets")
    if not isinstance(assets, list) or not assets:
        raise VerificationError("program manifest has no pinned assets")

    documents: list[tuple[str, dict[str, Any]]] = [
        (str(manifest_path.relative_to(ROOT)), manifest)
    ]
    listed_paths: set[Path] = set()
    for index, reference in enumerate(assets):
        if not isinstance(reference, dict):
            raise VerificationError(
                f"program manifest asset {index} is not an object"
            )
        asset_path = _verify_pinned_asset(
            reference, f"program manifest asset {index}"
        )
        if asset_path in listed_paths:
            raise VerificationError(
                f"program manifest pins an asset twice: {asset_path}"
            )
        listed_paths.add(asset_path)
        if asset_path.suffix == ".json":
            documents.append(
                (str(asset_path.relative_to(ROOT)), _load_json(asset_path))
            )

    version_root = manifest_path.parent
    actual_paths = {
        path.resolve()
        for path in version_root.rglob("*")
        if path.is_file() and path.resolve() != manifest_path.resolve()
    }
    if listed_paths != actual_paths:
        missing = sorted(
            str(path.relative_to(ROOT)) for path in actual_paths - listed_paths
        )
        stale = sorted(
            str(path.relative_to(ROOT)) for path in listed_paths - actual_paths
        )
        raise VerificationError(
            "program manifest does not exactly cover the version directory; "
            f"unlisted={missing}, stale={stale}"
        )

    return documents, len(assets)


def _verify_workload_fixtures(
    contract: dict[str, Any],
    documents_by_path: dict[str, dict[str, Any]],
) -> None:
    workloads = contract.get("workloads")
    if not isinstance(workloads, list) or not workloads:
        raise VerificationError("program contract has no workloads")
    for workload_reference in workloads:
        if not isinstance(workload_reference, dict):
            raise VerificationError("invalid workload reference")
        workload_path = workload_reference.get("path")
        if not isinstance(workload_path, str):
            raise VerificationError("workload reference has no path")
        workload = documents_by_path.get(workload_path)
        if workload is None:
            raise VerificationError(
                f"workload is not pinned by the program manifest: {workload_path}"
            )
        if workload.get("workloadID") != workload_reference.get("id"):
            raise VerificationError(f"workload ID mismatch: {workload_path}")
        if workload.get("workloadVersion") != workload_reference.get("version"):
            raise VerificationError(
                f"workload version mismatch: {workload_path}"
            )

        fixture = workload.get("fixture")
        if not isinstance(fixture, dict):
            raise VerificationError(f"workload has no fixture: {workload_path}")
        _verify_pinned_asset(fixture, f"fixture for {workload_path}")


def _verify_workload_measurement_modes(
    contract: dict[str, Any],
    documents_by_path: dict[str, dict[str, Any]],
) -> None:
    payload_schema = next(
        (
            document
            for path, document in documents_by_path.items()
            if PurePosixPath(path).name
            == "text-generation-payload.schema.json"
        ),
        None,
    )
    if not isinstance(payload_schema, dict):
        raise VerificationError("program has no text payload schema")
    try:
        allowed_modes = set(
            payload_schema["properties"]["measurementMode"]["enum"]
        )
    except (KeyError, TypeError) as error:
        raise VerificationError(
            "text payload schema has no measurement-mode enum"
        ) from error
    if not allowed_modes or not all(
        isinstance(mode, str) for mode in allowed_modes
    ):
        raise VerificationError(
            "text payload schema has an invalid measurement-mode enum"
        )

    for workload_reference in contract["workloads"]:
        workload_path = workload_reference["path"]
        workload = documents_by_path[workload_path]
        mode = workload.get("measurementMode")
        if mode not in allowed_modes:
            raise VerificationError(
                f"workload measurement mode is not accepted by its payload "
                f"schema: {workload_path}: {mode!r}"
            )


def _verify_workload_response_contracts(
    contract: dict[str, Any],
    documents_by_path: dict[str, dict[str, Any]],
) -> None:
    for workload_reference in contract["workloads"]:
        workload_path = workload_reference["path"]
        workload = documents_by_path[workload_path]
        response = workload.get("responseContract")
        if response is None:
            continue
        if not isinstance(response, dict):
            raise VerificationError(
                f"workload response contract is invalid: {workload_path}"
            )
        if response.get("affectsMetricEligibility") is not False:
            raise VerificationError(
                "behavior must remain independent from performance metrics: "
                f"{workload_path}"
            )
        if response.get("affectsRecommendationEligibility") is not True:
            raise VerificationError(
                "behavior contract must state its recommendation effect: "
                f"{workload_path}"
            )
        maximum_sentences = response.get("maximumSentences")
        policy = response.get("verificationPolicy")
        if (
            not isinstance(maximum_sentences, int)
            or maximum_sentences < 1
            or not isinstance(policy, dict)
            or not isinstance(
                policy.get("minimumVerifiedMeasuredAttempts"), int
            )
            or policy["minimumVerifiedMeasuredAttempts"] < 1
        ):
            raise VerificationError(
                f"workload response policy is incomplete: {workload_path}"
            )
        concepts = policy.get("concepts")
        contradictions = policy.get("contradictionPhrases")
        if (
            not isinstance(concepts, list)
            or not concepts
            or not isinstance(contradictions, list)
            or not all(
                isinstance(phrase, str) and phrase
                for phrase in contradictions
            )
        ):
            raise VerificationError(
                f"workload response policy is invalid: {workload_path}"
            )
        for concept in concepts:
            groups = (
                concept.get("allOfTermGroups")
                if isinstance(concept, dict)
                else None
            )
            if (
                not isinstance(concept, dict)
                or not isinstance(concept.get("id"), str)
                or not isinstance(groups, list)
                or not groups
                or not all(
                    isinstance(group, list)
                    and group
                    and all(
                        isinstance(term, str) and term
                        for term in group
                    )
                    for group in groups
                )
            ):
                raise VerificationError(
                    f"workload response concept is invalid: {workload_path}"
                )


def _verify_schema_set(
    documents_by_path: dict[str, dict[str, Any]],
) -> int:
    schema_paths = [
        path
        for path in documents_by_path
        if "/schemas/" in path and path.endswith(".schema.json")
    ]
    required_names = {
        "evidence-envelope.schema.json",
        "text-generation-payload.schema.json",
        "submission.schema.json",
        "validation-report.schema.json",
        "review-record.schema.json",
    }
    actual_names = {PurePosixPath(path).name for path in schema_paths}
    if actual_names != required_names:
        raise VerificationError(
            "program schema set mismatch; "
            f"expected={sorted(required_names)}, found={sorted(actual_names)}"
        )
    for path in schema_paths:
        schema = documents_by_path[path]
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            raise VerificationError(
                f"schema does not declare JSON Schema 2020-12: {path}"
            )
        if not isinstance(schema.get("$id"), str):
            raise VerificationError(f"schema has no stable $id: {path}")
    return len(schema_paths)


def _verify_runner_candidate(
    reference: dict[str, Any],
    documents: list[tuple[str, dict[str, Any]]],
) -> tuple[int, bool]:
    manifest_path = _verify_pinned_asset(
        reference, "candidate runner component manifest"
    )
    manifest = _load_json(manifest_path)
    documents.append((str(manifest_path.relative_to(ROOT)), manifest))
    schema_version = manifest.get("schemaVersion")
    if schema_version not in {
        "power-runner-component-manifest-1.0.0-draft.1",
        "power-runner-component-manifest-1.0.0",
    }:
        raise VerificationError(
            "candidate runner has an unsupported component manifest"
        )
    if (
        schema_version
        == "power-runner-component-manifest-1.0.0-draft.1"
        and manifest.get("status") != "migration-draft"
    ):
        raise VerificationError("candidate runner is not a migration draft")
    if (
        schema_version == "power-runner-component-manifest-1.0.0"
        and any(
            key in manifest
            for key in (
                "status",
                "completeForCertification",
                "certificationBlockers",
            )
        )
    ):
        raise VerificationError(
            "lifecycle-neutral Runner manifest contains release state"
        )

    package_reference = manifest.get("packageManifest")
    if not isinstance(package_reference, dict):
        raise VerificationError("candidate runner has no Package.swift pin")
    _verify_pinned_asset(package_reference, "candidate runner Package.swift")
    dependency_lock_reference = manifest.get("resolvedDependencies")
    if not isinstance(dependency_lock_reference, dict):
        raise VerificationError(
            "candidate runner has no Package.resolved pin"
        )
    _verify_pinned_asset(
        dependency_lock_reference,
        "candidate runner Package.resolved",
    )
    runtime_identity_reference = manifest.get("runtimeIdentity")
    if not isinstance(runtime_identity_reference, dict):
        raise VerificationError(
            "candidate runner has no canonical runtime identity"
        )
    runtime_identity_path = _verify_pinned_asset(
        runtime_identity_reference,
        "candidate runner runtime identity",
    )
    runtime_identity = _load_json(runtime_identity_path)
    if (
        runtime_identity.get("schemaVersion")
        != "power-runtime-identity-1.0.0-draft.1"
        or not isinstance(runtime_identity.get("configuration"), dict)
        or runtime_identity["configuration"].get(
            "dependencyLockSHA256"
        )
        != dependency_lock_reference.get("sha256")
    ):
        raise VerificationError(
            "candidate runner runtime identity is inconsistent"
        )

    components = manifest.get("components")
    if not isinstance(components, dict):
        raise VerificationError("candidate runner has no components")
    expected_roots = {
        "evidenceEnvelope": "apps/PowerRunnerKit/Sources/PowerEvidence",
        "runnerCore": "apps/PowerRunnerKit/Sources/PowerRunnerCore",
        "programModule": "apps/PowerRunnerKit/Sources/PowerTextProgram",
        "targetAdapter": "apps/PowerRunnerKit/Sources/PowerAppleTarget",
        "runtimeAdapter": "apps/PowerRunnerKit/Sources/PowerMLXRuntime",
    }
    for component_name, source_root in expected_roots.items():
        component = components.get(component_name)
        if not isinstance(component, dict):
            raise VerificationError(
                f"candidate runner has no {component_name} component"
            )
        if component.get("sourceRoot") != source_root:
            raise VerificationError(
                f"candidate runner {component_name} source root mismatch"
            )
        files = component.get("files")
        expected_digest = component.get("sha256")
        if not isinstance(files, list) or not files:
            raise VerificationError(
                f"candidate runner {component_name} has no source files"
            )
        listed_paths: set[Path] = set()
        for index, file_reference in enumerate(files):
            if not isinstance(file_reference, dict):
                raise VerificationError(
                    f"candidate runner {component_name} file {index} "
                    "is invalid"
                )
            listed_paths.add(
                _verify_pinned_asset(
                    file_reference,
                    f"candidate runner {component_name} file {index}",
                ).resolve()
            )
        actual_paths = {
            path.resolve()
            for path in _repo_path(source_root).glob("*.swift")
            if path.is_file()
        }
        if listed_paths != actual_paths:
            raise VerificationError(
                f"candidate runner {component_name} file coverage mismatch"
            )
        canonical = json.dumps(
            files,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        actual_digest = hashlib.sha256(canonical).hexdigest()
        if expected_digest != actual_digest:
            raise VerificationError(
                f"candidate runner {component_name} aggregate digest "
                "mismatch"
            )

    runtime_adapter = components.get("runtimeAdapter")
    runtime_implemented = isinstance(runtime_adapter, dict)
    if schema_version.endswith("-draft.1"):
        complete = manifest.get("completeForCertification")
        if complete is True and not runtime_implemented:
            raise VerificationError(
                "runner cannot be complete without a Runtime Adapter"
            )
        if complete is not False:
            raise VerificationError(
                "migration candidate must remain incomplete "
                "before certification"
            )
    return len(expected_roots), runtime_implemented


def _verify_app_candidate(
    reference: dict[str, Any],
    documents: list[tuple[str, dict[str, Any]]],
) -> int:
    manifest_path = _verify_pinned_asset(
        reference, "candidate App component manifest"
    )
    manifest = _load_json(manifest_path)
    documents.append((str(manifest_path.relative_to(ROOT)), manifest))
    if (
        manifest.get("schemaVersion")
        != "power-app-component-manifest-1.0.0"
    ):
        raise VerificationError(
            "candidate App has an unsupported component manifest"
        )
    required_pins = {
        "xcodeProject": "apps/ios/PowerBenchmarkApp.xcodeproj/project.pbxproj",
        "infoPlist": "apps/ios/PowerBenchmarkApp/Info.plist",
        "certificationScheme":
            "apps/ios/PowerBenchmarkApp.xcodeproj/xcshareddata/"
            "xcschemes/PowerCertification.xcscheme",
        "officialScheme":
            "apps/ios/PowerBenchmarkApp.xcodeproj/xcshareddata/"
            "xcschemes/PowerOfficial.xcscheme",
        "signingConfiguration":
            "apps/ios/Configuration/Signing.xcconfig",
        "releaseIdentity":
            "apps/ios/Configuration/ReleaseIdentity.json",
        "releaseConfiguration":
            "apps/ios/Configuration/ReleaseIdentity.generated.xcconfig",
        "resolvedDependencies":
            "apps/ios/PowerBenchmarkApp.xcodeproj/"
            "project.xcworkspace/xcshareddata/swiftpm/Package.resolved",
        "supportPackage": "apps/PowerAppKit/Package.swift",
        "supportPackageDependencies": "apps/PowerAppKit/Package.resolved",
    }
    for name, expected_path in required_pins.items():
        pin = manifest.get(name)
        if not isinstance(pin, dict) or pin.get("path") != expected_path:
            raise VerificationError(
                f"candidate App {name} pin is missing or misplaced"
            )
        _verify_pinned_asset(pin, f"candidate App {name}")

    expected_paths = {
        "appShell": {
            *(
                path.resolve()
                for path in (
                    ROOT / "apps" / "ios" / "PowerBenchmarkApp"
                ).glob("*.swift")
            ),
            (
                ROOT
                / "apps"
                / "ios"
                / "Power2ProductIdentity.generated.swift"
            ).resolve(),
            (
                ROOT
                / "apps"
                / "ios"
                / "Power2CandidateCatalog.generated.swift"
            ).resolve(),
            (
                ROOT
                / "apps"
                / "ios"
                / "PowerBenchmarkApp"
                / "Info.plist"
            ).resolve(),
            (
                ROOT
                / "apps"
                / "ios"
                / "Configuration"
                / "Signing.xcconfig"
            ).resolve(),
            (
                ROOT
                / "apps"
                / "ios"
                / "Configuration"
                / "ReleaseIdentity.json"
            ).resolve(),
            (
                ROOT
                / "apps"
                / "ios"
                / "Configuration"
                / "ReleaseIdentity.generated.xcconfig"
            ).resolve(),
        },
        "resultsStore": {
            path.resolve()
            for path in (
                ROOT
                / "apps"
                / "PowerAppKit"
                / "Sources"
                / "PowerResultsStore"
            ).glob("*.swift")
        },
        "submissionKit": {
            path.resolve()
            for path in (
                ROOT
                / "apps"
                / "PowerAppKit"
                / "Sources"
                / "PowerSubmissionKit"
            ).glob("*.swift")
        },
        "githubSubmission": {
            path.resolve()
            for path in (
                ROOT
                / "apps"
                / "PowerAppKit"
                / "Sources"
                / "PowerGitHubSubmission"
            ).glob("*.swift")
        },
        "releasePreflight": {
            path.resolve()
            for path in (
                ROOT
                / "apps"
                / "PowerAppKit"
                / "Sources"
                / "PowerReleasePreflight"
            ).glob("*.swift")
        },
        "runCheckpointStore": {
            path.resolve()
            for path in (
                ROOT
                / "apps"
                / "PowerAppKit"
                / "Sources"
                / "PowerRunCheckpointStore"
            ).glob("*.swift")
        },
    }
    components = manifest.get("components")
    if not isinstance(components, dict):
        raise VerificationError("candidate App has no components")
    if set(components) != set(expected_paths):
        raise VerificationError(
            "candidate App component set does not match the approved design"
        )
    for name, actual_paths in expected_paths.items():
        component = components.get(name)
        if not isinstance(component, dict):
            raise VerificationError(
                f"candidate App has no {name} component"
            )
        files = component.get("files")
        if not isinstance(files, list) or not files:
            raise VerificationError(
                f"candidate App {name} has no source files"
            )
        listed_paths: set[Path] = set()
        for index, file_reference in enumerate(files):
            if not isinstance(file_reference, dict):
                raise VerificationError(
                    f"candidate App {name} file {index} is invalid"
                )
            listed_paths.add(
                _verify_pinned_asset(
                    file_reference,
                    f"candidate App {name} file {index}",
                ).resolve()
            )
        if listed_paths != actual_paths:
            raise VerificationError(
                f"candidate App {name} file coverage mismatch"
            )
        canonical = json.dumps(
            files,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        if component.get("sha256") != hashlib.sha256(
            canonical
        ).hexdigest():
            raise VerificationError(
                f"candidate App {name} aggregate digest mismatch"
            )

    return len(expected_paths)


def _verify_release_candidates(
    candidate: dict[str, Any],
    *,
    measurement_stack_reference: dict[str, Any],
    runner_reference: dict[str, Any],
    runner_certificate_reference: dict[str, Any],
    app_reference: dict[str, Any],
    program_reference: dict[str, Any],
    target_reference: dict[str, Any],
    runner_policy_reference: dict[str, Any],
    documents: list[tuple[str, dict[str, Any]]],
) -> tuple[str, str]:
    runner_candidate_reference = candidate.get(
        "runnerCertificationCandidate"
    )
    app_candidate_reference = candidate.get("appReleaseCandidate")
    if not isinstance(runner_candidate_reference, dict):
        raise VerificationError(
            "Power candidate has no Runner certification candidate"
        )
    if not isinstance(app_candidate_reference, dict):
        raise VerificationError(
            "Power candidate has no App release candidate"
        )

    runner_candidate_path = _verify_pinned_asset(
        runner_candidate_reference,
        "Runner certification candidate",
    )
    app_candidate_path = _verify_pinned_asset(
        app_candidate_reference,
        "App release candidate",
    )
    runner_certificate_path = _verify_pinned_asset(
        runner_certificate_reference,
        "active Runner certificate",
    )
    runner_candidate = _load_json(runner_candidate_path)
    runner_certificate = _load_json(runner_certificate_path)
    app_candidate = _load_json(app_candidate_path)
    documents.extend(
        (
            (
                str(runner_candidate_path.relative_to(ROOT)),
                runner_candidate,
            ),
            (
                str(app_candidate_path.relative_to(ROOT)),
                app_candidate,
            ),
            (
                str(runner_certificate_path.relative_to(ROOT)),
                runner_certificate,
            ),
        )
    )

    if (
        runner_candidate.get("schemaVersion")
        != "power-runner-certificate-candidate-1.0.0-draft.1"
        or runner_candidate.get("state") != "candidate"
    ):
        raise VerificationError(
            "Runner certification candidate is not a closed candidate"
        )
    runner_id = (
        "power2-certification-candidate-"
        + str(runner_reference.get("sha256", ""))[:12]
    )
    active_runner_id = (
        "power2-runner-"
        + str(runner_reference.get("sha256", ""))[:12]
    )
    if runner_candidate.get("certificateID") != runner_id:
        raise VerificationError(
            "Runner certification candidate ID is not component-bound"
        )
    expected_runner_references = {
        "measurementStack": measurement_stack_reference,
        "certificationPolicy": {
            "path": runner_policy_reference.get("path"),
            "sha256": runner_policy_reference.get("sha256"),
        },
        "runnerComponents": runner_reference,
        "activeCertificate": runner_certificate_reference,
    }
    for field, expected in expected_runner_references.items():
        if runner_candidate.get(field) != expected:
            raise VerificationError(
                f"Runner certification candidate {field} mismatch"
            )
    if (
        runner_candidate.get("programManifestSHA256")
        != program_reference.get("sha256")
        or runner_candidate.get("targetManifestSHA256")
        != target_reference.get("sha256")
    ):
        raise VerificationError(
            "Runner certification candidate Program or Target mismatch"
        )

    runner_manifest = _load_json(
        _verify_pinned_asset(
            runner_reference,
            "Runner component manifest for certification",
        )
    )
    runtime_reference = runner_manifest.get("runtimeIdentity")
    if (
        not isinstance(runtime_reference, dict)
        or runner_candidate.get("runtimeIdentity") != runtime_reference
    ):
        raise VerificationError(
            "Runner certification candidate runtime reference mismatch"
        )
    runtime = _load_json(
        _verify_pinned_asset(
            runtime_reference,
            "Runner certification runtime identity",
        )
    )
    expected_runtime = {
        key: runtime.get(key)
        for key in (
            "name",
            "version",
            "resolvedRevision",
            "backend",
            "configuration",
        )
    }
    if runner_candidate.get("runtime") != expected_runtime:
        raise VerificationError(
            "Runner certification candidate runtime value mismatch"
        )
    components = runner_manifest.get("components")
    expected_component_digests = {
        name: components.get(name, {}).get("sha256")
        for name in (
            "runnerCore",
            "programModule",
            "targetAdapter",
            "runtimeAdapter",
            "evidenceEnvelope",
        )
    } if isinstance(components, dict) else {}
    if runner_candidate.get("componentSHA256") != expected_component_digests:
        raise VerificationError(
            "Runner certification candidate component digest mismatch"
        )
    runner_verification = runner_candidate.get("verification")
    required_runner_automated_checks = (
        "sourceAndDependencyIntegrity",
        "unitTests",
        "schemaAndFixtureIntegrity",
        "deterministicSerialization",
        "failurePreservation",
        "genericIOSReleaseBuild",
    )
    if (
        not isinstance(runner_verification, dict)
        or any(
            runner_verification.get(check) != "pass"
            for check in required_runner_automated_checks
        )
        or runner_verification.get("physicalDeviceSmokeRun") != "pass"
        or runner_verification.get("rawResultReview") != "pass"
    ):
        raise VerificationError(
            "Runner certification candidate verification state is unsafe"
        )
    if runner_candidate.get("issuanceBlockedBy") != []:
        raise VerificationError(
            "Runner certification candidate still reports issuance blockers"
        )

    if (
        runner_certificate.get("schemaVersion")
        != "power-runner-certificate-1.0.0-rc.1"
        or runner_certificate.get("state") != "active"
        or runner_certificate.get("certificateID") != active_runner_id
        or runner_certificate.get("certificationPolicy")
        != expected_runner_references["certificationPolicy"]
        or runner_certificate.get("runnerComponents") != runner_reference
        or runner_certificate.get("programManifestSHA256")
        != program_reference.get("sha256")
        or runner_certificate.get("targetManifestSHA256")
        != target_reference.get("sha256")
        or runner_certificate.get("runtimeIdentity") != runtime_reference
        or runner_certificate.get("runtime") != expected_runtime
        or runner_certificate.get("componentSHA256")
        != expected_component_digests
    ):
        raise VerificationError(
            "active Runner certificate identity is not source-bound"
        )
    active_verification = runner_certificate.get("verification")
    required_active_checks = (
        *required_runner_automated_checks,
        "physicalDeviceSmokeRun",
        "rawResultReview",
    )
    if (
        not isinstance(active_verification, dict)
        or any(
            active_verification.get(check) != "pass"
            for check in required_active_checks
        )
    ):
        raise VerificationError(
            "active Runner certificate has incomplete verification"
        )
    certification_evidence = runner_certificate.get(
        "certificationEvidence"
    )
    candidate_evidence = runner_candidate.get("certificationEvidence")
    if (
        not isinstance(certification_evidence, dict)
        or not isinstance(candidate_evidence, dict)
        or certification_evidence.get("candidateCertificateID")
        != runner_id
        or {
            "result": certification_evidence.get("result"),
            "review": certification_evidence.get("review"),
        }
        != candidate_evidence
    ):
        raise VerificationError(
            "Runner certification evidence references are inconsistent"
        )
    certification_result_path = _verify_pinned_asset(
        certification_evidence.get("result"),
        "Runner certification result",
    )
    certification_review_path = _verify_pinned_asset(
        certification_evidence.get("review"),
        "Runner certification review",
    )
    certification_stack_path = _verify_pinned_asset(
        certification_evidence.get("measurementStack"),
        "Runner certification measurement stack",
    )
    certification_result = _load_json(certification_result_path)
    certification_review = _load_json(certification_review_path)
    certification_stack = _load_json(certification_stack_path)
    documents.extend(
        (
            (
                str(certification_result_path.relative_to(ROOT)),
                certification_result,
            ),
            (
                str(certification_review_path.relative_to(ROOT)),
                certification_review,
            ),
            (
                str(certification_stack_path.relative_to(ROOT)),
                certification_stack,
            ),
        )
    )
    if (
        certification_result.get("runnerCertificateID") != runner_id
        or certification_review.get("runnerCertificateID") != runner_id
        or certification_review.get("status") != "pass"
        or certification_review.get("physicalDeviceSmokeRun") != "pass"
        or certification_review.get("rawResultReview") != "pass"
        or certification_review.get("publishable") is not False
        or certification_review.get("rankingEligible") is not False
        or certification_review.get("sourceResultSHA256")
        != certification_evidence["result"].get("sha256")
        or runner_certificate.get("issuedAt")
        != certification_review.get("reviewedAt")
        or certification_stack.get("runnerCertificate") is not None
    ):
        raise VerificationError(
            "Runner certification evidence is not issuance-safe"
        )

    app_rehearsals = candidate.get("appReleaseRehearsalEvidence")
    if not isinstance(app_rehearsals, list) or not app_rehearsals:
        raise VerificationError(
            "Power candidate has no retained App release rehearsal evidence"
        )
    reviewed_app_releases: list[dict[str, Any]] = []
    for index, evidence in enumerate(app_rehearsals):
        if not isinstance(evidence, dict):
            raise VerificationError(
                f"App release rehearsal evidence {index} is invalid"
            )
        source_commit = evidence.get("sourceCommit")
        if (
            not isinstance(source_commit, str)
            or len(source_commit) != 40
            or any(
                character not in "0123456789abcdef"
                for character in source_commit
            )
        ):
            raise VerificationError(
                f"App release rehearsal evidence {index} has no source commit"
            )
        historical_app_reference = evidence.get("appComponents")
        result_reference = evidence.get("result")
        review_reference = evidence.get("review")
        if not all(
            isinstance(reference, dict)
            for reference in (
                historical_app_reference,
                result_reference,
                review_reference,
            )
        ):
            raise VerificationError(
                f"App release rehearsal evidence {index} is incomplete"
            )
        historical_app_path = _verify_pinned_asset(
            historical_app_reference,
            f"App release rehearsal {index} component manifest",
        )
        result_path = _verify_pinned_asset(
            result_reference,
            f"App release rehearsal {index} result",
        )
        review_path = _verify_pinned_asset(
            review_reference,
            f"App release rehearsal {index} review",
        )
        historical_app = _load_json(historical_app_path)
        result = _load_json(result_path)
        review = _load_json(review_path)
        review_validator = review.get("validator")
        documents.extend(
            (
                (
                    str(historical_app_path.relative_to(ROOT)),
                    historical_app,
                ),
                (str(result_path.relative_to(ROOT)), result),
                (str(review_path.relative_to(ROOT)), review),
            )
        )
        result_app_release = result.get("appRelease")
        if (
            historical_app.get("schemaVersion")
            != "power-app-component-manifest-1.0.0-draft.1"
            or historical_app.get("status") != "migration-draft"
            or not isinstance(result_app_release, dict)
            or result_app_release.get("sourceRevision")
            != historical_app_reference.get("sha256")
            or result_app_release.get(
                "embeddedMeasurementStackSHA256"
            )
            != measurement_stack_reference.get("sha256")
            or result.get("runnerCertificateID") != active_runner_id
            or review.get("appRelease") != result_app_release
            or review.get("runnerCertificateID") != active_runner_id
            or not isinstance(review_validator, dict)
            or review_validator.get("sourceRevision")
            != source_commit
            or review.get("sourceResultSHA256")
            != result_reference.get("sha256")
            or review.get("status") != "pass"
            or review.get("physicalDeviceEndToEndRehearsal") != "pass"
            or review.get("classification") != "auto-accept"
            or review.get("publishable") is not False
            or review.get("rankingEligible") is not False
        ):
            raise VerificationError(
                f"App release rehearsal evidence {index} is not audit-safe"
            )
        reviewed_app_releases.append(result_app_release)

    if (
        app_candidate.get("schemaVersion")
        != "power-app-release-candidate-1.0.0-draft.1"
        or app_candidate.get("state") != "candidate"
    ):
        raise VerificationError(
            "App release candidate is not a closed candidate"
        )
    app_manifest = _load_json(
        _verify_pinned_asset(
            app_reference,
            "App component manifest for release candidate",
        )
    )
    app_identity = _load_json(
        _verify_pinned_asset(
            app_manifest.get("releaseIdentity"),
            "Power App build identity",
        )
    )
    build_kinds = app_identity.get("buildKinds")
    official_identity = (
        build_kinds.get("official")
        if isinstance(build_kinds, dict)
        else None
    )
    app_version = app_identity.get("version")
    app_build = app_identity.get("build")
    if (
        app_identity.get("schemaVersion")
        != "power-app-build-identity-1.0.0-draft.1"
        or not isinstance(app_version, str)
        or not isinstance(app_build, str)
        or not isinstance(official_identity, dict)
    ):
        raise VerificationError("Power App build identity is incomplete")

    app_digest = app_reference.get("sha256")
    if (
        app_candidate.get("releaseID")
        != f"power-app-{app_version}-candidate-" + str(app_digest)[:12]
        or app_candidate.get("sourceRevision") != app_digest
        or app_candidate.get("appComponents") != app_reference
        or app_candidate.get("embeddedMeasurementStack")
        != measurement_stack_reference
        or app_candidate.get("supportedRunnerCertificateIDs")
        != [active_runner_id]
    ):
        raise VerificationError(
            "App release candidate identity is not source-bound"
        )
    if (
        app_candidate.get("version") != app_version
        or app_candidate.get("build") != app_build
        or app_candidate.get("buildConfiguration") != "Official"
        or app_candidate.get("bundleIdentifier")
        != official_identity.get("bundleIdentifier")
    ):
        raise VerificationError(
            "App release candidate build identity is inconsistent"
        )
    app_verification = app_candidate.get("verification")
    exact_app_rehearsal_passed = any(
        app_release.get("version") == app_version
        and app_release.get("build") == app_build
        and app_release.get("sourceRevision") == app_digest
        and app_release.get("embeddedMeasurementStackSHA256")
        == measurement_stack_reference.get("sha256")
        for app_release in reviewed_app_releases
    )
    if (
        not isinstance(app_verification, dict)
        or app_verification.get("sourceAndDependencyIntegrity") != "pass"
        or app_verification.get("genericIOSReleaseBuild") != "pass"
        or app_verification.get("physicalDeviceEndToEndRehearsal")
        != ("pass" if exact_app_rehearsal_passed else "pending")
    ):
        raise VerificationError(
            "App release candidate verification state is unsafe"
        )

    rehearsal_reference = candidate.get("trustedSubmissionRehearsal")
    if not isinstance(rehearsal_reference, dict):
        raise VerificationError(
            "Power candidate has no trusted-main contributor rehearsal"
        )
    rehearsal_path = _verify_pinned_asset(
        rehearsal_reference,
        "trusted-main contributor rehearsal",
    )
    rehearsal = _load_json(rehearsal_path)
    triage_reference = rehearsal.get("trustedTriageReport")
    result_reference = rehearsal.get("physicalDeviceResult")
    pull_request = rehearsal.get("pullRequest")
    workflow_run = rehearsal.get("workflowRun")
    if not all(
        isinstance(value, dict)
        for value in (
            triage_reference,
            result_reference,
            pull_request,
            workflow_run,
        )
    ):
        raise VerificationError(
            "trusted-main contributor rehearsal is incomplete"
        )
    triage_path = _verify_pinned_asset(
        triage_reference,
        "trusted-main triage report",
    )
    rehearsed_result_path = _verify_pinned_asset(
        result_reference,
        "trusted-main physical-device result",
    )
    triage = _load_json(triage_path)
    trusted_base = rehearsal.get("trustedBaseCommit")
    pull_number = pull_request.get("number")
    if (
        rehearsal.get("schemaVersion")
        != "power-contributor-rehearsal-record-1.0.0-draft.1"
        or rehearsal.get("state") != "pass"
        or rehearsal.get("closedPublicIntake") is not True
        or rehearsal.get("classification") != "auto_accept"
        or triage.get("classification") != "auto_accept"
        or triage.get("errors") != []
        or triage.get("reasonCodes") != []
        or triage.get("packageCount") != 1
        or triage.get("expectedContributor")
        != rehearsal.get("expectedContributor")
        or result_reference.get("sha256")
        != triage.get("packages", [{}])[0].get("sourceResultSHA256")
        or not isinstance(trusted_base, str)
        or len(trusted_base) != 40
        or any(
            character not in "0123456789abcdef"
            for character in trusted_base
        )
        or not isinstance(pull_number, int)
        or pull_number < 1
        or pull_request.get("url")
        != (
            "https://github.com/YizeSun/iOS-LLM-Leaderboard/pull/"
            + str(pull_number)
        )
        or not isinstance(pull_request.get("headCommit"), str)
        or len(pull_request["headCommit"]) != 40
        or not isinstance(workflow_run.get("id"), int)
    ):
        raise VerificationError(
            "trusted-main contributor rehearsal is not audit-safe"
        )
    documents.extend(
        (
            (str(rehearsal_path.relative_to(ROOT)), rehearsal),
            (str(triage_path.relative_to(ROOT)), triage),
            (
                str(rehearsed_result_path.relative_to(ROOT)),
                _load_json(rehearsed_result_path),
            ),
        )
    )

    return runner_id, str(app_candidate.get("releaseID"))


def _verify_model_registry(
    registry: dict[str, Any],
    cohort: dict[str, Any],
    documents: list[tuple[str, dict[str, Any]]],
) -> int:
    entries = registry.get("entries")
    if not isinstance(entries, list) or not entries:
        raise VerificationError(
            "Power candidate must register at least one exact rerun artifact"
        )

    predicate = cohort.get("predicate")
    if not isinstance(predicate, dict):
        raise VerificationError("model cohort has no predicate")
    if predicate.get("field") != "parameterCount":
        raise VerificationError("candidate cohort must use parameterCount")
    if predicate.get("operator") != "less-than-or-equal":
        raise VerificationError("candidate cohort operator is unsupported")
    cohort_limit = predicate.get("value")
    if not isinstance(cohort_limit, int) or cohort_limit < 1:
        raise VerificationError("candidate cohort has no positive size limit")

    entry_ids: set[str] = set()
    referenced_paths: set[Path] = set()
    required_manifest_fields = {
        "publisher",
        "family",
        "artifactID",
        "artifactRevision",
        "parameterCount",
        "quantization",
        "format",
        "repositorySizeBytes",
        "tokenizer",
        "runtimeCompatibility",
        "licenseIdentifier",
        "licenseSourceURL",
        "sourceURL",
    }

    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise VerificationError(f"model registry entry {index} is invalid")
        entry_id = entry.get("registryEntryID")
        if not isinstance(entry_id, str) or not entry_id:
            raise VerificationError(f"model registry entry {index} has no ID")
        if entry_id in entry_ids:
            raise VerificationError(f"duplicate model registry ID: {entry_id}")
        entry_ids.add(entry_id)

        manifest_path = _verify_pinned_asset(
            entry, f"model registry entry {entry_id}"
        )
        referenced_paths.add(manifest_path)
        manifest = _load_json(manifest_path)
        documents.append((str(manifest_path.relative_to(ROOT)), manifest))

        if manifest.get("registryEntryID") != entry_id:
            raise VerificationError(
                f"model manifest ID mismatch for {entry_id}"
            )
        if manifest.get("status") != "rerun-candidate":
            raise VerificationError(
                f"model {entry_id} is not a rerun candidate"
            )
        missing_fields = sorted(required_manifest_fields - manifest.keys())
        if missing_fields:
            raise VerificationError(
                f"model {entry_id} is missing fields: {missing_fields}"
            )
        if manifest.get("oldRankingStatusImported") is not False:
            raise VerificationError(
                f"model {entry_id} imports retired ranking state"
            )
        if (
            manifest.get("performanceClaimsRequireNewAcceptedEvidence")
            is not True
        ):
            raise VerificationError(
                f"model {entry_id} does not require new evidence"
            )
        runtime_compatibility = manifest.get("runtimeCompatibility")
        if (
            not isinstance(runtime_compatibility, dict)
            or runtime_compatibility.get("runtime") != "MLX Swift LM"
            or not isinstance(
                runtime_compatibility.get(
                    "extraEndOfSequenceTokens"
                ),
                list,
            )
            or not all(
                isinstance(value, str) and value
                for value in runtime_compatibility.get(
                    "extraEndOfSequenceTokens", []
                )
            )
        ):
            raise VerificationError(
                f"model {entry_id} has invalid runtime compatibility"
            )

        artifact_revision = manifest.get("artifactRevision")
        source_url = manifest.get("sourceURL")
        if (
            not isinstance(artifact_revision, str)
            or len(artifact_revision) != 40
            or any(
                character not in "0123456789abcdef"
                for character in artifact_revision
            )
        ):
            raise VerificationError(
                f"model {entry_id} has an invalid artifact revision"
            )
        if (
            not isinstance(source_url, str)
            or artifact_revision not in source_url
        ):
            raise VerificationError(
                f"model {entry_id} source URL is not revision-pinned"
            )

        parameter_count = manifest.get("parameterCount")
        if not isinstance(parameter_count, int) or parameter_count < 1:
            raise VerificationError(
                f"model {entry_id} has no exact parameter count"
            )
        if parameter_count > cohort_limit:
            raise VerificationError(
                f"model {entry_id} is outside the selected cohort"
            )
        base_model = manifest.get("baseModel")
        if (
            not isinstance(base_model, dict)
            or base_model.get("parameterCount") != parameter_count
        ):
            raise VerificationError(
                f"model {entry_id} base parameter identity does not match"
            )

        weights = manifest.get("weights")
        if not isinstance(weights, list) or not weights:
            raise VerificationError(f"model {entry_id} has no pinned weights")
        for weight in weights:
            if (
                not isinstance(weight, dict)
                or not isinstance(weight.get("byteCount"), int)
                or not isinstance(weight.get("sha256"), str)
                or len(weight["sha256"]) != 64
            ):
                raise VerificationError(
                    f"model {entry_id} has an invalid weight record"
                )

        tokenizer = manifest.get("tokenizer")
        if (
            not isinstance(tokenizer, dict)
            or not isinstance(tokenizer.get("sha256"), str)
            or len(tokenizer["sha256"]) != 64
            or not isinstance(tokenizer.get("files"), list)
            or not tokenizer["files"]
        ):
            raise VerificationError(
                f"model {entry_id} has no pinned tokenizer identity"
            )

    actual_paths = {
        path.resolve()
        for path in (ROOT / "models" / "artifacts").rglob("manifest.json")
    }
    if referenced_paths != actual_paths:
        unregistered = sorted(
            str(path.relative_to(ROOT))
            for path in actual_paths - referenced_paths
        )
        missing = sorted(
            str(path.relative_to(ROOT))
            for path in referenced_paths - actual_paths
        )
        raise VerificationError(
            "model registry does not exactly cover artifact manifests; "
            f"unregistered={unregistered}, missing={missing}"
        )

    return len(entries)


def _verify_active_power_state(
    registry: dict[str, Any],
    candidate: dict[str, Any],
    *,
    program_reference: dict[str, Any],
    target_reference: dict[str, Any],
    documents: list[tuple[str, dict[str, Any]]],
) -> str:
    """Verify the one immutable active pointer and its retained release."""

    if (
        registry.get("schemaVersion") != "power-product-registry-1.0.0"
        or registry.get("status") != "active"
        or registry.get("publicIntakeOpen") is not True
        or registry.get("currentStack") != POWER_CURRENT_PATH
    ):
        raise VerificationError("Power registry is not a valid active registry")

    current_path = _repo_path(POWER_CURRENT_PATH)
    current = _load_json(current_path)
    documents.append((POWER_CURRENT_PATH, current))
    if (
        current.get("schemaVersion") != "power-stack-pointer-1.0.0"
        or current.get("productID") != "power"
        or current.get("status") != "active"
        or current.get("publicIntakeOpen") is not True
    ):
        raise VerificationError("Power current pointer is not active")

    current_stack_path = _verify_pinned_asset(
        current.get("measurementStack", {}),
        "active measurement stack",
    )
    current_stack = _load_json(current_stack_path)
    current_runner_path = _verify_pinned_asset(
        current.get("runnerComponents", {}),
        "active Runner components",
    )
    current_runner = _load_json(current_runner_path)
    runner_certificate_path = _verify_pinned_asset(
        current.get("runnerCertificate", {}),
        "active Runner certificate",
    )
    runner_certificate = _load_json(runner_certificate_path)
    documents.extend(
        (
            (
                str(current_stack_path.relative_to(ROOT)),
                current_stack,
            ),
            (
                str(current_runner_path.relative_to(ROOT)),
                current_runner,
            ),
            (
                str(runner_certificate_path.relative_to(ROOT)),
                runner_certificate,
            ),
        )
    )
    certificate_id = runner_certificate.get("certificateID")
    if (
        current_stack.get("stackID") != current.get("stackID")
        or current_stack.get("status") != "release-candidate"
        or current_stack.get("program") != program_reference
        or current_stack.get("target") != target_reference
        or current_stack.get("runnerCertificate")
        != current.get("runnerCertificate")
        or current_runner.get("schemaVersion")
        not in {
            "power-runner-component-manifest-1.0.0-draft.1",
            "power-runner-component-manifest-1.0.0",
        }
        or runner_certificate.get("state") != "active"
        or runner_certificate.get("runnerComponents")
        != current.get("runnerComponents")
        or not isinstance(certificate_id, str)
    ):
        raise VerificationError(
            "active stack, Runner components, and certificate disagree"
        )

    app_reference = current.get("appRelease")
    if not isinstance(app_reference, dict):
        raise VerificationError("Power current pointer has no App release")
    app_release_path = _verify_pinned_asset(
        app_reference, "active App release"
    )
    app_release = _load_json(app_release_path)
    documents.append(
        (str(app_release_path.relative_to(ROOT)), app_release)
    )

    if (
        app_release.get("schemaVersion") != "power-app-release-1.0.0"
        or app_release.get("productID") != "power"
        or app_release.get("state") != "supported"
        or app_release.get("buildConfiguration") != "Official"
        or app_release.get("embeddedMeasurementStack")
        != current.get("measurementStack")
        or app_release.get("supportedRunnerCertificateIDs")
        != [certificate_id]
        or app_release.get("verification")
        != {
            "sourceAndDependencyIntegrity": "pass",
            "genericIOSReleaseBuild": "pass",
            "physicalDeviceEndToEndRehearsal": "pass",
            "rawResultReview": "pass",
        }
    ):
        raise VerificationError("active App release identity is inconsistent")

    app_components = app_release.get("appComponents")
    if (
        not isinstance(app_components, dict)
        or app_components.get("sha256")
        != app_release.get("sourceRevision")
    ):
        raise VerificationError(
            "active App release component identity is inconsistent"
        )
    component_path = _verify_pinned_asset(
        app_components, "active App component manifest"
    )
    documents.append(
        (str(component_path.relative_to(ROOT)), _load_json(component_path))
    )

    release_evidence = app_release.get("releaseEvidence")
    if (
        not isinstance(release_evidence, dict)
        or current.get("activationEvidence") != release_evidence
    ):
        raise VerificationError(
            "Power activation evidence does not match the App release"
        )
    result_path = _verify_pinned_asset(
        release_evidence.get("result", {}), "App release result"
    )
    review_path = _verify_pinned_asset(
        release_evidence.get("review", {}), "App release review"
    )
    result = _load_json(result_path)
    review = _load_json(review_path)
    documents.extend(
        (
            (str(result_path.relative_to(ROOT)), result),
            (str(review_path.relative_to(ROOT)), review),
        )
    )
    expected_app_identity = {
        "version": app_release.get("version"),
        "build": app_release.get("build"),
        "sourceRevision": app_release.get("sourceRevision"),
        "embeddedMeasurementStackSHA256":
            current.get("measurementStack", {}).get("sha256"),
    }
    if (
        result.get("appRelease") != expected_app_identity
        or result.get("runnerCertificateID") != certificate_id
        or review.get("status") != "pass"
        or review.get("physicalDeviceEndToEndRehearsal") != "pass"
        or review.get("classification") != "auto-accept"
        or review.get("publishable") is not False
        or review.get("rankingEligible") is not False
        or review.get("sourceResultSHA256")
        != release_evidence["result"].get("sha256")
    ):
        raise VerificationError("active App release evidence is inconsistent")

    programs = registry.get("programs")
    targets = registry.get("targets")
    if (
        not isinstance(programs, list)
        or programs
        != [
            {
                "id": program_reference.get("id"),
                "manifest": program_reference.get("path"),
                "status": "active",
                "currentVersion": program_reference.get("version"),
            }
        ]
        or not isinstance(targets, list)
        or targets
        != [
            {
                "id": target_reference.get("id"),
                "manifest": target_reference.get("path"),
                "status": "active",
                "currentVersion": target_reference.get("version"),
            }
        ]
    ):
        raise VerificationError("active Power registry versions are inconsistent")

    return str(app_release.get("releaseID"))


def verify_power_candidate() -> dict[str, Any]:
    """Verify active Power state and the fail-closed next release plan.

    The initial activation record is retained for audit, but released source
    manifests are verified as immutable snapshots rather than re-bound to the
    mutable working-tree source paths they originally listed. New source is
    checked independently through ``products/power/next.json``.
    """

    registry_path = _repo_path(POWER_REGISTRY_PATH)
    registry = _load_json(registry_path)
    active = _repo_path(POWER_CURRENT_PATH).exists()
    if not active:
        if registry.get("status") != "migration-draft":
            raise VerificationError("Power registry is not a migration draft")
        if registry.get("publicIntakeOpen") is not False:
            raise VerificationError("Power public intake must remain closed")
        if registry.get("currentStack") is not None:
            raise VerificationError(
                "Power currentStack must remain null before cutover"
            )

    candidate_path_value = registry.get("candidateStack")
    if not isinstance(candidate_path_value, str):
        raise VerificationError("Power registry has no candidate stack")
    candidate_path = _repo_path(candidate_path_value)
    candidate = _load_json(candidate_path)
    if candidate.get("status") != "migration-draft":
        raise VerificationError("Power candidate is not a migration draft")
    if candidate.get("publicIntakeOpen") is not False:
        raise VerificationError("Power candidate unexpectedly opens intake")
    if candidate.get("appRelease") is not None:
        raise VerificationError("unreleased App must not be activated")

    documents: list[tuple[str, dict[str, Any]]] = [
        (POWER_REGISTRY_PATH, registry),
        (candidate_path_value, candidate),
    ]

    runner_candidate_reference = candidate.get("runnerCandidate")
    if not isinstance(runner_candidate_reference, dict):
        raise VerificationError("Power candidate has no runner candidate")
    app_candidate_reference = candidate.get("appCandidate")
    if not isinstance(app_candidate_reference, dict):
        raise VerificationError("Power candidate has no App candidate")
    if active:
        runner_manifest_path = _verify_pinned_asset(
            runner_candidate_reference,
            "released Runner component manifest",
        )
        runner_manifest = _load_json(runner_manifest_path)
        runner_components = runner_manifest.get("components")
        if not isinstance(runner_components, dict):
            raise VerificationError(
                "released Runner manifest has no components"
            )
        runner_component_count = len(runner_components)
        runtime_adapter_implemented = isinstance(
            runner_components.get("runtimeAdapter"),
            dict,
        )
        current = _load_json(_repo_path(POWER_CURRENT_PATH))
        app_release_path = _verify_pinned_asset(
            current.get("appRelease", {}),
            "active App release",
        )
        app_release = _load_json(app_release_path)
        app_manifest_path = _verify_pinned_asset(
            app_release.get("appComponents", {}),
            "released App component manifest",
        )
        app_manifest = _load_json(app_manifest_path)
        app_components = app_manifest.get("components")
        if not isinstance(app_components, dict):
            raise VerificationError(
                "released App manifest has no components"
            )
        app_component_count = len(app_components)
    else:
        runner_component_count, runtime_adapter_implemented = (
            _verify_runner_candidate(runner_candidate_reference, documents)
        )
        app_component_count = _verify_app_candidate(
            app_candidate_reference,
            documents,
        )

    measurement_stack_reference = candidate.get("measurementStack")
    if not isinstance(measurement_stack_reference, dict):
        raise VerificationError("candidate has no measurement stack")
    measurement_stack_path = _verify_pinned_asset(
        measurement_stack_reference, "candidate measurement stack"
    )
    measurement_stack = _load_json(measurement_stack_path)
    documents.append(
        (str(measurement_stack_path.relative_to(ROOT)), measurement_stack)
    )
    if measurement_stack.get("status") != "release-candidate":
        raise VerificationError(
            "measurement stack is not a closed release candidate"
        )
    if measurement_stack.get("stackID") != candidate.get("stackID"):
        raise VerificationError("candidate and measurement stack IDs differ")
    runner_certificate_reference = candidate.get("runnerCertificate")
    if not isinstance(runner_certificate_reference, dict):
        raise VerificationError(
            "candidate has no active Runner certificate"
        )
    if (
        measurement_stack.get("runnerCertificate")
        != runner_certificate_reference
    ):
        raise VerificationError(
            "measurement stack Runner certificate mismatch"
        )

    program_reference = measurement_stack.get("program")
    target_reference = measurement_stack.get("target")
    policies = measurement_stack.get("policies")
    models = measurement_stack.get("models")
    if not isinstance(program_reference, dict):
        raise VerificationError("candidate has no program reference")
    if not isinstance(target_reference, dict):
        raise VerificationError("candidate has no target reference")
    if not isinstance(policies, dict):
        raise VerificationError("candidate has no policy references")
    if not isinstance(models, dict):
        raise VerificationError("candidate has no model references")

    program_manifest_path = _verify_pinned_asset(
        program_reference, "candidate program"
    )
    program_manifest = _load_json(program_manifest_path)
    program_documents, pinned_asset_count = _verify_program_manifest(
        program_manifest_path, program_manifest
    )
    documents.extend(program_documents)

    if program_manifest.get("programID") != program_reference.get("id"):
        raise VerificationError("candidate program ID does not match manifest")
    if program_manifest.get("programVersion") != program_reference.get("version"):
        raise VerificationError(
            "candidate program version does not match manifest"
        )

    target_path = _verify_pinned_asset(target_reference, "candidate target")
    target = _load_json(target_path)
    documents.append((str(target_path.relative_to(ROOT)), target))
    if target.get("targetID") != target_reference.get("id"):
        raise VerificationError("candidate target ID does not match manifest")
    if target.get("targetVersion") != target_reference.get("version"):
        raise VerificationError("candidate target version does not match manifest")
    if target.get("physicalDeviceRequired") is not True:
        raise VerificationError("Power iPhone target must require physical hardware")
    if target.get("simulatorAllowed") is not False:
        raise VerificationError("Power iPhone target must reject simulator evidence")

    for policy_name in ("runner", "intake", "ranking"):
        reference = policies.get(policy_name)
        if not isinstance(reference, dict):
            raise VerificationError(f"candidate has no {policy_name} policy")
        policy_path = _verify_pinned_asset(
            reference, f"candidate {policy_name} policy"
        )
        policy = _load_json(policy_path)
        documents.append((str(policy_path.relative_to(ROOT)), policy))
        if policy.get("policyVersion") != reference.get("version"):
            raise VerificationError(
                f"candidate {policy_name} policy version mismatch"
            )

    if active:
        runner_candidate_path = _verify_pinned_asset(
            candidate.get("runnerCertificationCandidate", {}),
            "retained Runner certificate candidate",
        )
        runner_certification_candidate_id = _load_json(
            runner_candidate_path
        ).get("certificateID")
        app_candidate_path = _verify_pinned_asset(
            candidate.get("appReleaseCandidate", {}),
            "retained App release candidate",
        )
        app_release_candidate_id = _load_json(
            app_candidate_path
        ).get("releaseID")
    else:
        runner_certification_candidate_id, app_release_candidate_id = (
            _verify_release_candidates(
                candidate,
                measurement_stack_reference=measurement_stack_reference,
                runner_reference=runner_candidate_reference,
                runner_certificate_reference=runner_certificate_reference,
                app_reference=app_candidate_reference,
                program_reference=program_reference,
                target_reference=target_reference,
                runner_policy_reference=policies["runner"],
                documents=documents,
            )
        )

    registry_reference = models.get("registry")
    cohort_reference = models.get("cohort")
    if not isinstance(registry_reference, dict):
        raise VerificationError("candidate has no model registry")
    if not isinstance(cohort_reference, dict):
        raise VerificationError("candidate has no model cohort")

    model_registry_path = _verify_pinned_asset(
        registry_reference, "candidate model registry"
    )
    model_registry = _load_json(model_registry_path)
    documents.append(
        (str(model_registry_path.relative_to(ROOT)), model_registry)
    )
    if model_registry.get("oldRankingStatusImported") is not False:
        raise VerificationError("candidate imports retired ranking status")
    cohort_path = _verify_pinned_asset(cohort_reference, "candidate model cohort")
    cohort = _load_json(cohort_path)
    documents.append((str(cohort_path.relative_to(ROOT)), cohort))
    if cohort.get("cohortID") != cohort_reference.get("id"):
        raise VerificationError("candidate cohort ID mismatch")
    if cohort.get("cohortVersion") != cohort_reference.get("version"):
        raise VerificationError("candidate cohort version mismatch")
    if cohort.get("rankingStatusImportedFromOlderMajor") is not False:
        raise VerificationError("candidate cohort imports retired ranking status")

    registered_model_count = _verify_model_registry(
        model_registry, cohort, documents
    )

    documents_by_path = dict(documents)
    contract_path = next(
        (
            reference["path"]
            for reference in program_manifest["assets"]
            if reference.get("role") == "program-contract"
        ),
        None,
    )
    if not isinstance(contract_path, str) or contract_path not in documents_by_path:
        raise VerificationError("program manifest has no readable contract")
    contract = documents_by_path[contract_path]
    if contract.get("programID") != program_reference.get("id"):
        raise VerificationError("program contract ID mismatch")
    if contract.get("programVersion") != program_reference.get("version"):
        raise VerificationError("program contract version mismatch")

    _verify_workload_fixtures(contract, documents_by_path)
    schema_count = _verify_schema_set(documents_by_path)
    _verify_workload_measurement_modes(contract, documents_by_path)
    _verify_workload_response_contracts(contract, documents_by_path)

    next_state: str | None = None
    next_runner_certificate_id: str | None = None
    next_app_release_candidate_id: str | None = None
    if active:
        next_path_value = registry.get("nextRelease")
        if next_path_value != "products/power/next.json":
            raise VerificationError(
                "active Power registry has no canonical next-release plan"
            )
        next_path = _repo_path(next_path_value)
        next_release = _load_json(next_path)
        next_state_value = next_release.get("state")
        reported_next_state = next_state_value
        if (
            next_release.get("schemaVersion")
            != "power-release-plan-1.0.0"
            or next_release.get("productID") != "power"
            or next_state_value not in {
                "runner-certification-required",
                "app-release-rehearsal-required",
                "activated",
            }
            or next_release.get("publicIntakeOpen") is not False
            or (
                next_state_value != "activated"
                and next_release.get("appRelease") is not None
            )
        ):
            raise VerificationError(
                "next Power release plan is not fail-closed"
            )
        documents.append((next_path_value, next_release))
        current = _load_json(_repo_path(POWER_CURRENT_PATH))
        if next_state_value == "activated":
            completed_base_path = _verify_pinned_asset(
                next_release.get("baseRelease", {}),
                "completed release base snapshot",
            )
            completed_app_release = _verify_pinned_asset(
                next_release.get("appRelease", {}),
                "completed App release",
            )
            completed_activation = next_release.get(
                "activationEvidence"
            )
            if not isinstance(completed_activation, dict):
                raise VerificationError(
                    "completed release has no activation evidence"
                )
            for key in ("result", "review"):
                _verify_pinned_asset(
                    completed_activation.get(key, {}),
                    f"completed release activation {key}",
                )
            if (
                completed_base_path == _repo_path(POWER_CURRENT_PATH)
                or completed_app_release
                != _verify_pinned_asset(
                    current.get("appRelease", {}),
                    "active completed App release",
                )
                or next_release.get("activatedAt")
                != current.get("activatedAt")
                or next_release.get("stackID") != current.get("stackID")
                or next_release.get("measurementStack")
                != current.get("measurementStack")
                or next_release.get("runnerComponents")
                != current.get("runnerComponents")
                or next_release.get("runnerCertificate")
                != current.get("runnerCertificate")
                or next_release.get("appRelease")
                != current.get("appRelease")
                or completed_activation
                != current.get("activationEvidence")
            ):
                raise VerificationError(
                    "completed next release does not match active Power"
                )
            next_release = {
                **next_release,
                "state": "app-release-rehearsal-required",
                "baseRelease": {
                    "path": POWER_CURRENT_PATH,
                    "sha256": _sha256(
                        _repo_path(POWER_CURRENT_PATH)
                    ),
                },
                "appRelease": None,
            }
            next_state_value = "app-release-rehearsal-required"
        base_path = _verify_pinned_asset(
            next_release.get("baseRelease", {}),
            "next release base pointer",
        )
        if base_path != _repo_path(POWER_CURRENT_PATH):
            raise VerificationError(
                "next release is not based on current Power"
            )
        next_runner = next_release.get("runnerComponents")
        if not isinstance(next_runner, dict):
            raise VerificationError(
                "next release has no Runner component candidate"
            )
        _verify_runner_candidate(next_runner, documents)
        expected_candidate_id = (
            "power2-certification-candidate-"
            + str(next_runner.get("sha256", ""))[:12]
        )
        if (
            next_release.get("runnerCertificationCandidateID")
            != expected_candidate_id
        ):
            raise VerificationError(
                "next Runner candidate ID is not source-derived"
            )
        if next_state_value == "runner-certification-required":
            if (
                next_release.get("measurementStack")
                != current.get("measurementStack")
                or next_release.get("runnerCertificate") is not None
                or next_release.get("appReleaseCandidate") is not None
            ):
                raise VerificationError(
                    "initial next release must remain at the closed "
                    "Runner certification gate"
                )
        else:
            next_stack_path = _verify_pinned_asset(
                next_release.get("measurementStack", {}),
                "next release measurement stack",
            )
            next_stack = _load_json(next_stack_path)
            documents.append(
                (
                    str(next_stack_path.relative_to(ROOT)),
                    next_stack,
                )
            )
            next_certificate_reference = next_release.get(
                "runnerCertificate"
            )
            if not isinstance(next_certificate_reference, dict):
                raise VerificationError(
                    "App rehearsal has no issued Runner certificate"
                )
            next_certificate_path = _verify_pinned_asset(
                next_certificate_reference,
                "next release Runner certificate",
            )
            next_certificate = _load_json(next_certificate_path)
            documents.append(
                (
                    str(next_certificate_path.relative_to(ROOT)),
                    next_certificate,
                )
            )
            next_certificate_id = next_certificate.get("certificateID")
            expected_certificate_id = (
                "power2-runner-"
                + str(next_runner.get("sha256", ""))[:12]
            )
            if (
                next_stack.get("stackID")
                != next_release.get("stackID")
                or next_stack.get("status") != "release-candidate"
                or next_stack.get("runnerCertificate")
                != next_certificate_reference
                or next_certificate.get("state") != "active"
                or next_certificate.get("runnerComponents")
                != next_runner
                or next_certificate_id != expected_certificate_id
            ):
                raise VerificationError(
                    "next App rehearsal stack and Runner certificate "
                    "are inconsistent"
                )

            next_evidence = next_release.get(
                "runnerCertificationEvidence"
            )
            certificate_evidence = next_certificate.get(
                "certificationEvidence"
            )
            if (
                not isinstance(next_evidence, dict)
                or not isinstance(certificate_evidence, dict)
            ):
                raise VerificationError(
                    "next Runner certificate has no retained evidence"
                )
            evidence_keys = {
                "result": "result",
                "review": "review",
                "runnerComponentsSnapshot": "runnerComponentsSnapshot",
                "certificationAppComponents":
                    "certificationAppComponents",
            }
            for next_key, certificate_key in evidence_keys.items():
                reference = next_evidence.get(next_key)
                if reference != certificate_evidence.get(certificate_key):
                    raise VerificationError(
                        "next Runner certification evidence mismatch: "
                        f"{next_key}"
                    )
                evidence_path = _verify_pinned_asset(
                    reference,
                    f"next Runner certification evidence {next_key}",
                )
                documents.append(
                    (
                        str(evidence_path.relative_to(ROOT)),
                        _load_json(evidence_path),
                    )
                )
            runtime_snapshot = next_evidence.get(
                "runtimeIdentitySnapshot"
            )
            if runtime_snapshot != next_certificate.get(
                "runtimeIdentity"
            ):
                raise VerificationError(
                    "next Runner runtime snapshot mismatch"
                )
            runtime_snapshot_path = _verify_pinned_asset(
                runtime_snapshot,
                "next Runner runtime snapshot",
            )
            documents.append(
                (
                    str(runtime_snapshot_path.relative_to(ROOT)),
                    _load_json(runtime_snapshot_path),
                )
            )
            certification_result = _load_json(
                _verify_pinned_asset(
                    next_evidence["result"],
                    "next Runner certification result",
                )
            )
            certification_review = _load_json(
                _verify_pinned_asset(
                    next_evidence["review"],
                    "next Runner certification review",
                )
            )
            if (
                certification_result.get("runnerCertificateID")
                != next_release.get("runnerCertificationCandidateID")
                or certification_review.get("runnerCertificateID")
                != next_release.get("runnerCertificationCandidateID")
                or certification_review.get("status") != "pass"
                or certification_review.get("physicalDeviceSmokeRun")
                != "pass"
                or certification_review.get("rawResultReview") != "pass"
                or certification_review.get("publishable") is not False
                or certification_review.get("rankingEligible") is not False
                or certification_review.get("sourceResultSHA256")
                != next_evidence["result"].get("sha256")
            ):
                raise VerificationError(
                    "next Runner certification evidence is not "
                    "issuance-safe"
                )

            next_app_candidate_reference = next_release.get(
                "appReleaseCandidate"
            )
            if not isinstance(next_app_candidate_reference, dict):
                raise VerificationError(
                    "App rehearsal has no frozen App release candidate"
                )
            next_app_candidate_path = _verify_pinned_asset(
                next_app_candidate_reference,
                "next App release candidate",
            )
            next_app_candidate = _load_json(next_app_candidate_path)
            documents.append(
                (
                    str(next_app_candidate_path.relative_to(ROOT)),
                    next_app_candidate,
                )
            )
            next_app_reference = next_app_candidate.get("appComponents")
            if not isinstance(next_app_reference, dict):
                raise VerificationError(
                    "next App release candidate has no component manifest"
                )
            _verify_app_candidate(next_app_reference, documents)
            next_app_manifest = _load_json(
                _verify_pinned_asset(
                    next_app_reference,
                    "next App component manifest",
                )
            )
            next_app_identity = _load_json(
                _verify_pinned_asset(
                    next_app_manifest.get("releaseIdentity", {}),
                    "next App release identity",
                )
            )
            next_official_identity = next_app_identity.get(
                "buildKinds", {}
            ).get("official", {})
            next_app_digest = next_app_reference.get("sha256")
            if (
                next_app_candidate.get("schemaVersion")
                != "power-app-release-candidate-1.0.0-draft.1"
                or next_app_candidate.get("productID") != "power"
                or next_app_candidate.get("state") != "candidate"
                or next_app_candidate.get("releaseID")
                != (
                    f"power-app-{next_app_identity.get('version')}"
                    f"-candidate-{str(next_app_digest)[:12]}"
                )
                or next_app_candidate.get("sourceRevision")
                != next_app_digest
                or next_app_candidate.get("version")
                != next_app_identity.get("version")
                or next_app_candidate.get("build")
                != next_app_identity.get("build")
                or next_app_candidate.get("bundleIdentifier")
                != next_official_identity.get("bundleIdentifier")
                or next_app_candidate.get("buildConfiguration")
                != "Official"
                or next_app_candidate.get("embeddedMeasurementStack")
                != next_release.get("measurementStack")
                or next_app_candidate.get(
                    "supportedRunnerCertificateIDs"
                )
                != [next_certificate_id]
                or next_app_candidate.get("verification")
                != {
                    "sourceAndDependencyIntegrity": "pass",
                    "genericIOSReleaseBuild": "pass",
                    "physicalDeviceEndToEndRehearsal": "pending",
                }
                or next_release.get("app")
                != {
                    "version": next_app_identity.get("version"),
                    "build": next_app_identity.get("build"),
                }
            ):
                raise VerificationError(
                    "next App release candidate is not source-bound"
                )
            next_runner_certificate_id = str(next_certificate_id)
            next_app_release_candidate_id = str(
                next_app_candidate.get("releaseID")
            )
        next_state = str(reported_next_state)

    active_release_id: str | None = None
    if active:
        active_release_id = _verify_active_power_state(
            registry,
            candidate,
            program_reference=program_reference,
            target_reference=target_reference,
            documents=documents,
        )
    _reject_legacy_references(documents)

    summary_stack_id = candidate.get("stackID")
    if active:
        summary_stack_id = _load_json(
            _repo_path(POWER_CURRENT_PATH)
        ).get("stackID")

    return {
        "status": "valid-active" if active else "valid-migration-draft",
        "stackID": summary_stack_id,
        "publicIntakeOpen": active,
        "program": (
            f"{program_reference.get('id')}@"
            f"{program_reference.get('version')}"
        ),
        "target": (
            f"{target_reference.get('id')}@"
            f"{target_reference.get('version')}"
        ),
        "pinnedProgramAssets": pinned_asset_count,
        "schemas": schema_count,
        "registeredModels": registered_model_count,
        "runnerComponents": runner_component_count,
        "runtimeAdapterImplemented": runtime_adapter_implemented,
        "appComponents": app_component_count,
        "appShellImplemented": True,
        "runnerCertificationCandidate":
            runner_certification_candidate_id,
        "appReleaseCandidate": app_release_candidate_id,
        "runnerCertified": True,
        "appReleased": active,
        "appRelease": active_release_id,
        "nextReleaseState": next_state,
        "nextRunnerCertificate": next_runner_certificate_id,
        "nextAppReleaseCandidate": next_app_release_candidate_id,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify and manage versioned benchmark product state."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "verify-power-candidate",
        help="verify the clean-break Power candidate and active state",
    )
    validate_parser = subparsers.add_parser(
        "validate-power-package",
        help="validate a Power 2.0 two-file package against trusted candidate state",
    )
    validate_parser.add_argument("path", type=Path)
    validate_parser.add_argument("--pr-author", required=True)
    validate_parser.add_argument("--evaluated-at", required=True)
    validate_parser.add_argument(
        "--validator-source-revision",
        required=True,
        help="trusted base Git revision (40- or 64-character hex)",
    )
    validate_parser.add_argument(
        "--accepted-result-digest",
        action="append",
        default=[],
        help="previously accepted result SHA-256; may be repeated",
    )
    create_parser = subparsers.add_parser(
        "create-power-package",
        help="create a Power 2.0 two-file package without rewriting evidence",
    )
    create_parser.add_argument("result", type=Path)
    create_parser.add_argument("--output-root", type=Path)
    create_parser.add_argument("--github-login", required=True)
    create_parser.add_argument(
        "--conflict-of-interest",
        choices=("none", "disclosed"),
        default="none",
    )
    create_parser.add_argument("--disclosure")
    create_parser.add_argument("--environment-notes")
    create_parser.add_argument(
        "--accept-declarations",
        action="store_true",
    )
    create_parser.add_argument("--submission-id")
    create_parser.add_argument("--created-at")
    ranking_parser = subparsers.add_parser(
        "generate-power-ranking",
        help="derive Power 2.0 ranking views from trusted packages",
    )
    ranking_parser.add_argument("submissions_root", type=Path)
    ranking_parser.add_argument("output", type=Path)
    ranking_parser.add_argument("--generated-at", required=True)
    ranking_parser.add_argument(
        "--validator-source-revision",
        required=True,
    )
    activation_parser = subparsers.add_parser(
        "activate-power",
        help=(
            "review one Official result and stage the App release, active "
            "pointer, and registry together"
        ),
    )
    activation_parser.add_argument("result", type=Path)
    activation_parser.add_argument("--reviewed-at", required=True)
    activation_parser.add_argument("--activated-at", required=True)
    activation_parser.add_argument(
        "--validator-source-revision",
        required=True,
    )
    activation_parser.add_argument(
        "--write",
        action="store_true",
        help="write the verified activation set; omit for a dry run",
    )
    next_activation_parser = subparsers.add_parser(
        "activate-power-next",
        help=(
            "review one staged Official result and atomically advance the "
            "existing Power release"
        ),
    )
    next_activation_parser.add_argument("result", type=Path)
    next_activation_parser.add_argument("--reviewed-at", required=True)
    next_activation_parser.add_argument("--activated-at", required=True)
    next_activation_parser.add_argument(
        "--validator-source-revision",
        required=True,
    )
    next_activation_parser.add_argument(
        "--write",
        action="store_true",
        help="write the verified upgrade set; omit for a dry run",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    exit_code = 0
    try:
        if args.command == "verify-power-candidate":
            summary = verify_power_candidate()
        elif args.command == "validate-power-package":
            try:
                from scripts.lib.power2.engine import validate_package
            except ModuleNotFoundError:
                from lib.power2.engine import validate_package

            summary = validate_package(
                args.path,
                evaluated_at=args.evaluated_at,
                validator_source_revision=args.validator_source_revision,
                pr_author=args.pr_author,
                accepted_result_digests=set(args.accepted_result_digest),
            )
            if summary["classification"] == "reject":
                exit_code = 1
        elif args.command == "create-power-package":
            try:
                from scripts.lib.power2.package import (
                    DEFAULT_SUBMISSION_ROOT,
                    create_package,
                )
            except ModuleNotFoundError:
                from lib.power2.package import (
                    DEFAULT_SUBMISSION_ROOT,
                    create_package,
                )

            package = create_package(
                args.result,
                args.output_root or DEFAULT_SUBMISSION_ROOT,
                github_login=args.github_login,
                conflict_of_interest=args.conflict_of_interest,
                disclosure=args.disclosure,
                environment_notes=args.environment_notes,
                declarations_accepted=args.accept_declarations,
                submission_id=args.submission_id,
                created_at=args.created_at,
            )
            summary = {
                "status": "created",
                "package": str(package),
                "resultBytesPreserved": True,
            }
        elif args.command == "generate-power-ranking":
            try:
                from scripts.lib.power2.ranking import write_dataset
            except ModuleNotFoundError:
                from lib.power2.ranking import write_dataset

            summary = write_dataset(
                args.submissions_root,
                args.output,
                generated_at=args.generated_at,
                validator_source_revision=(
                    args.validator_source_revision
                ),
            )
        elif args.command == "activate-power":
            try:
                from scripts.lib.power2.activation import (
                    render_activation,
                    write_activation,
                )
            except ModuleNotFoundError:
                from lib.power2.activation import (
                    render_activation,
                    write_activation,
                )

            rendered = render_activation(
                args.result,
                reviewed_at=args.reviewed_at,
                validator_source_revision=(
                    args.validator_source_revision
                ),
                activated_at=args.activated_at,
            )
            if args.write:
                write_activation(rendered)
            summary = {
                **rendered.summary,
                "writeRequested": args.write,
                "written": args.write,
            }
        elif args.command == "activate-power-next":
            try:
                from scripts.lib.power2.next_activation import (
                    render_next_activation,
                    write_next_activation,
                )
            except ModuleNotFoundError:
                from lib.power2.next_activation import (
                    render_next_activation,
                    write_next_activation,
                )

            rendered = render_next_activation(
                args.result,
                reviewed_at=args.reviewed_at,
                validator_source_revision=(
                    args.validator_source_revision
                ),
                activated_at=args.activated_at,
            )
            if args.write:
                write_next_activation(rendered)
            summary = {
                **rendered.summary,
                "writeRequested": args.write,
                "written": args.write,
            }
        else:  # pragma: no cover - argparse prevents this branch.
            raise VerificationError(f"unsupported command: {args.command}")
    except (VerificationError, ValueError) as error:
        print(json.dumps({"status": "invalid", "error": str(error)}, indent=2))
        return 1

    print(json.dumps(summary, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
