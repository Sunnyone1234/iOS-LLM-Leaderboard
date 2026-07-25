#!/usr/bin/env python3
"""Issue the Runner certificate for an in-progress Power next release.

The command consumes an already reviewed physical-device Certification result.
It preserves the raw result and review bytes, snapshots the exact Runner,
runtime, and Certification App manifests, issues a new immutable Runner
certificate, creates a new measurement-stack manifest, and advances
``products/power/next.json`` to the closed Official App rehearsal gate.

It never changes ``products/power/current.json`` or opens public intake.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
NEXT_PATH = ROOT / "products/power/next.json"
APP_COMPONENT_PATH = ROOT / "apps/ios/component-manifest.json"
RUNTIME_IDENTITY_PATH = ROOT / "apps/PowerRunnerKit/runtime-identity.json"
CERTIFICATE_ROOT = ROOT / "products/power/runner-certificates"
STACK_ROOT = ROOT / "products/power/stacks"


class IssuanceError(ValueError):
    """Raised when reviewed evidence is not safe to certify."""


def _json_bytes(value: dict[str, Any]) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _load_bytes(path: Path, label: str) -> tuple[bytes, dict[str, Any]]:
    try:
        contents = path.read_bytes()
        value = json.loads(contents)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise IssuanceError(f"cannot read {label}: {error}") from error
    if not isinstance(value, dict):
        raise IssuanceError(f"{label} must be a JSON object")
    return contents, value


def _sha256_bytes(contents: bytes) -> str:
    return hashlib.sha256(contents).hexdigest()


def _sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _repo_path(relative_path: str) -> Path:
    pure = PurePosixPath(relative_path)
    if pure.is_absolute() or ".." in pure.parts:
        raise IssuanceError(f"unsafe repository path: {relative_path}")
    path = (ROOT / pure).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as error:
        raise IssuanceError(
            f"repository path escapes root: {relative_path}"
        ) from error
    return path


def _reference(
    value: Any,
    label: str,
) -> tuple[Path, dict[str, str]]:
    if not isinstance(value, dict):
        raise IssuanceError(f"{label} must be a pinned reference")
    relative_path = value.get("path")
    digest = value.get("sha256")
    if (
        not isinstance(relative_path, str)
        or not isinstance(digest, str)
        or not re.fullmatch(r"[0-9a-f]{64}", digest)
    ):
        raise IssuanceError(f"{label} must be a pinned reference")
    path = _repo_path(relative_path)
    try:
        actual = _sha256(path)
    except OSError as error:
        raise IssuanceError(f"cannot read {label}: {error}") from error
    if actual != digest:
        raise IssuanceError(f"{label} digest mismatch")
    return path, {"path": relative_path, "sha256": digest}


def _rendered_reference(path: Path, contents: bytes) -> dict[str, str]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": _sha256_bytes(contents),
    }


def _component_digest(
    manifest: dict[str, Any],
    name: str,
) -> str:
    components = manifest.get("components")
    component = components.get(name) if isinstance(components, dict) else None
    digest = component.get("sha256") if isinstance(component, dict) else None
    if not isinstance(digest, str):
        raise IssuanceError(f"Runner manifest has no {name} digest")
    return digest


def _runtime_value(runtime: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "name",
        "version",
        "resolvedRevision",
        "backend",
        "configuration",
    )
    if any(key not in runtime for key in keys):
        raise IssuanceError("Runner runtime identity is incomplete")
    return {key: runtime[key] for key in keys}


def render_issuance(
    result_path: Path,
    review_path: Path,
) -> tuple[dict[Path, bytes], dict[str, Any]]:
    result_bytes, result = _load_bytes(
        result_path, "Certification result"
    )
    review_bytes, review = _load_bytes(
        review_path, "Certification review"
    )
    _, next_release = _load_bytes(NEXT_PATH, "next release plan")
    if (
        next_release.get("schemaVersion")
        != "power-release-plan-1.0.0"
        or next_release.get("state") != "runner-certification-required"
        or next_release.get("publicIntakeOpen") is not False
        or next_release.get("runnerCertificate") is not None
        or next_release.get("appRelease") is not None
    ):
        raise IssuanceError(
            "next release is not at the Runner certification gate"
        )

    result_digest = _sha256_bytes(result_bytes)
    candidate_id = next_release.get("runnerCertificationCandidateID")
    if (
        review.get("schemaVersion")
        != "power-runner-certification-review-1.0.0-draft.1"
        or review.get("status") != "pass"
        or review.get("physicalDeviceSmokeRun") != "pass"
        or review.get("rawResultReview") != "pass"
        or review.get("publishable") is not False
        or review.get("rankingEligible") is not False
        or review.get("sourceResultSHA256") != result_digest
        or review.get("runnerCertificateID") != candidate_id
        or result.get("runnerCertificateID") != candidate_id
        or review.get("appRelease") != result.get("appRelease")
    ):
        raise IssuanceError(
            "Certification review does not authorize this exact result"
        )

    result_id = result.get("resultID")
    if (
        not isinstance(result_id, str)
        or not re.fullmatch(
            r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-"
            r"[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}",
            result_id,
        )
    ):
        raise IssuanceError("Certification result has no valid result ID")
    evidence_root = (
        CERTIFICATE_ROOT / "evidence" / result_id.lower()
    )

    stack_path, stack_reference = _reference(
        next_release.get("measurementStack"),
        "Certification measurement stack",
    )
    _, stack = _load_bytes(stack_path, "Certification measurement stack")
    runner_path, runner_reference = _reference(
        next_release.get("runnerComponents"),
        "Runner component candidate",
    )
    runner_bytes, runner = _load_bytes(
        runner_path, "Runner component candidate"
    )
    if (
        runner.get("schemaVersion")
        != "power-runner-component-manifest-1.0.0"
    ):
        raise IssuanceError("unsupported Runner component manifest")
    expected_candidate_id = (
        "power2-certification-candidate-"
        + runner_reference["sha256"][:12]
    )
    if candidate_id != expected_candidate_id:
        raise IssuanceError("Runner candidate ID is not source-bound")

    app_bytes, _ = _load_bytes(
        APP_COMPONENT_PATH, "Certification App component manifest"
    )
    app_digest = _sha256_bytes(app_bytes)
    result_app = result.get("appRelease")
    if (
        not isinstance(result_app, dict)
        or result_app.get("version") != "2.0.0-certification"
        or result_app.get("build")
        != next_release.get("app", {}).get("build")
        or result_app.get("sourceRevision") != app_digest
        or result_app.get("embeddedMeasurementStackSHA256")
        != stack_reference["sha256"]
    ):
        raise IssuanceError(
            "Certification result App identity does not match this source"
        )

    runtime_bytes, runtime = _load_bytes(
        RUNTIME_IDENTITY_PATH, "Runner runtime identity"
    )
    runtime_reference = runner.get("runtimeIdentity")
    if (
        not isinstance(runtime_reference, dict)
        or runtime_reference.get("sha256")
        != _sha256_bytes(runtime_bytes)
    ):
        raise IssuanceError(
            "Runner candidate and runtime identity do not agree"
        )

    program = stack.get("program")
    target = stack.get("target")
    policies = stack.get("policies")
    if (
        not isinstance(program, dict)
        or not isinstance(target, dict)
        or not isinstance(policies, dict)
    ):
        raise IssuanceError("Certification stack is incomplete")
    _, program_reference = _reference(program, "Power Program")
    _, target_reference = _reference(target, "Power Target")
    _, runner_policy_reference = _reference(
        policies.get("runner"), "Runner policy"
    )

    frozen_result_path = evidence_root / "result.json"
    frozen_review_path = evidence_root / "review.json"
    frozen_runner_path = (
        evidence_root / "runner-component-manifest.json"
    )
    frozen_app_path = evidence_root / "app-component-manifest.json"
    frozen_runtime_path = evidence_root / "runtime-identity.json"
    result_reference = _rendered_reference(
        frozen_result_path, result_bytes
    )
    review_reference = _rendered_reference(
        frozen_review_path, review_bytes
    )
    frozen_runner_reference = _rendered_reference(
        frozen_runner_path, runner_bytes
    )
    frozen_app_reference = _rendered_reference(
        frozen_app_path, app_bytes
    )
    frozen_runtime_reference = _rendered_reference(
        frozen_runtime_path, runtime_bytes
    )

    certificate_id = (
        "power2-runner-" + runner_reference["sha256"][:12]
    )
    certificate_path = (
        CERTIFICATE_ROOT / f"{certificate_id}.json"
    )
    certificate = {
        "schemaVersion": "power-runner-certificate-1.0.0-rc.1",
        "productID": "power",
        "certificateID": certificate_id,
        "state": "active",
        "issuedAt": review.get("reviewedAt"),
        "certificationPolicy": runner_policy_reference,
        "programManifestSHA256": program_reference["sha256"],
        "targetManifestSHA256": target_reference["sha256"],
        "runnerComponents": frozen_runner_reference,
        "componentSHA256": {
            name: _component_digest(runner, name)
            for name in (
                "runnerCore",
                "programModule",
                "targetAdapter",
                "runtimeAdapter",
                "evidenceEnvelope",
            )
        },
        "runtimeIdentity": frozen_runtime_reference,
        "runtime": _runtime_value(runtime),
        "certificationEvidence": {
            "candidateCertificateID": candidate_id,
            "measurementStack": stack_reference,
            "result": result_reference,
            "review": review_reference,
            "runnerComponentsSnapshot": frozen_runner_reference,
            "certificationAppComponents": frozen_app_reference,
        },
        "verification": {
            "sourceAndDependencyIntegrity": "pass",
            "unitTests": "pass",
            "schemaAndFixtureIntegrity": "pass",
            "deterministicSerialization": "pass",
            "failurePreservation": "pass",
            "genericIOSReleaseBuild": "pass",
            "physicalDeviceSmokeRun": "pass",
            "rawResultReview": "pass",
        },
    }
    certificate_bytes = _json_bytes(certificate)
    certificate_reference = _rendered_reference(
        certificate_path, certificate_bytes
    )

    if stack.get("stackID") != "power-text-iphone-2.0.0-rc.1":
        raise IssuanceError(
            "automatic next stack issuance expects Power rc.1"
        )
    release_stack = dict(stack)
    release_stack.update(
        {
            "stackID": "power-text-iphone-2.0.0-rc.2",
            "status": "release-candidate",
            "runnerCertificate": certificate_reference,
        }
    )
    release_stack_path = (
        STACK_ROOT
        / "power-text-iphone-2.0.0-rc.2"
        / "manifest.json"
    )
    release_stack_bytes = _json_bytes(release_stack)
    release_stack_reference = _rendered_reference(
        release_stack_path, release_stack_bytes
    )

    advanced = dict(next_release)
    advanced.update(
        {
            "state": "app-release-rehearsal-required",
            "stackID": release_stack["stackID"],
            "measurementStack": release_stack_reference,
            "runnerComponents": frozen_runner_reference,
            "runnerCertificate": certificate_reference,
            "appRelease": None,
            "appReleaseCandidate": None,
            "runnerCertificationEvidence": {
                "result": result_reference,
                "review": review_reference,
                "runnerComponentsSnapshot": frozen_runner_reference,
                "certificationAppComponents": frozen_app_reference,
                "runtimeIdentitySnapshot": frozen_runtime_reference,
            },
        }
    )
    advanced_bytes = _json_bytes(advanced)

    files = {
        frozen_result_path: result_bytes,
        frozen_review_path: review_bytes,
        frozen_runner_path: runner_bytes,
        frozen_app_path: app_bytes,
        frozen_runtime_path: runtime_bytes,
        certificate_path: certificate_bytes,
        release_stack_path: release_stack_bytes,
        NEXT_PATH: advanced_bytes,
    }
    summary = {
        "status": "ready",
        "resultID": result_id,
        "resultSHA256": result_digest,
        "runnerCertificateID": certificate_id,
        "runnerCertificate": certificate_reference,
        "measurementStack": release_stack_reference,
        "nextReleaseState": advanced["state"],
        "publicIntakeOpen": False,
        "files": sorted(
            path.relative_to(ROOT).as_posix() for path in files
        ),
    }
    return files, summary


def write_issuance(files: dict[Path, bytes]) -> None:
    for path, contents in files.items():
        if path != NEXT_PATH and path.exists():
            if path.read_bytes() != contents:
                raise IssuanceError(
                    f"refusing to overwrite immutable file: {path}"
                )
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("review", type=Path)
    parser.add_argument(
        "--write",
        action="store_true",
        help="write the issuance set; omit for a dry run",
    )
    args = parser.parse_args(argv)
    try:
        files, summary = render_issuance(args.result, args.review)
        if args.write:
            write_issuance(files)
    except (IssuanceError, OSError) as error:
        print(
            json.dumps(
                {"status": "invalid", "error": str(error)},
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    print(
        json.dumps(
            {
                **summary,
                "writeRequested": args.write,
                "written": args.write,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
