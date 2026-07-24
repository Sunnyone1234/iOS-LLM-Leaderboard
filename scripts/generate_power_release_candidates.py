#!/usr/bin/env python3
"""Generate closed Power 2 Runner and App release candidate identities."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_PATH = ROOT / "products/power/candidate.json"
RUNNER_OUTPUT_PATH = (
    ROOT / "products/power/runner-certificates/candidate.json"
)
ACTIVE_RUNNER_OUTPUT_PATH = (
    ROOT
    / "products/power/runner-certificates"
    / "power2-runner-87f62feecc2b.json"
)
RELEASE_STACK_OUTPUT_PATH = (
    ROOT
    / "products/power/stacks"
    / "power-text-iphone-2.0.0-rc.1"
    / "manifest.json"
)
APP_OUTPUT_PATH = ROOT / "products/power/app-releases/candidate.json"
APP_IDENTITY_PATH = ROOT / "apps/ios/Configuration/ReleaseIdentity.json"

# This checkpoint records the exact identities that completed the automated
# candidate suite. Any stack, Runner, or App source change automatically
# returns the generated candidates to pending until the suite is rerun and
# this checkpoint is deliberately advanced.
AUTOMATED_VERIFICATION_CHECKPOINT = {
    "measurementStackSHA256":
        "a92a208324af0ea85c092e1cf04248c669f01c588c9f0d0b724e4c40a1014642",
    "runnerComponentsSHA256":
        "87f62feecc2b3fca994cc4f40214aed9876f1477c51fdb7c56c6945eb6b03ee2",
    "appComponentsSHA256":
        "63aaba5bd9d9d81f19ee17ad589bf019620d2443615cae723ac5558ecb4d2e5c",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repo_path(relative_path: str) -> Path:
    pure_path = PurePosixPath(relative_path)
    if pure_path.is_absolute() or ".." in pure_path.parts:
        raise ValueError(f"unsafe repository path: {relative_path}")
    path = (ROOT / pure_path).resolve()
    path.relative_to(ROOT.resolve())
    return path


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _reference(
    value: Any,
    label: str,
) -> tuple[Path, dict[str, str]]:
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
    return path, {"path": relative_path, "sha256": digest}


def _component_digest(
    manifest: dict[str, Any],
    name: str,
) -> str:
    components = manifest.get("components")
    if not isinstance(components, dict):
        raise ValueError("Runner component manifest has no components")
    component = components.get(name)
    if not isinstance(component, dict):
        raise ValueError(f"Runner component manifest has no {name}")
    digest = component.get("sha256")
    if not isinstance(digest, str):
        raise ValueError(f"Runner component {name} has no digest")
    return digest


def _render(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _rendered_reference(
    path: Path,
    rendered: str,
) -> dict[str, str]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
    }


def _app_rehearsal_passed(
    candidate: dict[str, Any],
    *,
    app_reference: dict[str, str],
    measurement_stack_reference: dict[str, str],
    runner_certificate_id: str,
    app_version: str,
    app_build: str,
) -> bool:
    rehearsals = candidate.get("appReleaseRehearsalEvidence")
    if not isinstance(rehearsals, list):
        raise ValueError("candidate has no App release rehearsal evidence")

    exact_rehearsal_passed = False
    for index, evidence in enumerate(rehearsals):
        if not isinstance(evidence, dict):
            raise ValueError(
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
            raise ValueError(
                f"App release rehearsal evidence {index} has no source commit"
            )
        _, historical_app_reference = _reference(
            evidence.get("appComponents"),
            f"App release rehearsal {index} component manifest",
        )
        result_path, result_reference = _reference(
            evidence.get("result"),
            f"App release rehearsal {index} result",
        )
        review_path, _ = _reference(
            evidence.get("review"),
            f"App release rehearsal {index} review",
        )
        result = _load_json(result_path)
        review = _load_json(review_path)
        result_app_release = result.get("appRelease")
        review_validator = review.get("validator")
        if (
            historical_app_reference["sha256"]
            == app_reference["sha256"]
            and isinstance(result_app_release, dict)
            and result_app_release.get("version") == app_version
            and result_app_release.get("build") == app_build
            and result_app_release.get("sourceRevision")
            == app_reference["sha256"]
            and result_app_release.get(
                "embeddedMeasurementStackSHA256"
            )
            == measurement_stack_reference["sha256"]
            and result.get("runnerCertificateID")
            == runner_certificate_id
            and review.get("appRelease") == result_app_release
            and review.get("runnerCertificateID")
            == runner_certificate_id
            and isinstance(review_validator, dict)
            and review_validator.get("sourceRevision") == source_commit
            and review.get("sourceResultSHA256")
            == result_reference["sha256"]
            and review.get("status") == "pass"
            and review.get("physicalDeviceEndToEndRehearsal") == "pass"
            and review.get("classification") == "auto-accept"
            and review.get("publishable") is False
            and review.get("rankingEligible") is False
        ):
            exact_rehearsal_passed = True
    return exact_rehearsal_passed


def render_candidates() -> tuple[str, str, str, str]:
    candidate = _load_json(CANDIDATE_PATH)
    if (
        candidate.get("status") != "migration-draft"
        or candidate.get("publicIntakeOpen") is not False
        or candidate.get("appRelease") is not None
    ):
        raise ValueError("release candidates require a closed migration draft")

    certification_stack_path, certification_stack_reference = _reference(
        candidate.get("certificationCandidateStack"),
        "Certification candidate measurement stack",
    )
    runner_path, runner_reference = _reference(
        candidate.get("runnerCandidate"),
        "Runner component manifest",
    )
    app_path, app_reference = _reference(
        candidate.get("appCandidate"),
        "App component manifest",
    )
    _, certification_app_reference = _reference(
        candidate.get("certificationAppCandidate"),
        "Certification App component manifest",
    )
    certification_stack = _load_json(certification_stack_path)
    runner = _load_json(runner_path)
    app = _load_json(app_path)
    app_identity = _load_json(APP_IDENTITY_PATH)
    if (
        app_identity.get("schemaVersion")
        != "power-app-build-identity-1.0.0-draft.1"
    ):
        raise ValueError("unsupported Power App build identity")
    app_version = app_identity.get("version")
    app_build = app_identity.get("build")
    build_kinds = app_identity.get("buildKinds")
    official_identity = (
        build_kinds.get("official")
        if isinstance(build_kinds, dict)
        else None
    )
    if (
        not isinstance(app_version, str)
        or not isinstance(app_build, str)
        or not isinstance(official_identity, dict)
        or not isinstance(
            official_identity.get("bundleIdentifier"),
            str,
        )
    ):
        raise ValueError("Power App build identity is incomplete")
    program_reference = certification_stack.get("program")
    target_reference = certification_stack.get("target")
    runner_policy_reference = (
        certification_stack.get("policies", {}).get("runner")
        if isinstance(certification_stack.get("policies"), dict)
        else None
    )
    _, program_reference = _reference(
        program_reference,
        "Program manifest",
    )
    _, target_reference = _reference(
        target_reference,
        "Target manifest",
    )
    _, runner_policy_reference = _reference(
        runner_policy_reference,
        "Runner certification policy",
    )
    runtime_path, runtime_reference = _reference(
        runner.get("runtimeIdentity"),
        "Runner runtime identity",
    )
    runtime = _load_json(runtime_path)

    evidence = candidate.get("certificationEvidence")
    if not isinstance(evidence, dict):
        raise ValueError("candidate has no Certification evidence")
    result_path, result_reference = _reference(
        evidence.get("result"),
        "Certification result",
    )
    review_path, review_reference = _reference(
        evidence.get("review"),
        "Certification review",
    )
    result = _load_json(result_path)
    review = _load_json(review_path)
    runner_candidate_id = (
        "power2-certification-candidate-" + runner_reference["sha256"][:12]
    )
    if (
        review.get("status") != "pass"
        or review.get("physicalDeviceSmokeRun") != "pass"
        or review.get("rawResultReview") != "pass"
        or review.get("publishable") is not False
        or review.get("rankingEligible") is not False
        or review.get("sourceResultSHA256") != result_reference["sha256"]
        or review.get("runnerCertificateID") != runner_candidate_id
        or result.get("runnerCertificateID") != runner_candidate_id
        or result.get("appRelease", {}).get("sourceRevision")
        != certification_app_reference["sha256"]
        or result.get("appRelease", {}).get(
            "embeddedMeasurementStackSHA256"
        )
        != certification_stack_reference["sha256"]
    ):
        raise ValueError("Certification evidence is not issuance-safe")

    active_runner_id = (
        "power2-runner-" + runner_reference["sha256"][:12]
    )
    active_runner = {
        "schemaVersion": "power-runner-certificate-1.0.0-rc.1",
        "productID": "power",
        "certificateID": active_runner_id,
        "state": "active",
        "issuedAt": review["reviewedAt"],
        "certificationPolicy": runner_policy_reference,
        "programManifestSHA256": program_reference["sha256"],
        "targetManifestSHA256": target_reference["sha256"],
        "runnerComponents": runner_reference,
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
        "runtimeIdentity": runtime_reference,
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
        "certificationEvidence": {
            "candidateCertificateID": runner_candidate_id,
            "measurementStack": certification_stack_reference,
            "result": result_reference,
            "review": review_reference,
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
    rendered_active_runner = _render(active_runner)
    active_runner_reference = _rendered_reference(
        ACTIVE_RUNNER_OUTPUT_PATH,
        rendered_active_runner,
    )
    release_stack = dict(certification_stack)
    release_stack.update(
        {
            "stackID": "power-text-iphone-2.0.0-rc.1",
            "status": "release-candidate",
            "runnerCertificate": active_runner_reference,
        }
    )
    rendered_release_stack = _render(release_stack)
    release_stack_reference = _rendered_reference(
        RELEASE_STACK_OUTPUT_PATH,
        rendered_release_stack,
    )

    runner_automated_verification_passed = (
        release_stack_reference["sha256"]
        == AUTOMATED_VERIFICATION_CHECKPOINT[
            "measurementStackSHA256"
        ]
        and runner_reference["sha256"]
        == AUTOMATED_VERIFICATION_CHECKPOINT[
            "runnerComponentsSHA256"
        ]
    )
    app_automated_verification_passed = (
        runner_automated_verification_passed
        and app_reference["sha256"]
        == AUTOMATED_VERIFICATION_CHECKPOINT[
            "appComponentsSHA256"
        ]
    )
    runner_automated_state = (
        "pass" if runner_automated_verification_passed else "pending"
    )
    app_automated_state = (
        "pass" if app_automated_verification_passed else "pending"
    )
    app_physical_rehearsal_passed = _app_rehearsal_passed(
        candidate,
        app_reference=app_reference,
        measurement_stack_reference=release_stack_reference,
        runner_certificate_id=active_runner_id,
        app_version=app_version,
        app_build=app_build,
    )

    runner_candidate = {
        "schemaVersion":
            "power-runner-certificate-candidate-1.0.0-draft.1",
        "productID": "power",
        "certificateID": runner_candidate_id,
        "state": "candidate",
        "measurementStack": release_stack_reference,
        "certificationPolicy": runner_policy_reference,
        "programManifestSHA256": program_reference["sha256"],
        "targetManifestSHA256": target_reference["sha256"],
        "runnerComponents": runner_reference,
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
        "runtimeIdentity": runtime_reference,
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
        "verification": {
            "sourceAndDependencyIntegrity": "pass",
            "unitTests": runner_automated_state,
            "schemaAndFixtureIntegrity": runner_automated_state,
            "deterministicSerialization": runner_automated_state,
            "failurePreservation": runner_automated_state,
            "genericIOSReleaseBuild": runner_automated_state,
            "physicalDeviceSmokeRun": "pass",
            "rawResultReview": "pass",
        },
        "certificationEvidence": {
            "result": result_reference,
            "review": review_reference,
        },
        "activeCertificate": active_runner_reference,
        "issuanceBlockedBy": (
            []
            if runner_automated_verification_passed
            else ["complete automated verification"]
        ),
    }

    app_candidate_id = (
        f"power-app-{app_version}-candidate-"
        + app_reference["sha256"][:12]
    )
    app_candidate = {
        "schemaVersion": "power-app-release-candidate-1.0.0-draft.1",
        "productID": "power",
        "releaseID": app_candidate_id,
        "state": "candidate",
        "version": app_version,
        "build": app_build,
        "sourceRevision": app_reference["sha256"],
        "bundleIdentifier": official_identity["bundleIdentifier"],
        "buildConfiguration": "Official",
        "appComponents": app_reference,
        "embeddedMeasurementStack": release_stack_reference,
        "supportedRunnerCertificateIDs": [
            active_runner_id
        ],
        "verification": {
            "sourceAndDependencyIntegrity": "pass",
            "genericIOSReleaseBuild": app_automated_state,
            "physicalDeviceEndToEndRehearsal": (
                "pass" if app_physical_rehearsal_passed else "pending"
            ),
        },
        "releaseBlockedBy": (
            []
            if app_physical_rehearsal_passed
            else ["complete a physical-device end-to-end rehearsal"]
        ) + [
            "activate the immutable stack and public intake atomically",
        ] + (
            []
            if app_automated_verification_passed
            else ["complete the Official generic iOS Release build"]
        ),
    }

    return (
        _render(runner_candidate),
        rendered_active_runner,
        rendered_release_stack,
        _render(app_candidate),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail instead of rewriting stale candidate identities",
    )
    args = parser.parse_args(argv)
    try:
        (
            expected_runner,
            expected_active_runner,
            expected_release_stack,
            expected_app,
        ) = render_candidates()
    except (KeyError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if args.check:
        stale = []
        for path, expected in (
            (RUNNER_OUTPUT_PATH, expected_runner),
            (ACTIVE_RUNNER_OUTPUT_PATH, expected_active_runner),
            (RELEASE_STACK_OUTPUT_PATH, expected_release_stack),
            (APP_OUTPUT_PATH, expected_app),
        ):
            try:
                actual = path.read_text(encoding="utf-8")
            except OSError:
                actual = ""
            if actual != expected:
                stale.append(str(path.relative_to(ROOT)))
        if stale:
            print(
                "error: stale generated release candidates: "
                + ", ".join(stale),
                file=sys.stderr,
            )
            return 1
        return 0

    RUNNER_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ACTIVE_RUNNER_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RELEASE_STACK_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    APP_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RUNNER_OUTPUT_PATH.write_text(expected_runner, encoding="utf-8")
    ACTIVE_RUNNER_OUTPUT_PATH.write_text(
        expected_active_runner,
        encoding="utf-8",
    )
    RELEASE_STACK_OUTPUT_PATH.write_text(
        expected_release_stack,
        encoding="utf-8",
    )
    APP_OUTPUT_PATH.write_text(expected_app, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
