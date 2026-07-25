"""Trusted-base validation engine for clean-break Power 2.0 packages."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
import uuid
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath
from typing import Any

from . import json_schema


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CANDIDATE_PATH = ROOT / "products" / "power" / "candidate.json"
DEFAULT_CURRENT_PATH = ROOT / "products" / "power" / "current.json"
DEFAULT_NEXT_PATH = ROOT / "products" / "power" / "next.json"
APP_COMPONENT_PATH = ROOT / "apps" / "ios" / "component-manifest.json"
ALLOWED_PACKAGE_FILES = {"submission.json", "result.json"}
VALIDATOR_NAME = "power-intake-engine"
VALIDATOR_VERSION = "2.0.0-draft.2"


def _canonical_uuid_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        canonical = str(uuid.UUID(value))
    except ValueError:
        return None
    return canonical if value.casefold() == canonical else None


class Power2ValidationError(ValueError):
    """Raised when trusted repository configuration is inconsistent."""


@dataclass
class ValidationContext:
    public_intake_open: bool
    measurement_stack_sha256: str
    program_reference: dict[str, Any]
    target_reference: dict[str, Any]
    policy_references: dict[str, dict[str, Any]]
    policy_documents: dict[str, dict[str, Any]]
    program_manifest: dict[str, Any]
    program_contract: dict[str, Any]
    target_manifest: dict[str, Any]
    workloads: dict[str, tuple[dict[str, Any], str]]
    model_entries: dict[str, tuple[dict[str, Any], str]]
    runner_certificate: dict[str, Any] | None
    app_release: dict[str, Any] | None
    schema_paths: dict[str, Path]


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Power2ValidationError(f"cannot load trusted JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise Power2ValidationError(f"trusted JSON is not an object: {path}")
    return value


def _repo_path(relative_path: str) -> Path:
    pure_path = PurePosixPath(relative_path)
    if pure_path.is_absolute() or ".." in pure_path.parts:
        raise Power2ValidationError(f"unsafe trusted path: {relative_path}")
    path = (ROOT / pure_path).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as error:
        raise Power2ValidationError(
            f"trusted path escapes repository: {relative_path}"
        ) from error
    return path


def _verify_reference_file(
    reference: dict[str, Any],
    label: str,
) -> Path:
    relative_path = reference.get("path")
    expected_digest = reference.get("sha256")
    if not isinstance(relative_path, str) or not isinstance(expected_digest, str):
        raise Power2ValidationError(f"{label} is not a pinned reference")
    path = _repo_path(relative_path)
    actual_digest = _sha256_file(path)
    if actual_digest != expected_digest:
        raise Power2ValidationError(
            f"{label} digest mismatch: expected {expected_digest}, "
            f"found {actual_digest}"
        )
    return path


def _load_reference(reference: dict[str, Any], label: str) -> tuple[Path, dict[str, Any]]:
    path = _verify_reference_file(reference, label)
    return path, _load_json(path)


def _load_optional_reference(
    reference: dict[str, Any] | None,
    label: str,
) -> dict[str, Any] | None:
    if reference is None:
        return None
    if not isinstance(reference, dict):
        raise Power2ValidationError(f"{label} is not null or a reference")
    _, document = _load_reference(reference, label)
    return document


def _load_pointer_context(
    pointer_path: Path,
) -> ValidationContext:
    pointer = _load_json(pointer_path)
    measurement_reference = pointer.get("measurementStack")
    if not isinstance(measurement_reference, dict):
        raise Power2ValidationError("candidate has no measurement stack")
    _, measurement_stack = _load_reference(
        measurement_reference, "measurement stack"
    )

    program_reference = measurement_stack.get("program")
    target_reference = measurement_stack.get("target")
    policy_references = measurement_stack.get("policies")
    model_references = measurement_stack.get("models")
    if not isinstance(program_reference, dict):
        raise Power2ValidationError("measurement stack has no program")
    if not isinstance(target_reference, dict):
        raise Power2ValidationError("measurement stack has no target")
    if not isinstance(policy_references, dict):
        raise Power2ValidationError("measurement stack has no policies")
    if not isinstance(model_references, dict):
        raise Power2ValidationError("measurement stack has no model registry")

    _, program_manifest = _load_reference(
        program_reference, "program manifest"
    )
    _, target_manifest = _load_reference(target_reference, "target manifest")
    policy_documents: dict[str, dict[str, Any]] = {}
    for name in ("runner", "intake", "ranking"):
        reference = policy_references.get(name)
        if not isinstance(reference, dict):
            raise Power2ValidationError(f"measurement stack has no {name} policy")
        _, policy_documents[name] = _load_reference(
            reference, f"{name} policy"
        )

    assets = program_manifest.get("assets")
    if not isinstance(assets, list):
        raise Power2ValidationError("program manifest has no assets")
    assets_by_role: dict[str, list[dict[str, Any]]] = {}
    assets_by_path: dict[str, dict[str, Any]] = {}
    for asset in assets:
        if not isinstance(asset, dict):
            raise Power2ValidationError("program manifest contains invalid asset")
        role = asset.get("role")
        path = asset.get("path")
        if isinstance(role, str):
            assets_by_role.setdefault(role, []).append(asset)
        if isinstance(path, str):
            assets_by_path[path] = asset
        _verify_reference_file(asset, f"program asset {path}")

    contract_assets = assets_by_role.get("program-contract", [])
    if len(contract_assets) != 1:
        raise Power2ValidationError("program must pin exactly one contract")
    _, program_contract = _load_reference(
        contract_assets[0], "program contract"
    )

    schema_roles = {
        "evidence": "evidence-envelope-schema",
        "submission": "submission-schema",
        "validation": "validation-report-schema",
    }
    schema_paths: dict[str, Path] = {}
    for key, role in schema_roles.items():
        references = assets_by_role.get(role, [])
        if len(references) != 1:
            raise Power2ValidationError(
                f"program must pin exactly one {role}"
            )
        schema_paths[key] = _repo_path(references[0]["path"])

    workloads: dict[str, tuple[dict[str, Any], str]] = {}
    for workload_reference in program_contract.get("workloads", []):
        if not isinstance(workload_reference, dict):
            raise Power2ValidationError("program has invalid workload reference")
        workload_id = workload_reference.get("id")
        path_value = workload_reference.get("path")
        if not isinstance(workload_id, str) or not isinstance(path_value, str):
            raise Power2ValidationError("program workload has no ID or path")
        asset = assets_by_path.get(path_value)
        if asset is None:
            raise Power2ValidationError(
                f"workload is not pinned by program manifest: {path_value}"
            )
        _, workload = _load_reference(asset, f"workload {workload_id}")
        workloads[workload_id] = (workload, asset["sha256"])

    registry_reference = model_references.get("registry")
    if not isinstance(registry_reference, dict):
        raise Power2ValidationError("measurement stack has no model registry")
    _, model_registry = _load_reference(
        registry_reference, "model registry"
    )
    model_entries: dict[str, tuple[dict[str, Any], str]] = {}
    for entry in model_registry.get("entries", []):
        if not isinstance(entry, dict):
            raise Power2ValidationError("model registry has invalid entry")
        entry_id = entry.get("registryEntryID")
        if not isinstance(entry_id, str):
            raise Power2ValidationError("model registry entry has no ID")
        _, manifest = _load_reference(entry, f"model {entry_id}")
        model_entries[entry_id] = (manifest, entry["sha256"])

    return ValidationContext(
        public_intake_open=pointer.get("publicIntakeOpen") is True,
        measurement_stack_sha256=measurement_reference["sha256"],
        program_reference=program_reference,
        target_reference=target_reference,
        policy_references=policy_references,
        policy_documents=policy_documents,
        program_manifest=program_manifest,
        program_contract=program_contract,
        target_manifest=target_manifest,
        workloads=workloads,
        model_entries=model_entries,
        runner_certificate=_load_optional_reference(
            measurement_stack.get("runnerCertificate"),
            "runner certificate",
        ),
        app_release=_load_optional_reference(
            pointer.get("appRelease"), "App release"
        ),
        schema_paths=schema_paths,
    )


def load_candidate_context(
    candidate_path: Path = DEFAULT_CANDIDATE_PATH,
) -> ValidationContext:
    """Load the closed migration candidate for certification and tests."""

    pointer = _load_json(candidate_path)
    if (
        pointer.get("schemaVersion")
        != "power-stack-pointer-1.0.0-draft.1"
        or pointer.get("status") != "migration-draft"
        or pointer.get("publicIntakeOpen") is not False
        or pointer.get("appRelease") is not None
    ):
        raise Power2ValidationError(
            "Power migration candidate is not fail-closed"
        )
    return _load_pointer_context(candidate_path)


def load_product_context(
    current_path: Path = DEFAULT_CURRENT_PATH,
) -> ValidationContext:
    """Load the public Power pointer, failing closed before activation.

    During the migration window, the candidate remains the only trusted
    configuration and carries ``publicIntakeOpen: false``. Once
    ``current.json`` is issued, public tools resolve only that immutable
    pointer without requiring a second CLI or workflow.
    """

    if not current_path.is_file():
        return load_candidate_context(DEFAULT_CANDIDATE_PATH)
    pointer = _load_json(current_path)
    if (
        pointer.get("schemaVersion") != "power-stack-pointer-1.0.0"
        or pointer.get("status") != "active"
        or pointer.get("publicIntakeOpen") is not True
        or not isinstance(pointer.get("appRelease"), dict)
    ):
        raise Power2ValidationError(
            "active Power pointer is incomplete or fail-closed"
        )
    return _load_pointer_context(current_path)


def load_candidate_certification_review_context(
    candidate_path: Path = DEFAULT_NEXT_PATH,
) -> ValidationContext:
    """Open only the next-release gates needed to review smoke evidence.

    This context is intentionally separate from public intake. It accepts the
    source-bound Certification App and synthetic candidate certificate ID so
    a maintainer can review one physical-device result before a new Runner
    certificate or App release exists.
    """

    context = load_product_context()
    candidate = _load_json(candidate_path)
    if (
        candidate.get("schemaVersion") != "power-release-plan-1.0.0"
        or candidate.get("state") != "runner-certification-required"
        or candidate.get("publicIntakeOpen") is not False
        or candidate.get("runnerCertificate") is not None
        or candidate.get("appRelease") is not None
    ):
        raise Power2ValidationError(
            "next Power release is not at the Runner certification gate"
        )
    runner_reference = candidate.get("runnerComponents")
    measurement_stack_reference = candidate.get("measurementStack")
    if not isinstance(runner_reference, dict):
        raise Power2ValidationError(
            "next release has no Runner component identity"
        )
    if not isinstance(measurement_stack_reference, dict):
        raise Power2ValidationError(
            "next release has no measurement stack"
        )
    _, runner_manifest = _load_reference(
        runner_reference,
        "next Runner components",
    )
    _verify_reference_file(
        measurement_stack_reference,
        "next-release measurement stack",
    )
    if (
        runner_manifest.get("schemaVersion")
        != "power-runner-component-manifest-1.0.0"
    ):
        raise Power2ValidationError(
            "next Runner component manifest is unsupported"
        )
    certificate_id = candidate.get("runnerCertificationCandidateID")
    if not isinstance(certificate_id, str):
        raise Power2ValidationError(
            "next release has no Runner certification candidate ID"
        )
    runtime_reference = runner_manifest.get("runtimeIdentity")
    if not isinstance(runtime_reference, dict):
        raise Power2ValidationError(
            "next Runner component manifest has no runtime identity"
        )
    _, runtime = _load_reference(
        runtime_reference,
        "next Runner runtime identity",
    )
    app_identity = candidate.get("app")
    if not isinstance(app_identity, dict):
        raise Power2ValidationError("next release has no App identity")
    app_source_revision = _sha256_file(APP_COMPONENT_PATH)
    review_runner = {
        "state": "active",
        "certificateID": certificate_id,
        "programManifestSHA256":
            context.program_reference.get("sha256"),
        "targetManifestSHA256":
            context.target_reference.get("sha256"),
        "runnerComponents": runner_reference,
        "runtime": {
            key: runtime[key]
            for key in (
                "name",
                "version",
                "resolvedRevision",
                "backend",
                "configuration",
            )
        },
    }
    review_app = {
        "state": "supported",
        "version": "2.0.0-certification",
        "build": app_identity.get("build"),
        "sourceRevision": app_source_revision,
        "supportedRunnerCertificateIDs": [certificate_id],
    }
    return replace(
        context,
        public_intake_open=True,
        measurement_stack_sha256=measurement_stack_reference["sha256"],
        runner_certificate=review_runner,
        app_release=review_app,
    )


def load_candidate_app_release_review_context(
    candidate_path: Path = DEFAULT_NEXT_PATH,
) -> ValidationContext:
    """Open only the gates needed for the closed Official App rehearsal.

    The release-candidate stack already contains an active Runner certificate,
    but public intake remains closed. This context temporarily treats the exact
    Official App candidate as supported so its physical-device result can be
    reviewed without making that result publishable or ranking-eligible.
    """

    candidate = _load_json(candidate_path)
    if (
        candidate.get("schemaVersion") != "power-release-plan-1.0.0"
        or candidate.get("state") != "app-release-rehearsal-required"
        or candidate.get("publicIntakeOpen") is not False
        or candidate.get("appRelease") is not None
    ):
        raise Power2ValidationError(
            "next Power release is not at the Official App rehearsal gate"
        )
    measurement_reference = candidate.get("measurementStack")
    if not isinstance(measurement_reference, dict):
        raise Power2ValidationError(
            "next Power release has no measurement stack"
        )
    _, measurement_stack = _load_reference(
        measurement_reference,
        "next-release measurement stack",
    )
    context = _load_pointer_context(candidate_path)
    app_reference = candidate.get("appReleaseCandidate")
    if not isinstance(app_reference, dict):
        raise Power2ValidationError(
            "candidate has no App release candidate"
        )
    _, app_candidate = _load_reference(
        app_reference,
        "App release candidate",
    )
    certificate = context.runner_certificate
    certificate_id = (
        certificate.get("certificateID")
        if isinstance(certificate, dict)
        else None
    )
    if (
        not isinstance(certificate_id, str)
        or certificate.get("state") != "active"
        or candidate.get("runnerCertificate")
        != measurement_stack.get("runnerCertificate")
        or certificate.get("runnerComponents")
        != candidate.get("runnerComponents")
    ):
        raise Power2ValidationError(
            "App rehearsal has no active Runner certificate"
        )
    if (
        app_candidate.get("state") != "candidate"
        or app_candidate.get("embeddedMeasurementStack")
        != candidate.get("measurementStack")
        or app_candidate.get("appComponents", {}).get("sha256")
        != app_candidate.get("sourceRevision")
        or app_candidate.get("supportedRunnerCertificateIDs")
        != [certificate_id]
    ):
        raise Power2ValidationError(
            "App release candidate is inconsistent with the active stack"
        )
    review_app = {
        "state": "supported",
        "version": app_candidate.get("version"),
        "build": app_candidate.get("build"),
        "sourceRevision": app_candidate.get("sourceRevision"),
        "supportedRunnerCertificateIDs": [certificate_id],
    }
    return replace(
        context,
        public_intake_open=True,
        app_release=review_app,
    )


def _check(status: str, reason_codes: list[str] | None = None) -> dict[str, Any]:
    return {
        "status": status,
        "reasonCodes": list(dict.fromkeys(reason_codes or [])),
    }


def _append_diagnostics(
    diagnostics: list[str],
    prefix: str,
    messages: list[str],
) -> None:
    diagnostics.extend(f"{prefix}: {message}" for message in messages)


def _is_renderable(prefix: str, is_special: bool) -> bool:
    return not is_special and any(
        not character.isspace() for character in prefix
    )


def _raw_attempt_reasons(
    attempt: dict[str, Any],
    index: int,
    diagnostics: list[str],
    maximum_renderability_probe_events: int,
) -> list[str]:
    reasons: list[str] = []
    monotonic = attempt.get("monotonic")
    token_counts = attempt.get("tokenCounts")
    events = attempt.get("tokenEvents")
    memory = attempt.get("memory")
    thermal = attempt.get("thermal")
    if (
        not isinstance(monotonic, dict)
        or not isinstance(token_counts, dict)
        or not isinstance(events, list)
        or not isinstance(memory, dict)
        or not isinstance(thermal, dict)
    ):
        return ["raw-attempt-inconsistent"]

    accepted = monotonic.get("requestAcceptedNanoseconds")
    if accepted != 0:
        reasons.append("raw-attempt-inconsistent")
        diagnostics.append(
            f"attempt {index} request acceptance must be the zero origin"
        )

    received_values: list[int] = []
    renderable_values: list[int] = []
    inspected_event_count = 0
    found_renderable = False
    for event_index, event in enumerate(events):
        if not isinstance(event, dict) or event.get("index") != event_index:
            reasons.append("raw-attempt-inconsistent")
            diagnostics.append(
                f"attempt {index} token event order is not contiguous"
            )
            continue
        received = event.get("receivedNanoseconds")
        if not isinstance(received, int):
            reasons.append("raw-attempt-inconsistent")
            continue
        received_values.append(received)

        decoded_at = event.get("decodedAtNanoseconds")
        decoded_prefix = event.get("decodedPrefix")
        is_special = event.get("isSpecial")
        is_renderable = event.get("isRenderable")
        inspected = (
            isinstance(decoded_at, int)
            and isinstance(decoded_prefix, str)
            and isinstance(is_special, bool)
            and isinstance(is_renderable, bool)
        )
        entirely_uninspected = (
            decoded_at is None
            and decoded_prefix is None
            and is_special is None
            and is_renderable is None
        )
        if inspected:
            inspected_event_count += 1
            if found_renderable:
                reasons.append("raw-attempt-inconsistent")
                diagnostics.append(
                    f"attempt {index} inspected token {event_index} after "
                    "the first renderable event"
                )
            if decoded_at < received:
                reasons.append("raw-attempt-inconsistent")
                diagnostics.append(
                    f"attempt {index} token {event_index} was decoded "
                    "before receipt"
                )
            expected_renderable = _is_renderable(
                decoded_prefix, is_special
            )
            if is_renderable is not expected_renderable:
                reasons.append("raw-attempt-inconsistent")
                diagnostics.append(
                    f"attempt {index} token {event_index} renderability "
                    "does not match its decoded prefix"
                )
            if is_renderable:
                renderable_values.append(decoded_at)
                found_renderable = True
        elif not entirely_uninspected:
            reasons.append("raw-attempt-inconsistent")
            diagnostics.append(
                f"attempt {index} token {event_index} has a partial "
                "renderability probe"
            )

    if inspected_event_count > maximum_renderability_probe_events:
        reasons.append("raw-attempt-inconsistent")
        diagnostics.append(
            f"attempt {index} exceeds the renderability probe limit"
        )

    if received_values != sorted(received_values):
        reasons.append("raw-attempt-inconsistent")
        diagnostics.append(
            f"attempt {index} token receipt times are not monotonic"
        )
    output_count = token_counts.get("output")
    if output_count != len(events):
        reasons.append("raw-attempt-inconsistent")
        diagnostics.append(
            f"attempt {index} output count does not match token events"
        )

    expected_first = received_values[0] if received_values else None
    if monotonic.get("firstTokenNanoseconds") != expected_first:
        reasons.append("raw-attempt-inconsistent")
        diagnostics.append(
            f"attempt {index} first-token summary cannot be reproduced"
        )
    expected_renderable = (
        min(renderable_values) if renderable_values else None
    )
    if monotonic.get("firstRenderableNanoseconds") != expected_renderable:
        reasons.append("raw-attempt-inconsistent")
        diagnostics.append(
            f"attempt {index} first-renderable summary cannot be reproduced"
        )
    expected_decode = (
        received_values[-1] - received_values[0]
        if len(received_values) >= 2
        else None
    )
    if monotonic.get("decodeNanoseconds") != expected_decode:
        reasons.append("raw-attempt-inconsistent")
        diagnostics.append(
            f"attempt {index} decode duration cannot be reproduced"
        )
    completed = monotonic.get("completedNanoseconds")
    if (
        isinstance(completed, int)
        and received_values
        and completed < received_values[-1]
    ):
        reasons.append("raw-attempt-inconsistent")
        diagnostics.append(
            f"attempt {index} completed before its final token event"
        )

    samples = memory.get("samples")
    if not isinstance(samples, list):
        reasons.append("raw-attempt-inconsistent")
    else:
        sample_times: list[int] = []
        sample_values: list[int] = []
        for sample in samples:
            if not isinstance(sample, dict):
                reasons.append("raw-attempt-inconsistent")
                continue
            elapsed = sample.get("elapsedNanoseconds")
            footprint = sample.get("physicalFootprintBytes")
            if not isinstance(elapsed, int) or not isinstance(footprint, int):
                reasons.append("raw-attempt-inconsistent")
                continue
            sample_times.append(elapsed)
            sample_values.append(footprint)
        if sample_times != sorted(sample_times):
            reasons.append("raw-attempt-inconsistent")
            diagnostics.append(
                f"attempt {index} memory samples are not monotonic"
            )
        expected_peak = max(sample_values) if sample_values else None
        if memory.get("peakPhysicalFootprintBytes") != expected_peak:
            reasons.append("raw-attempt-inconsistent")
            diagnostics.append(
                f"attempt {index} memory peak cannot be reproduced"
            )

    transitions = thermal.get("transitions")
    if not isinstance(transitions, list):
        reasons.append("raw-attempt-inconsistent")
    else:
        transition_times: list[int] = []
        transition_states: list[str] = []
        for transition in transitions:
            if not isinstance(transition, dict):
                reasons.append("raw-attempt-inconsistent")
                continue
            elapsed = transition.get("elapsedNanoseconds")
            state = transition.get("state")
            if not isinstance(elapsed, int) or not isinstance(state, str):
                reasons.append("raw-attempt-inconsistent")
                continue
            transition_times.append(elapsed)
            transition_states.append(state)
        if transition_times != sorted(transition_times):
            reasons.append("raw-attempt-inconsistent")
            diagnostics.append(
                f"attempt {index} thermal transitions are not monotonic"
            )
        expected_end = (
            transition_states[-1]
            if transition_states
            else thermal.get("start")
        )
        if thermal.get("end") != expected_end:
            reasons.append("raw-attempt-inconsistent")
            diagnostics.append(
                f"attempt {index} thermal end state cannot be reproduced"
            )
    return list(dict.fromkeys(reasons))


def _contract_reasons(
    result: dict[str, Any],
    context: ValidationContext,
    diagnostics: list[str],
) -> list[str]:
    reasons: list[str] = []
    program = result.get("program")
    target = result.get("target")
    model = result.get("model")
    payload = result.get("payload")

    if not isinstance(program, dict) or (
        program.get("id"),
        program.get("version"),
        program.get("manifestSHA256"),
    ) != (
        context.program_reference.get("id"),
        context.program_reference.get("version"),
        context.program_reference.get("sha256"),
    ):
        reasons.append("program-or-target-digest-mismatch")
        diagnostics.append("program identity does not match trusted stack")

    if not isinstance(target, dict) or (
        target.get("id"),
        target.get("version"),
        target.get("manifestSHA256"),
    ) != (
        context.target_reference.get("id"),
        context.target_reference.get("version"),
        context.target_reference.get("sha256"),
    ):
        reasons.append("program-or-target-digest-mismatch")
        diagnostics.append("target identity does not match trusted stack")

    if not isinstance(model, dict):
        reasons.append("model-artifact-not-registered")
        diagnostics.append("model identity is missing")
    else:
        entry_id = model.get("registryEntryID")
        registered = context.model_entries.get(entry_id)
        if registered is None:
            reasons.append("model-artifact-not-registered")
            diagnostics.append(f"model registry entry is unknown: {entry_id!r}")
        else:
            manifest, manifest_digest = registered
            expected = (
                manifest_digest,
                manifest.get("artifactID"),
                manifest.get("artifactRevision"),
                manifest.get("parameterCount"),
                manifest.get("quantization"),
                manifest.get("format"),
            )
            actual = (
                model.get("registryEntrySHA256"),
                model.get("artifactID"),
                model.get("artifactRevision"),
                model.get("parameterCount"),
                model.get("quantization"),
                model.get("format"),
            )
            if actual != expected:
                reasons.append("model-artifact-identity-mismatch")
                diagnostics.append(
                    "result model snapshot does not match its registered manifest"
                )

    if not isinstance(payload, dict):
        reasons.append("invalid-program-payload")
        diagnostics.append("program payload is missing")
        return list(dict.fromkeys(reasons))

    workload_reference = payload.get("workload")
    workload_id = (
        workload_reference.get("id")
        if isinstance(workload_reference, dict)
        else None
    )
    registered_workload = context.workloads.get(workload_id)
    if registered_workload is None:
        reasons.append("unsupported-workload")
        diagnostics.append(f"workload is not registered: {workload_id!r}")
        return list(dict.fromkeys(reasons))

    workload, workload_digest = registered_workload
    if (
        workload_reference.get("version") != workload.get("workloadVersion")
        or workload_reference.get("sha256") != workload_digest
    ):
        reasons.append("workload-identity-mismatch")
        diagnostics.append("workload version or digest does not match")
    if payload.get("measurementMode") != workload.get("measurementMode"):
        reasons.append("measurement-mode-mismatch")
        diagnostics.append("measurement mode does not match workload")
    if payload.get("inferenceConfiguration") != workload.get("generation"):
        reasons.append("inference-configuration-mismatch")
        diagnostics.append("inference configuration does not match workload")

    attempts = payload.get("attempts")
    if not isinstance(attempts, list):
        reasons.append("invalid-attempt-sequence")
        return list(dict.fromkeys(reasons))
    renderability_policy = context.program_contract.get(
        "renderabilityPolicy", {}
    )
    maximum_renderability_probe_events = renderability_policy.get(
        "maximumProbeEvents"
    )
    if (
        not isinstance(maximum_renderability_probe_events, int)
        or maximum_renderability_probe_events < 1
    ):
        reasons.append("invalid-program-contract")
        diagnostics.append(
            "program contract has no valid renderability probe limit"
        )
        maximum_renderability_probe_events = 0

    for index, attempt in enumerate(attempts):
        if not isinstance(attempt, dict):
            reasons.append("invalid-attempt-sequence")
            continue
        if attempt.get("index") != index:
            reasons.append("invalid-attempt-sequence")
        reasons.extend(
            _raw_attempt_reasons(
                attempt,
                index,
                diagnostics,
                maximum_renderability_probe_events,
            )
        )
        if attempt.get("outcome") != "succeeded":
            continue
        monotonic = attempt.get("monotonic")
        if not isinstance(monotonic, dict):
            reasons.append("invalid-monotonic-timing")
            continue
        accepted = monotonic.get("requestAcceptedNanoseconds")
        first_token = monotonic.get("firstTokenNanoseconds")
        completed = monotonic.get("completedNanoseconds")
        first_renderable = monotonic.get("firstRenderableNanoseconds")
        if (
            not isinstance(accepted, int)
            or not isinstance(first_token, int)
            or not isinstance(completed, int)
            or not accepted <= first_token <= completed
        ):
            reasons.append("invalid-monotonic-timing")
            diagnostics.append(f"attempt {index} has impossible token timing")
        if first_renderable is not None and (
            not isinstance(first_renderable, int)
            or not isinstance(accepted, int)
            or not isinstance(completed, int)
            or not accepted <= first_renderable <= completed
        ):
            reasons.append("invalid-monotonic-timing")
            diagnostics.append(
                f"attempt {index} has impossible renderable timing"
            )
        for duration_name in (
            "promptEvaluationNanoseconds",
            "decodeNanoseconds",
        ):
            duration = monotonic.get(duration_name)
            if not isinstance(duration, int) or duration <= 0:
                reasons.append("invalid-monotonic-timing")
                diagnostics.append(
                    f"attempt {index} has invalid {duration_name}"
                )

    if (
        context.program_contract.get("externalArtifactsAllowed") is False
        and result.get("artifacts") != []
    ):
        reasons.append("unsupported-external-artifacts")
        diagnostics.append(
            "text-generation two-file packages cannot reference external artifacts"
        )
    return list(dict.fromkeys(reasons))


def _ordinary_target_reasons(
    result: dict[str, Any],
    context: ValidationContext,
) -> list[str]:
    environment = result.get("environment")
    if not isinstance(environment, dict):
        return ["target-environment-ineligible"]
    admission = context.target_manifest.get("ordinaryRankingAdmission", {})
    reasons: list[str] = []
    if environment.get("batteryStateAtStart") != admission.get(
        "batteryStateAtStart"
    ):
        reasons.append("battery-state-ineligible")
    battery_level = environment.get("batteryLevelAtStart")
    minimum = admission.get("minimumBatteryPercentAtStart")
    if (
        not isinstance(battery_level, (int, float))
        or not isinstance(minimum, (int, float))
        or battery_level * 100 < minimum
    ):
        reasons.append("battery-level-ineligible")
    if environment.get("lowPowerModeAtStart") is not admission.get(
        "lowPowerModeAtStart"
    ):
        reasons.append("low-power-mode-ineligible")
    if environment.get("thermalStateAtStart") not in admission.get(
        "allowedThermalStatesAtStart", []
    ):
        reasons.append("start-thermal-state-ineligible")
    if environment.get("thermalAssistance") != admission.get(
        "thermalAssistance"
    ):
        reasons.append("thermal-assistance-ineligible")
    return reasons


def _metric_checks(
    result: dict[str, Any],
    context: ValidationContext,
    contract_valid: bool,
) -> dict[str, dict[str, Any]]:
    checks: dict[str, dict[str, Any]] = {}
    metrics = context.program_contract.get("metrics", [])
    payload = result.get("payload")
    attempts = payload.get("attempts", []) if isinstance(payload, dict) else []
    measured_successes = [
        attempt
        for attempt in attempts
        if isinstance(attempt, dict)
        and attempt.get("phase") == "measured"
        and attempt.get("outcome") == "succeeded"
    ]
    minimum = context.program_contract.get("attemptContract", {}).get(
        "minimumSuccessfulMeasuredAttemptsPerMetric", 3
    )
    target_reasons = _ordinary_target_reasons(result, context)
    workload_id = (
        payload.get("workload", {}).get("id")
        if isinstance(payload, dict)
        and isinstance(payload.get("workload"), dict)
        else None
    )

    for metric in metrics:
        metric_id = metric.get("id")
        if not isinstance(metric_id, str):
            continue
        scope = metric.get("scope")
        if (
            scope == "interactive-workload-only"
            and workload_id != "power.text.short-interaction"
        ) or (
            scope == "sustained-workload-only"
            and workload_id != "power.text.sustained-generation"
        ):
            checks[metric_id] = _check(
                "not-applicable", ["metric-not-defined-for-workload"]
            )
            continue
        if not contract_valid:
            checks[metric_id] = _check(
                "not-applicable", ["contract-conformance-failed"]
            )
            continue
        if target_reasons:
            checks[metric_id] = _check("not-applicable", target_reasons)
            continue

        eligible_attempts = 0
        for attempt in measured_successes:
            monotonic = attempt.get("monotonic", {})
            tokens = attempt.get("tokenCounts", {})
            memory = attempt.get("memory", {})
            eligible = {
                "first_renderable_ms": isinstance(
                    monotonic.get("firstRenderableNanoseconds"), int
                ),
                "pipeline_ttft_ms": isinstance(
                    monotonic.get("firstTokenNanoseconds"), int
                ),
                "request_completion_ms": isinstance(
                    monotonic.get("completedNanoseconds"), int
                ),
                "prefill_tokens_per_second": (
                    isinstance(monotonic.get("promptEvaluationNanoseconds"), int)
                    and monotonic["promptEvaluationNanoseconds"] > 0
                    and isinstance(tokens.get("input"), int)
                    and tokens["input"] > 0
                ),
                "decode_tokens_per_second": (
                    isinstance(monotonic.get("decodeNanoseconds"), int)
                    and monotonic["decodeNanoseconds"] > 0
                    and isinstance(tokens.get("output"), int)
                    and tokens["output"] >= 2
                ),
                "peak_physical_footprint_mib": isinstance(
                    memory.get("peakPhysicalFootprintBytes"), int
                ),
                "decode_first_to_last_percent_change": (
                    isinstance(monotonic.get("decodeNanoseconds"), int)
                    and monotonic["decodeNanoseconds"] > 0
                    and isinstance(tokens.get("output"), int)
                    and tokens["output"] >= 2
                ),
            }.get(metric_id, False)
            if eligible:
                eligible_attempts += 1

        if eligible_attempts >= minimum:
            checks[metric_id] = _check("pass")
        else:
            checks[metric_id] = _check(
                "not-applicable",
                ["insufficient-successful-measured-attempts"],
            )
    return checks


def _normalize_behavior_text(text: str) -> str:
    return " ".join(
        unicodedata.normalize("NFKC", text).casefold().split()
    )


def _behavior_attempt_status(
    generated_text: Any,
    response_contract: dict[str, Any],
) -> str:
    if not isinstance(generated_text, str):
        return "not-verified"
    normalized = _normalize_behavior_text(generated_text)
    if not normalized:
        return "not-verified"

    maximum_sentences = response_contract.get("maximumSentences")
    if not isinstance(maximum_sentences, int) or maximum_sentences < 1:
        raise Power2ValidationError(
            "response contract has no valid sentence limit"
        )
    sentence_count = len(
        [
            part
            for part in re.split(r"[.!?]+", normalized)
            if part.strip()
        ]
    )
    if sentence_count > maximum_sentences:
        return "not-verified"

    policy = response_contract.get("verificationPolicy")
    if not isinstance(policy, dict):
        raise Power2ValidationError(
            "response contract has no verification policy"
        )
    contradiction_phrases = policy.get("contradictionPhrases")
    concepts = policy.get("concepts")
    if (
        not isinstance(contradiction_phrases, list)
        or not all(
            isinstance(phrase, str) and phrase
            for phrase in contradiction_phrases
        )
        or not isinstance(concepts, list)
        or not concepts
    ):
        raise Power2ValidationError(
            "response verification policy is invalid"
        )
    if any(
        _normalize_behavior_text(phrase) in normalized
        for phrase in contradiction_phrases
    ):
        return "contradicted"

    tokens = set(re.findall(r"[^\W_]+", normalized, flags=re.UNICODE))
    for concept in concepts:
        term_groups = (
            concept.get("allOfTermGroups")
            if isinstance(concept, dict)
            else None
        )
        if (
            not isinstance(term_groups, list)
            or not term_groups
            or not all(
                isinstance(group, list)
                and group
                and all(isinstance(term, str) and term for term in group)
                for group in term_groups
            )
        ):
            raise Power2ValidationError(
                "response verification concept is invalid"
            )
        if any(
            tokens.isdisjoint(
                _normalize_behavior_text(term)
                for term in group
            )
            for group in term_groups
        ):
            return "not-verified"
    return "verified"


def _behavior_checks(
    result: dict[str, Any],
    context: ValidationContext,
    contract_valid: bool,
    diagnostics: list[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = result.get("payload")
    workload_id = (
        payload.get("workload", {}).get("id")
        if isinstance(payload, dict)
        and isinstance(payload.get("workload"), dict)
        else None
    )
    registered = context.workloads.get(workload_id)
    response_contract = (
        registered[0].get("responseContract")
        if registered is not None
        else None
    )
    if response_contract is None:
        return (
            _check("not-applicable", ["behavior-not-defined-for-workload"]),
            _check(
                "not-applicable",
                ["recommendation-not-defined-for-workload"],
            ),
        )
    if not isinstance(response_contract, dict):
        raise Power2ValidationError("workload response contract is invalid")
    if response_contract.get("affectsMetricEligibility") is not False:
        raise Power2ValidationError(
            "behavior must not affect Power performance metric eligibility"
        )
    if not contract_valid:
        return (
            _check(
                "not-applicable",
                ["contract-conformance-failed"],
            ),
            _check(
                "not-applicable",
                ["contract-conformance-failed"],
            ),
        )

    policy = response_contract.get("verificationPolicy")
    minimum = (
        policy.get("minimumVerifiedMeasuredAttempts")
        if isinstance(policy, dict)
        else None
    )
    if not isinstance(minimum, int) or minimum < 1:
        raise Power2ValidationError(
            "response verification policy has no valid attempt threshold"
        )
    attempts = (
        payload.get("attempts", [])
        if isinstance(payload, dict)
        else []
    )
    measured_successes = [
        attempt
        for attempt in attempts
        if isinstance(attempt, dict)
        and attempt.get("phase") == "measured"
        and attempt.get("outcome") == "succeeded"
    ]
    statuses = [
        _behavior_attempt_status(
            attempt.get("generatedText"),
            response_contract,
        )
        for attempt in measured_successes
    ]
    verified_count = statuses.count("verified")
    contradicted_count = statuses.count("contradicted")
    not_verified_count = statuses.count("not-verified")
    diagnostics.append(
        "behavior: "
        f"verified={verified_count}, "
        f"contradicted={contradicted_count}, "
        f"not-verified={not_verified_count}, "
        f"required={minimum}"
    )

    if contradicted_count:
        behavior = _check("fail", ["behavior-contradicted"])
    elif verified_count >= minimum:
        behavior = _check("pass")
    else:
        behavior = _check(
            "manual-review",
            ["behavior-not-verified"],
        )

    if response_contract.get("affectsRecommendationEligibility") is not True:
        recommendation = _check(
            "not-applicable",
            ["recommendation-not-defined-for-workload"],
        )
    elif behavior["status"] == "pass":
        recommendation = _check("pass")
    elif behavior["status"] == "fail":
        recommendation = _check(
            "fail",
            ["behavior-conformance-failed"],
        )
    else:
        recommendation = _check(
            "manual-review",
            ["behavior-not-verified"],
        )
    return behavior, recommendation


def _runner_check(
    result: dict[str, Any],
    context: ValidationContext,
) -> dict[str, Any]:
    certificate = context.runner_certificate
    if certificate is None:
        return _check("fail", ["runner-certificate-not-active"])
    if (
        certificate.get("state") != "active"
        or result.get("runnerCertificateID")
        != certificate.get("certificateID")
        or certificate.get("programManifestSHA256")
        != context.program_reference.get("sha256")
        or certificate.get("targetManifestSHA256")
        != context.target_reference.get("sha256")
    ):
        return _check("fail", ["runner-certificate-not-active"])
    runtime = result.get("runtime")
    expected_runtime = certificate.get("runtime")
    if isinstance(expected_runtime, dict) and runtime != expected_runtime:
        return _check("fail", ["runner-runtime-identity-mismatch"])
    return _check("pass")


def _app_release_check(
    result: dict[str, Any],
    context: ValidationContext,
) -> dict[str, Any]:
    app_release = context.app_release
    actual = result.get("appRelease")
    if app_release is None or not isinstance(actual, dict):
        return _check("fail", ["app-release-not-supported"])
    expected = (
        app_release.get("version"),
        app_release.get("build"),
        app_release.get("sourceRevision"),
        context.measurement_stack_sha256,
    )
    actual_identity = (
        actual.get("version"),
        actual.get("build"),
        actual.get("sourceRevision"),
        actual.get("embeddedMeasurementStackSHA256"),
    )
    supported_certificates = app_release.get(
        "supportedRunnerCertificateIDs", []
    )
    if (
        app_release.get("state") != "supported"
        or actual_identity != expected
        or result.get("runnerCertificateID") not in supported_certificates
    ):
        return _check("fail", ["app-release-not-supported"])
    return _check("pass")


def validate_package(
    package: Path,
    *,
    context: ValidationContext | None = None,
    evaluated_at: str,
    validator_source_revision: str,
    pr_author: str | None,
    accepted_result_digests: set[str] | None = None,
) -> dict[str, Any]:
    context = context or load_product_context()
    package = Path(package)
    diagnostics: list[str] = []
    structural_reasons: list[str] = []
    digest_reasons: list[str] = []
    contributor_reasons: list[str] = []

    submission_path = package / "submission.json"
    result_path = package / "result.json"
    submission_bytes = (
        submission_path.read_bytes()
        if submission_path.is_file() and not submission_path.is_symlink()
        else b""
    )
    result_bytes = (
        result_path.read_bytes()
        if result_path.is_file() and not result_path.is_symlink()
        else b""
    )
    submission_digest = _sha256_bytes(submission_bytes)
    result_digest = _sha256_bytes(result_bytes)

    if not package.is_dir():
        structural_reasons.append("submission-package-not-directory")
    else:
        entries = {path.name for path in package.iterdir()}
        if entries != ALLOWED_PACKAGE_FILES:
            structural_reasons.append("submission-package-file-set-invalid")
            diagnostics.append(
                f"package files must be {sorted(ALLOWED_PACKAGE_FILES)}, "
                f"found {sorted(entries)}"
            )
        for path in (submission_path, result_path):
            if path.is_symlink() or not path.is_file():
                structural_reasons.append("submission-package-file-invalid")

    submission: dict[str, Any] = {}
    result: dict[str, Any] = {}
    try:
        loaded = json.loads(submission_bytes)
        if isinstance(loaded, dict):
            submission = loaded
        else:
            structural_reasons.append("invalid-submission-schema")
    except (UnicodeDecodeError, json.JSONDecodeError):
        structural_reasons.append("invalid-submission-schema")
    try:
        loaded = json.loads(result_bytes)
        if isinstance(loaded, dict):
            result = loaded
        else:
            structural_reasons.append("invalid-envelope")
    except (UnicodeDecodeError, json.JSONDecodeError):
        structural_reasons.append("invalid-envelope")

    if submission.get("schemaVersion") != "power-submission-1.0.0-draft.1":
        structural_reasons.append("unsupported-major-version")
    else:
        errors = json_schema.validate(
            submission, context.schema_paths["submission"], ROOT
        )
        if errors:
            structural_reasons.append("invalid-submission-schema")
            _append_diagnostics(diagnostics, "submission", errors)

    if result.get("schemaVersion") != "power-evidence-envelope-1.0.0-draft.1":
        structural_reasons.append("unsupported-major-version")
    else:
        errors = json_schema.validate(
            result, context.schema_paths["evidence"], ROOT
        )
        if errors:
            structural_reasons.append("invalid-envelope")
            _append_diagnostics(diagnostics, "result", errors)

    source_reference = submission.get("sourceResult")
    if not isinstance(source_reference, dict):
        digest_reasons.append("result-reference-missing")
    else:
        if source_reference.get("path") != "result.json":
            digest_reasons.append("result-reference-mismatch")
        if source_reference.get("sha256") != result_digest:
            digest_reasons.append("result-digest-mismatch")
        if source_reference.get("schemaVersion") != result.get("schemaVersion"):
            digest_reasons.append("result-reference-mismatch")
    submission_identifier = _canonical_uuid_text(
        submission.get("submissionID")
    )
    directory_identifier = _canonical_uuid_text(package.name)
    if (
        submission_identifier is None
        or directory_identifier is None
        or submission_identifier != directory_identifier
    ):
        digest_reasons.append("submission-directory-identity-mismatch")
    if result_digest in (accepted_result_digests or set()):
        digest_reasons.append("duplicate-result-sha256")

    contract_reasons = (
        _contract_reasons(result, context, diagnostics)
        if not structural_reasons
        else ["structural-validity-failed"]
    )
    contract_valid = not contract_reasons

    contributor = submission.get("contributor")
    github_login = (
        contributor.get("githubLogin")
        if isinstance(contributor, dict)
        else None
    )
    if pr_author is None:
        contributor_status = "manual-review"
        contributor_reasons.append("contributor-identity-unavailable")
    elif not isinstance(github_login, str) or github_login.casefold() != pr_author.casefold():
        contributor_status = "fail"
        contributor_reasons.append("contributor-identity-mismatch")
    else:
        contributor_status = "pass"

    manual_reasons: list[str] = []
    if isinstance(contributor, dict) and contributor.get("conflictOfInterest") == "disclosed":
        manual_reasons.append("declared-conflict-of-interest")
    environment = result.get("environment")
    if isinstance(environment, dict):
        if environment.get("thermalAssistance") != "none":
            manual_reasons.append("thermal-assistance-not-none")
        if "unknown" in (
            environment.get("batteryStateAtStart"),
            environment.get("thermalStateAtStart"),
            environment.get("thermalStateAtEnd"),
            environment.get("thermalAssistance"),
        ):
            manual_reasons.append("unknown-environment-field")

    behavior, recommendation = _behavior_checks(
        result,
        context,
        contract_valid,
        diagnostics,
    )
    checks = {
        "structuralValidity": _check(
            "pass" if not structural_reasons else "fail",
            structural_reasons,
        ),
        "contractConformance": _check(
            "pass" if contract_valid else "fail",
            contract_reasons,
        ),
        "digestIntegrity": _check(
            "pass" if not digest_reasons else "fail",
            digest_reasons,
        ),
        "runnerCertificate": _runner_check(result, context),
        "appRelease": _app_release_check(result, context),
        "intakeState": _check(
            "pass" if context.public_intake_open else "fail",
            [] if context.public_intake_open else ["public-intake-closed"],
        ),
        "contributor": _check(contributor_status, contributor_reasons),
        "behaviorConformance": behavior,
        "recommendationEligibility": recommendation,
        "metricEligibility": _metric_checks(
            result, context, contract_valid
        ),
    }

    intake_policy = context.policy_documents["intake"]
    hard_checks = intake_policy.get("hardRejectChecks")
    manual_checks = intake_policy.get("manualReviewChecks")
    if (
        not isinstance(hard_checks, list)
        or not hard_checks
        or not all(
            isinstance(name, str) and name in checks
            for name in hard_checks
        )
    ):
        raise Power2ValidationError(
            "intake policy has invalid hardRejectChecks"
        )
    if (
        not isinstance(manual_checks, list)
        or not all(
            isinstance(name, str) and name in checks
            for name in manual_checks
        )
    ):
        raise Power2ValidationError(
            "intake policy has invalid manualReviewChecks"
        )
    hard_failure = any(
        checks[name]["status"] == "fail" for name in hard_checks
    )
    check_requires_review = any(
        checks[name]["status"] == "manual-review"
        for name in manual_checks
    )
    if hard_failure:
        classification = "reject"
    elif check_requires_review or manual_reasons:
        classification = "manual-review"
    else:
        classification = "auto-accept"

    reason_codes: list[str] = []
    reason_check_names = list(dict.fromkeys(hard_checks + manual_checks))
    for name in reason_check_names:
        reason_codes.extend(checks[name]["reasonCodes"])
    reason_codes.extend(manual_reasons)
    reason_codes = list(dict.fromkeys(reason_codes))

    intake_policy_digest = context.policy_references["intake"]["sha256"]
    report_identity = "|".join(
        (
            result_digest,
            submission_digest,
            intake_policy_digest,
            evaluated_at,
            validator_source_revision,
        )
    )
    report = {
        "schemaVersion": "power-validation-report-1.0.0-draft.2",
        "reportID": str(uuid.uuid5(uuid.NAMESPACE_URL, report_identity)),
        "createdAt": evaluated_at,
        "validator": {
            "name": VALIDATOR_NAME,
            "version": VALIDATOR_VERSION,
            "sourceRevision": validator_source_revision,
            "policySHA256": intake_policy_digest,
        },
        "sourceResultSHA256": result_digest,
        "submissionSHA256": submission_digest,
        "checks": checks,
        "classification": classification,
        "reasonCodes": reason_codes,
        "diagnostics": diagnostics or ["validation completed without diagnostics"],
    }
    report_errors = json_schema.validate(
        report, context.schema_paths["validation"], ROOT
    )
    if report_errors:
        raise Power2ValidationError(
            "validator emitted an invalid report: " + "; ".join(report_errors)
        )
    return report
