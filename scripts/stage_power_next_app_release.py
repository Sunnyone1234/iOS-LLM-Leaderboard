#!/usr/bin/env python3
"""Stage the immutable Official App candidate for the next Power release.

The command snapshots the exact generated App component manifest, binds it to
the issued Runner certificate and release-candidate measurement stack, and
advances only ``products/power/next.json``. It never opens public intake,
publishes an App release, or changes ``products/power/current.json``.

The generic iOS Release build is performed outside this command. The caller
must explicitly attest that it passed; the remaining physical-device App
rehearsal stays pending until separately reviewed.
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
APP_IDENTITY_PATH = ROOT / "apps/ios/Configuration/ReleaseIdentity.json"
APP_RELEASE_ROOT = ROOT / "products/power/app-releases"


class StagingError(ValueError):
    """Raised when the App source is not safe to stage."""


def _json_bytes(value: dict[str, Any]) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _load_bytes(path: Path, label: str) -> tuple[bytes, dict[str, Any]]:
    try:
        contents = path.read_bytes()
        value = json.loads(contents)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise StagingError(f"cannot read {label}: {error}") from error
    if not isinstance(value, dict):
        raise StagingError(f"{label} must be a JSON object")
    return contents, value


def _sha256_bytes(contents: bytes) -> str:
    return hashlib.sha256(contents).hexdigest()


def _sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _repo_path(relative_path: str) -> Path:
    pure = PurePosixPath(relative_path)
    if pure.is_absolute() or ".." in pure.parts:
        raise StagingError(f"unsafe repository path: {relative_path}")
    path = (ROOT / pure).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as error:
        raise StagingError(
            f"repository path escapes root: {relative_path}"
        ) from error
    return path


def _reference(
    value: Any,
    label: str,
) -> tuple[Path, dict[str, str]]:
    if not isinstance(value, dict):
        raise StagingError(f"{label} must be a pinned reference")
    relative_path = value.get("path")
    digest = value.get("sha256")
    if (
        not isinstance(relative_path, str)
        or not isinstance(digest, str)
        or not re.fullmatch(r"[0-9a-f]{64}", digest)
    ):
        raise StagingError(f"{label} must be a pinned reference")
    path = _repo_path(relative_path)
    try:
        actual = _sha256(path)
    except OSError as error:
        raise StagingError(f"cannot read {label}: {error}") from error
    if actual != digest:
        raise StagingError(f"{label} digest mismatch")
    return path, {"path": relative_path, "sha256": digest}


def _rendered_reference(path: Path, contents: bytes) -> dict[str, str]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": _sha256_bytes(contents),
    }


def _verify_app_manifest(
    manifest: dict[str, Any],
    identity: dict[str, Any],
) -> None:
    if (
        manifest.get("schemaVersion")
        != "power-app-component-manifest-1.0.0"
        or manifest.get("productID") != "power"
    ):
        raise StagingError("unsupported App component manifest")
    _, release_identity = _reference(
        manifest.get("releaseIdentity"),
        "App release identity",
    )
    if release_identity["path"] != APP_IDENTITY_PATH.relative_to(ROOT).as_posix():
        raise StagingError("App manifest uses an unexpected release identity")
    components = manifest.get("components")
    if not isinstance(components, dict) or not components:
        raise StagingError("App component manifest has no components")
    for name, component in components.items():
        if not isinstance(component, dict):
            raise StagingError(f"App component {name} is invalid")
        files = component.get("files")
        if not isinstance(files, list) or not files:
            raise StagingError(f"App component {name} has no files")
        canonical = json.dumps(
            files,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        if component.get("sha256") != _sha256_bytes(canonical):
            raise StagingError(
                f"App component {name} aggregate digest mismatch"
            )
        for index, reference in enumerate(files):
            _reference(reference, f"App component {name} file {index}")
    if (
        identity.get("schemaVersion")
        != "power-app-build-identity-1.0.0-draft.1"
    ):
        raise StagingError("unsupported App build identity")


def _superseded_rehearsal_files(
    *,
    existing_candidate_reference: dict[str, str],
    replacement_candidate_reference: dict[str, str],
    result_path: Path,
    review_path: Path,
) -> tuple[dict[Path, bytes], dict[str, Any]]:
    existing_candidate_path, pinned_existing_reference = _reference(
        existing_candidate_reference,
        "existing App release candidate",
    )
    _, existing_candidate = _load_bytes(
        existing_candidate_path,
        "existing App release candidate",
    )
    _, app_components_reference = _reference(
        existing_candidate.get("appComponents"),
        "existing App candidate components",
    )
    result_bytes, result = _load_bytes(
        result_path,
        "superseded App rehearsal result",
    )
    review_bytes, review = _load_bytes(
        review_path,
        "superseded App rehearsal review",
    )
    result_id = result.get("resultID")
    app_release = result.get("appRelease")
    supported_certificates = existing_candidate.get(
        "supportedRunnerCertificateIDs"
    )
    attempts = (
        result.get("payload", {}).get("attempts")
        if isinstance(result.get("payload"), dict)
        else None
    )
    expected_app_release = {
        "version": existing_candidate.get("version"),
        "build": existing_candidate.get("build"),
        "sourceRevision": existing_candidate.get("sourceRevision"),
        "embeddedMeasurementStackSHA256":
            existing_candidate.get(
                "embeddedMeasurementStack", {}
            ).get("sha256"),
    }
    if (
        existing_candidate.get("schemaVersion")
        != "power-app-release-candidate-1.0.0-draft.1"
        or existing_candidate.get("state") != "candidate"
        or not isinstance(result_id, str)
        or not re.fullmatch(
            r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-"
            r"[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}",
            result_id,
        )
        or app_release != expected_app_release
        or not isinstance(supported_certificates, list)
        or result.get("runnerCertificateID")
        not in supported_certificates
        or not isinstance(attempts, list)
        or not attempts
    ):
        raise StagingError(
            "superseded rehearsal result does not match the existing "
            "App candidate"
        )
    if (
        review.get("schemaVersion")
        != "power-app-release-review-1.0.0-draft.1"
        or review.get("status") != "pass"
        or review.get("classification") != "auto-accept"
        or review.get("physicalDeviceEndToEndRehearsal") != "pass"
        or review.get("publishable") is not False
        or review.get("rankingEligible") is not False
        or review.get("sourceResultSHA256")
        != _sha256_bytes(result_bytes)
        or review.get("appRelease") != app_release
        or review.get("runnerCertificateID")
        != result.get("runnerCertificateID")
    ):
        raise StagingError(
            "superseded rehearsal review is not a passing, "
            "non-publishable review of the supplied result"
        )

    evidence_root = APP_RELEASE_ROOT / "evidence" / result_id.lower()
    frozen_result_path = evidence_root / "result.json"
    frozen_review_path = evidence_root / "review.json"
    record_path = evidence_root / "record.json"
    result_reference = _rendered_reference(
        frozen_result_path,
        result_bytes,
    )
    review_reference = _rendered_reference(
        frozen_review_path,
        review_bytes,
    )
    record = {
        "schemaVersion":
            "power-app-release-rehearsal-record-1.0.0-draft.1",
        "productID": "power",
        "state": "superseded",
        "reasonCode":
            "candidate-lifecycle-authority-compiled-into-source",
        "reason": (
            "The rehearsal passed, but candidate lifecycle authority was "
            "removed from the hashed App source before public activation "
            "so the same replacement source can become current without "
            "recompilation."
        ),
        "publishable": False,
        "rankingEligible": False,
        "appReleaseCandidate": pinned_existing_reference,
        "appComponents": app_components_reference,
        "result": result_reference,
        "review": review_reference,
        "supersededBy": replacement_candidate_reference,
    }
    record_bytes = _json_bytes(record)
    files = {
        frozen_result_path: result_bytes,
        frozen_review_path: review_bytes,
        record_path: record_bytes,
    }
    return files, _rendered_reference(record_path, record_bytes)


def render_staging(
    *,
    supersede_existing: bool = False,
    superseded_result_path: Path | None = None,
    superseded_review_path: Path | None = None,
) -> tuple[dict[Path, bytes], dict[str, Any]]:
    _, next_release = _load_bytes(NEXT_PATH, "next release plan")
    if (
        next_release.get("schemaVersion")
        != "power-release-plan-1.0.0"
        or next_release.get("state")
        != "app-release-rehearsal-required"
        or next_release.get("publicIntakeOpen") is not False
        or next_release.get("appRelease") is not None
    ):
        raise StagingError(
            "next release is not at the Official App rehearsal gate"
        )
    existing_candidate_reference = next_release.get(
        "appReleaseCandidate"
    )
    if existing_candidate_reference is not None and not supersede_existing:
        raise StagingError("next release already has an App candidate")
    if supersede_existing and (
        existing_candidate_reference is None
        or superseded_result_path is None
        or superseded_review_path is None
    ):
        raise StagingError(
            "replacing an App candidate requires the existing candidate, "
            "its exact physical result, and its passing review"
        )

    stack_path, stack_reference = _reference(
        next_release.get("measurementStack"),
        "next measurement stack",
    )
    _, stack = _load_bytes(stack_path, "next measurement stack")
    certificate_path, certificate_reference = _reference(
        next_release.get("runnerCertificate"),
        "next Runner certificate",
    )
    _, certificate = _load_bytes(
        certificate_path, "next Runner certificate"
    )
    _, runner_reference = _reference(
        next_release.get("runnerComponents"),
        "next Runner components",
    )
    certificate_id = certificate.get("certificateID")
    if (
        stack.get("stackID") != next_release.get("stackID")
        or stack.get("status") != "release-candidate"
        or stack.get("runnerCertificate") != certificate_reference
        or certificate.get("state") != "active"
        or certificate.get("runnerComponents") != runner_reference
        or not isinstance(certificate_id, str)
        or not certificate_id
    ):
        raise StagingError(
            "next stack and issued Runner certificate are inconsistent"
        )

    app_bytes, app_manifest = _load_bytes(
        APP_COMPONENT_PATH, "App component manifest"
    )
    _, identity = _load_bytes(APP_IDENTITY_PATH, "App build identity")
    _verify_app_manifest(app_manifest, identity)
    app_digest = _sha256_bytes(app_bytes)

    version = identity.get("version")
    build = identity.get("build")
    build_kinds = identity.get("buildKinds")
    official = (
        build_kinds.get("official")
        if isinstance(build_kinds, dict)
        else None
    )
    bundle_identifier = (
        official.get("bundleIdentifier")
        if isinstance(official, dict)
        else None
    )
    if (
        not isinstance(version, str)
        or not isinstance(build, str)
        or not isinstance(bundle_identifier, str)
        or next_release.get("app")
        != {"version": version, "build": build}
    ):
        raise StagingError("next release App identity is inconsistent")

    release_id = (
        f"power-app-{version}-candidate-{app_digest[:12]}"
    )
    evidence_root = (
        APP_RELEASE_ROOT / "evidence" / f"candidate-{app_digest[:12]}"
    )
    frozen_manifest_path = (
        evidence_root / "app-component-manifest.json"
    )
    frozen_manifest_reference = _rendered_reference(
        frozen_manifest_path, app_bytes
    )
    candidate_path = (
        APP_RELEASE_ROOT
        / "candidates"
        / f"power-app-{version}-build.{build}-{app_digest[:12]}.json"
    )
    candidate = {
        "schemaVersion": "power-app-release-candidate-1.0.0-draft.1",
        "productID": "power",
        "releaseID": release_id,
        "state": "candidate",
        "version": version,
        "build": build,
        "sourceRevision": app_digest,
        "bundleIdentifier": bundle_identifier,
        "buildConfiguration": "Official",
        "appComponents": frozen_manifest_reference,
        "embeddedMeasurementStack": stack_reference,
        "supportedRunnerCertificateIDs": [certificate_id],
        "verification": {
            "sourceAndDependencyIntegrity": "pass",
            "genericIOSReleaseBuild": "pass",
            "physicalDeviceEndToEndRehearsal": "pending",
        },
        "releaseBlockedBy": [
            "complete and review the exact physical-device Official App rehearsal",
            "publish the immutable App release and current pointer atomically",
        ],
    }
    candidate_bytes = _json_bytes(candidate)
    candidate_reference = _rendered_reference(
        candidate_path, candidate_bytes
    )
    if (
        existing_candidate_reference is not None
        and candidate_reference == existing_candidate_reference
    ):
        raise StagingError(
            "replacement App candidate must have a new source identity"
        )

    advanced = dict(next_release)
    advanced["appReleaseCandidate"] = candidate_reference
    files = {
        frozen_manifest_path: app_bytes,
        candidate_path: candidate_bytes,
    }
    superseded_record_reference = None
    if existing_candidate_reference is not None:
        superseded_files, superseded_record_reference = (
            _superseded_rehearsal_files(
                existing_candidate_reference=
                    existing_candidate_reference,
                replacement_candidate_reference=candidate_reference,
                result_path=superseded_result_path,
                review_path=superseded_review_path,
            )
        )
        files.update(superseded_files)
        advanced["supersededAppReleaseRehearsal"] = (
            superseded_record_reference
        )
    advanced_bytes = _json_bytes(advanced)
    files[NEXT_PATH] = advanced_bytes
    summary = {
        "status": "ready",
        "releaseID": release_id,
        "sourceRevision": app_digest,
        "runnerCertificateID": certificate_id,
        "measurementStack": stack_reference,
        "appReleaseCandidate": candidate_reference,
        "physicalDeviceEndToEndRehearsal": "pending",
        "publicIntakeOpen": False,
        "supersededAppReleaseRehearsal":
            superseded_record_reference,
        "files": sorted(
            path.relative_to(ROOT).as_posix() for path in files
        ),
    }
    return files, summary


def write_staging(files: dict[Path, bytes]) -> None:
    for path, contents in files.items():
        if path != NEXT_PATH and path.exists():
            if path.read_bytes() != contents:
                raise StagingError(
                    f"refusing to overwrite immutable file: {path}"
                )
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--generic-ios-release-build-passed",
        action="store_true",
        help=(
            "confirm the exact source completed a generic iOS Official build"
        ),
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="write the candidate set; omit for a dry run",
    )
    parser.add_argument(
        "--supersede-existing",
        action="store_true",
        help=(
            "replace the staged candidate while retaining its reviewed "
            "physical rehearsal as immutable non-publishable evidence"
        ),
    )
    parser.add_argument(
        "--superseded-result",
        type=Path,
        help="exact raw physical result for the candidate being replaced",
    )
    parser.add_argument(
        "--superseded-review",
        type=Path,
        help="passing review for --superseded-result",
    )
    args = parser.parse_args(argv)
    if not args.generic_ios_release_build_passed:
        print(
            json.dumps(
                {
                    "status": "invalid",
                    "error": (
                        "--generic-ios-release-build-passed is required"
                    ),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    try:
        files, summary = render_staging(
            supersede_existing=args.supersede_existing,
            superseded_result_path=args.superseded_result,
            superseded_review_path=args.superseded_review,
        )
        if args.write:
            write_staging(files)
    except (OSError, StagingError) as error:
        print(
            json.dumps(
                {"status": "invalid", "error": str(error)},
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    summary["written"] = args.write
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
