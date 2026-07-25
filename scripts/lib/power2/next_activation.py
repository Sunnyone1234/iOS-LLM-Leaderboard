"""Atomically render a reviewed subsequent Power release activation."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from scripts.lib.power2.activation import (
        _json,
        _json_bytes,
        _reference,
        _rendered_reference,
        _revision,
        _review_failure_summary,
        _sha256_bytes,
        _timestamp,
    )
    from scripts.review_power2_app_release_result import review_result
except ModuleNotFoundError:
    from lib.power2.activation import (
        _json,
        _json_bytes,
        _reference,
        _rendered_reference,
        _revision,
        _review_failure_summary,
        _sha256_bytes,
        _timestamp,
    )
    from review_power2_app_release_result import review_result


ROOT = Path(__file__).resolve().parents[3]
NEXT_PATH = ROOT / "products/power/next.json"
CURRENT_PATH = ROOT / "products/power/current.json"
REGISTRY_PATH = ROOT / "products/power/registry.json"
APP_COMPONENT_PATH = ROOT / "apps/ios/component-manifest.json"
APP_RELEASE_ROOT = ROOT / "products/power/app-releases"
APP_EVIDENCE_ROOT = APP_RELEASE_ROOT / "evidence"


class Power2NextActivationError(ValueError):
    """Raised when a later release cannot be activated safely."""


@dataclass(frozen=True)
class NextActivationFiles:
    """Complete file set for one reviewed subsequent activation commit."""

    files: dict[Path, bytes]
    summary: dict[str, Any]


def _pinned(
    value: Any,
    label: str,
) -> tuple[Path, dict[str, str]]:
    try:
        return _reference(value, label)
    except (OSError, ValueError) as error:
        raise Power2NextActivationError(str(error)) from error


def _load(path: Path, label: str) -> dict[str, Any]:
    try:
        return _json(path)
    except (OSError, ValueError) as error:
        raise Power2NextActivationError(
            f"cannot read {label}: {error}"
        ) from error


def render_next_activation(
    result_path: Path,
    *,
    reviewed_at: str,
    validator_source_revision: str,
    activated_at: str,
) -> NextActivationFiles:
    """Review one exact rehearsal and render the atomic upgrade set."""

    try:
        reviewed_at = _timestamp(reviewed_at, "reviewed_at")
        activated_at = _timestamp(activated_at, "activated_at")
        validator_source_revision = _revision(
            validator_source_revision
        )
    except ValueError as error:
        raise Power2NextActivationError(str(error)) from error

    current_bytes = CURRENT_PATH.read_bytes()
    current = _load(CURRENT_PATH, "active Power pointer")
    registry = _load(REGISTRY_PATH, "Power registry")
    next_release = _load(NEXT_PATH, "next Power release")
    if (
        current.get("schemaVersion") != "power-stack-pointer-1.0.0"
        or current.get("status") != "active"
        or current.get("publicIntakeOpen") is not True
        or registry.get("schemaVersion")
        != "power-product-registry-1.0.0"
        or registry.get("status") != "active"
        or registry.get("publicIntakeOpen") is not True
        or registry.get("currentStack")
        != "products/power/current.json"
        or registry.get("nextRelease") != "products/power/next.json"
    ):
        raise Power2NextActivationError(
            "current Power release and registry are not active"
        )
    if (
        next_release.get("schemaVersion")
        != "power-release-plan-1.0.0"
        or next_release.get("productID") != "power"
        or next_release.get("state")
        != "app-release-rehearsal-required"
        or next_release.get("publicIntakeOpen") is not False
        or next_release.get("appRelease") is not None
    ):
        raise Power2NextActivationError(
            "next Power release is not at the App rehearsal gate"
        )

    base_path, base_reference = _pinned(
        next_release.get("baseRelease"),
        "next release base pointer",
    )
    if (
        base_path != CURRENT_PATH.resolve()
        or base_reference["sha256"] != _sha256_bytes(current_bytes)
    ):
        raise Power2NextActivationError(
            "next release is not based on the exact active pointer"
        )
    _, measurement_stack = _pinned(
        next_release.get("measurementStack"),
        "next measurement stack",
    )
    _, runner_components = _pinned(
        next_release.get("runnerComponents"),
        "next Runner components",
    )
    certificate_path, runner_certificate = _pinned(
        next_release.get("runnerCertificate"),
        "next Runner certificate",
    )
    runner_certificate_value = _load(
        certificate_path,
        "next Runner certificate",
    )
    candidate_path, candidate_reference = _pinned(
        next_release.get("appReleaseCandidate"),
        "next App release candidate",
    )
    candidate = _load(candidate_path, "next App release candidate")
    component_path, candidate_components = _pinned(
        candidate.get("appComponents"),
        "next App component manifest",
    )
    component_bytes = component_path.read_bytes()
    if (
        candidate.get("schemaVersion")
        != "power-app-release-candidate-1.0.0-draft.1"
        or candidate.get("state") != "candidate"
        or candidate.get("sourceRevision")
        != candidate_components["sha256"]
        or candidate.get("embeddedMeasurementStack")
        != measurement_stack
        or candidate.get("verification")
        != {
            "sourceAndDependencyIntegrity": "pass",
            "genericIOSReleaseBuild": "pass",
            "physicalDeviceEndToEndRehearsal": "pending",
        }
        or runner_certificate_value.get("state") != "active"
        or runner_certificate_value.get("runnerComponents")
        != runner_components
        or candidate.get("supportedRunnerCertificateIDs")
        != [runner_certificate_value.get("certificateID")]
    ):
        raise Power2NextActivationError(
            "next App candidate and Runner certificate are inconsistent"
        )
    if (
        APP_COMPONENT_PATH.read_bytes() != component_bytes
        or _sha256_bytes(component_bytes)
        != candidate.get("sourceRevision")
    ):
        raise Power2NextActivationError(
            "working App source no longer matches the frozen candidate"
        )

    result_path = Path(result_path)
    result_bytes = result_path.read_bytes()
    try:
        result = json.loads(result_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Power2NextActivationError(
            f"Official result is not valid JSON: {error}"
        ) from error
    if not isinstance(result, dict):
        raise Power2NextActivationError(
            "Official result must be a JSON object"
        )
    try:
        result_id = str(uuid.UUID(str(result.get("resultID"))))
    except ValueError as error:
        raise Power2NextActivationError(
            "Official result has no canonical UUID result ID"
        ) from error

    try:
        review = review_result(
            result_path,
            evaluated_at=reviewed_at,
            validator_source_revision=validator_source_revision,
        )
    except (OSError, ValueError) as error:
        raise Power2NextActivationError(
            f"cannot review Official result: {error}"
        ) from error
    if (
        review.get("status") != "pass"
        or review.get("physicalDeviceEndToEndRehearsal") != "pass"
        or review.get("classification") != "auto-accept"
        or review.get("publishable") is not False
        or review.get("rankingEligible") is not False
    ):
        raise Power2NextActivationError(
            "Official result did not pass the closed App release review: "
            + _review_failure_summary(review)
        )

    expected_app = {
        "version": candidate.get("version"),
        "build": candidate.get("build"),
        "sourceRevision": candidate.get("sourceRevision"),
        "embeddedMeasurementStackSHA256": measurement_stack["sha256"],
    }
    certificate_id = runner_certificate_value.get("certificateID")
    if (
        result.get("appRelease") != expected_app
        or result.get("runnerCertificateID") != certificate_id
        or review.get("appRelease") != expected_app
        or review.get("runnerCertificateID") != certificate_id
        or review.get("sourceResultSHA256")
        != _sha256_bytes(result_bytes)
    ):
        raise Power2NextActivationError(
            "Official result does not match the exact staged release"
        )

    evidence_root = APP_EVIDENCE_ROOT / result_id
    result_output = evidence_root / "result.json"
    review_output = evidence_root / "review.json"
    component_output = evidence_root / "app-component-manifest.json"
    base_output = evidence_root / "base-current.json"
    release_output = APP_RELEASE_ROOT / (
        f"power-app-{candidate['version']}-build."
        f"{candidate['build']}-{candidate['sourceRevision'][:12]}.json"
    )
    for output in (
        result_output,
        review_output,
        component_output,
        base_output,
        release_output,
    ):
        if output.exists():
            raise Power2NextActivationError(
                "activation output already exists: "
                + output.relative_to(ROOT).as_posix()
            )

    review_bytes = _json_bytes(review)
    result_reference = _rendered_reference(
        result_output,
        result_bytes,
    )
    review_reference = _rendered_reference(
        review_output,
        review_bytes,
    )
    component_reference = _rendered_reference(
        component_output,
        component_bytes,
    )
    base_snapshot_reference = _rendered_reference(
        base_output,
        current_bytes,
    )
    release_evidence = {
        "result": result_reference,
        "review": review_reference,
    }
    app_release = {
        "schemaVersion": "power-app-release-1.0.0",
        "productID": "power",
        "releaseID": (
            f"power-app-{candidate['version']}-build."
            f"{candidate['build']}-{candidate['sourceRevision'][:12]}"
        ),
        "state": "supported",
        "issuedAt": activated_at,
        "version": candidate["version"],
        "build": candidate["build"],
        "sourceRevision": candidate["sourceRevision"],
        "bundleIdentifier": candidate["bundleIdentifier"],
        "buildConfiguration": "Official",
        "appComponents": component_reference,
        "embeddedMeasurementStack": measurement_stack,
        "supportedRunnerCertificateIDs": [certificate_id],
        "releaseEvidence": release_evidence,
        "verification": {
            "sourceAndDependencyIntegrity": "pass",
            "genericIOSReleaseBuild": "pass",
            "physicalDeviceEndToEndRehearsal": "pass",
            "rawResultReview": "pass",
        },
    }
    release_bytes = _json_bytes(app_release)
    release_reference = _rendered_reference(
        release_output,
        release_bytes,
    )
    advanced_current = {
        "schemaVersion": "power-stack-pointer-1.0.0",
        "productID": "power",
        "stackID": next_release["stackID"],
        "status": "active",
        "publicIntakeOpen": True,
        "activatedAt": activated_at,
        "measurementStack": measurement_stack,
        "runnerComponents": runner_components,
        "runnerCertificate": runner_certificate,
        "appRelease": release_reference,
        "activationEvidence": release_evidence,
    }
    advanced_plan = {
        **next_release,
        "state": "activated",
        "activatedAt": activated_at,
        "baseRelease": base_snapshot_reference,
        "appRelease": release_reference,
        "activationEvidence": release_evidence,
    }
    measurement_stack_value = _load(
        ROOT / measurement_stack["path"],
        "next measurement stack",
    )
    program = measurement_stack_value.get("program")
    target = measurement_stack_value.get("target")
    if not isinstance(program, dict) or not isinstance(target, dict):
        raise Power2NextActivationError(
            "next measurement stack has no program or target"
        )
    advanced_registry = {
        **registry,
        "activatedAt": activated_at,
        "programs": [
            {
                "id": program.get("id"),
                "manifest": program.get("path"),
                "status": "active",
                "currentVersion": program.get("version"),
            }
        ],
        "targets": [
            {
                "id": target.get("id"),
                "manifest": target.get("path"),
                "status": "active",
                "currentVersion": target.get("version"),
            }
        ],
    }
    files = {
        result_output: result_bytes,
        review_output: review_bytes,
        component_output: component_bytes,
        base_output: current_bytes,
        release_output: release_bytes,
        CURRENT_PATH: _json_bytes(advanced_current),
        NEXT_PATH: _json_bytes(advanced_plan),
        REGISTRY_PATH: _json_bytes(advanced_registry),
    }
    return NextActivationFiles(
        files=files,
        summary={
            "status": "ready",
            "resultID": result_id,
            "sourceResultSHA256": result_reference["sha256"],
            "appRelease": release_reference,
            "candidateReference": candidate_reference,
            "previousCurrentSnapshot": base_snapshot_reference,
            "currentPointer": "products/power/current.json",
            "completedReleasePlan": "products/power/next.json",
            "publicIntakeOpen": True,
            "fileCount": len(files),
        },
    )


def write_next_activation(rendered: NextActivationFiles) -> None:
    """Write the already verified set for one atomic reviewed commit."""

    mutable = {CURRENT_PATH, NEXT_PATH, REGISTRY_PATH}
    for path, contents in rendered.files.items():
        if path not in mutable and path.exists():
            raise Power2NextActivationError(
                "refusing to overwrite immutable activation output: "
                + path.relative_to(ROOT).as_posix()
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)
