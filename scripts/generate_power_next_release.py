#!/usr/bin/env python3
"""Generate the fail-closed plan for the next Power release.

The active pointer is never rewritten by this command.  The plan binds current
protocol assets to the exact next Runner source manifest and App version.  It
stops at the first physical-device gate: a candidate Runner certificate must
be issued from reviewed Certification evidence before an App release can be
rehearsed or activated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CURRENT_PATH = ROOT / "products/power/current.json"
RUNNER_MANIFEST_PATH = (
    ROOT / "apps/PowerRunnerKit/candidate-component-manifest.json"
)
APP_IDENTITY_PATH = ROOT / "apps/ios/Configuration/ReleaseIdentity.json"
APP_COMPONENT_PATH = ROOT / "apps/ios/component-manifest.json"
OUTPUT_PATH = ROOT / "products/power/next.json"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reference(path: Path) -> dict[str, str]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": _sha256(path),
    }


def _verify_reference(value: Any, label: str) -> Path:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a pinned reference")
    relative_path = value.get("path")
    digest = value.get("sha256")
    if (
        not isinstance(relative_path, str)
        or not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise ValueError(f"{label} must be a pinned reference")
    path = (ROOT / relative_path).resolve()
    path.relative_to(ROOT.resolve())
    if _sha256(path) != digest:
        raise ValueError(f"{label} digest mismatch")
    return path


def validate_advanced(value: dict[str, Any]) -> None:
    """Validate a progressed plan without resetting its reviewed gates."""

    if (
        value.get("schemaVersion") != "power-release-plan-1.0.0"
        or value.get("productID") != "power"
        or value.get("state") != "app-release-rehearsal-required"
        or value.get("publicIntakeOpen") is not False
        or value.get("appRelease") is not None
    ):
        raise ValueError("unsupported advanced next-release plan")
    app_identity = _load(APP_IDENTITY_PATH)
    if value.get("app") != {
        "version": app_identity.get("version"),
        "build": app_identity.get("build"),
    }:
        raise ValueError("advanced next-release App identity is stale")
    base_path = _verify_reference(
        value.get("baseRelease"), "advanced base release"
    )
    if base_path != CURRENT_PATH.resolve():
        raise ValueError("advanced plan is not based on current Power")
    stack_path = _verify_reference(
        value.get("measurementStack"), "advanced measurement stack"
    )
    runner_path = _verify_reference(
        value.get("runnerComponents"), "advanced Runner components"
    )
    certificate_path = _verify_reference(
        value.get("runnerCertificate"), "advanced Runner certificate"
    )
    stack = _load(stack_path)
    runner = _load(runner_path)
    certificate = _load(certificate_path)
    if (
        stack.get("stackID") != value.get("stackID")
        or stack.get("status") != "release-candidate"
        or stack.get("runnerCertificate") != value.get("runnerCertificate")
    ):
        raise ValueError("advanced measurement stack is inconsistent")
    if (
        runner.get("schemaVersion")
        != "power-runner-component-manifest-1.0.0"
        or certificate.get("state") != "active"
        or certificate.get("runnerComponents")
        != value.get("runnerComponents")
    ):
        raise ValueError("advanced Runner certificate is inconsistent")
    expected_candidate_id = (
        "power2-certification-candidate-"
        + value["runnerComponents"]["sha256"][:12]
    )
    if value.get("runnerCertificationCandidateID") != expected_candidate_id:
        raise ValueError("advanced Runner candidate ID is not source-bound")
    evidence = value.get("runnerCertificationEvidence")
    if not isinstance(evidence, dict):
        raise ValueError("advanced plan has no Runner certification evidence")
    for key in (
        "result",
        "review",
        "runnerComponentsSnapshot",
        "certificationAppComponents",
        "runtimeIdentitySnapshot",
    ):
        _verify_reference(evidence.get(key), f"advanced evidence {key}")
    app_candidate = value.get("appReleaseCandidate")
    if app_candidate is not None:
        app_candidate_path = _verify_reference(
            app_candidate, "advanced App release candidate"
        )
        app_release_candidate = _load(app_candidate_path)
        app_components_path = _verify_reference(
            app_release_candidate.get("appComponents"),
            "advanced App components",
        )
        certificate_id = certificate.get("certificateID")
        app_digest = _sha256(APP_COMPONENT_PATH)
        official = app_identity.get("buildKinds", {}).get("official", {})
        if (
            app_components_path.read_bytes()
            != APP_COMPONENT_PATH.read_bytes()
            or app_release_candidate.get("schemaVersion")
            != "power-app-release-candidate-1.0.0-draft.1"
            or app_release_candidate.get("state") != "candidate"
            or app_release_candidate.get("version")
            != app_identity.get("version")
            or app_release_candidate.get("build")
            != app_identity.get("build")
            or app_release_candidate.get("sourceRevision") != app_digest
            or app_release_candidate.get("appComponents", {}).get("sha256")
            != app_digest
            or app_release_candidate.get("bundleIdentifier")
            != official.get("bundleIdentifier")
            or app_release_candidate.get("buildConfiguration")
            != "Official"
            or app_release_candidate.get("embeddedMeasurementStack")
            != value.get("measurementStack")
            or app_release_candidate.get(
                "supportedRunnerCertificateIDs"
            )
            != [certificate_id]
            or app_release_candidate.get("verification")
            != {
                "sourceAndDependencyIntegrity": "pass",
                "genericIOSReleaseBuild": "pass",
                "physicalDeviceEndToEndRehearsal": "pending",
            }
        ):
            raise ValueError(
                "advanced App release candidate is inconsistent"
            )


def validate_activated(value: dict[str, Any]) -> None:
    """Validate a completed plan before a later cycle replaces it."""

    current = _load(CURRENT_PATH)
    if (
        value.get("schemaVersion") != "power-release-plan-1.0.0"
        or value.get("productID") != "power"
        or value.get("state") != "activated"
        or value.get("publicIntakeOpen") is not False
        or not isinstance(value.get("activatedAt"), str)
        or current.get("schemaVersion")
        != "power-stack-pointer-1.0.0"
        or current.get("status") != "active"
        or current.get("publicIntakeOpen") is not True
        or current.get("activatedAt") != value.get("activatedAt")
    ):
        raise ValueError("unsupported activated next-release plan")
    _verify_reference(value.get("baseRelease"), "completed base release")
    for key in (
        "measurementStack",
        "runnerComponents",
        "runnerCertificate",
        "appReleaseCandidate",
        "appRelease",
    ):
        _verify_reference(value.get(key), f"completed {key}")
    activation = value.get("activationEvidence")
    if not isinstance(activation, dict):
        raise ValueError("completed plan has no activation evidence")
    for key in ("result", "review"):
        _verify_reference(
            activation.get(key),
            f"completed activation evidence {key}",
        )
    if (
        value.get("stackID") != current.get("stackID")
        or value.get("measurementStack")
        != current.get("measurementStack")
        or value.get("runnerComponents")
        != current.get("runnerComponents")
        or value.get("runnerCertificate")
        != current.get("runnerCertificate")
        or value.get("appRelease") != current.get("appRelease")
        or activation != current.get("activationEvidence")
    ):
        raise ValueError(
            "completed plan does not match the active Power pointer"
        )


def render() -> str:
    current = _load(CURRENT_PATH)
    runner = _load(RUNNER_MANIFEST_PATH)
    app_identity = _load(APP_IDENTITY_PATH)
    if (
        current.get("schemaVersion") != "power-stack-pointer-1.0.0"
        or current.get("status") != "active"
        or current.get("publicIntakeOpen") is not True
    ):
        raise ValueError("current Power pointer is not active")
    if (
        runner.get("schemaVersion")
        != "power-runner-component-manifest-1.0.0"
    ):
        raise ValueError("unsupported next Runner component manifest")
    version = app_identity.get("version")
    build = app_identity.get("build")
    if not isinstance(version, str) or not isinstance(build, str):
        raise ValueError("App release identity is incomplete")

    runner_reference = _reference(RUNNER_MANIFEST_PATH)
    value = {
        "schemaVersion": "power-release-plan-1.0.0",
        "productID": "power",
        "state": "runner-certification-required",
        "publicIntakeOpen": False,
        "baseRelease": _reference(CURRENT_PATH),
        "stackID": current["stackID"],
        "measurementStack": current["measurementStack"],
        "runnerComponents": runner_reference,
        "runnerCertificate": None,
        "runnerCertificationCandidateID":
            "power2-certification-candidate-"
            + runner_reference["sha256"][:12],
        "app": {
            "version": version,
            "build": build,
        },
        "appRelease": None,
        "requiredGates": [
            "automated source, schema, package, and generic build checks",
            "reviewed physical-device Runner Certification evidence",
            "reviewed physical-device Official App release rehearsal",
            "atomic immutable release and current-pointer update",
        ],
    }
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail instead of rewriting a stale next-release plan",
    )
    args = parser.parse_args(argv)
    try:
        expected = render()
    except (KeyError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if args.check:
        try:
            actual = OUTPUT_PATH.read_text(encoding="utf-8")
            actual_value = json.loads(actual)
        except OSError:
            actual = ""
            actual_value = None
        except json.JSONDecodeError:
            actual_value = None
        if (
            isinstance(actual_value, dict)
            and actual_value.get("state")
            == "app-release-rehearsal-required"
        ):
            try:
                validate_advanced(actual_value)
            except (KeyError, OSError, ValueError, json.JSONDecodeError) as error:
                print(f"error: {error}", file=sys.stderr)
                return 1
            return 0
        if (
            isinstance(actual_value, dict)
            and actual_value.get("state") == "activated"
        ):
            try:
                validate_activated(actual_value)
            except (
                KeyError,
                OSError,
                ValueError,
                json.JSONDecodeError,
            ) as error:
                print(f"error: {error}", file=sys.stderr)
                return 1
            return 0
        if actual != expected:
            print(
                "error: products/power/next.json is stale",
                file=sys.stderr,
            )
            return 1
        return 0

    if OUTPUT_PATH.exists():
        try:
            existing = _load(OUTPUT_PATH)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            print(f"error: {error}", file=sys.stderr)
            return 2
        if existing.get("state") == "app-release-rehearsal-required":
            print(
                "error: next release has passed Runner certification; "
                "refusing to reset reviewed progress",
                file=sys.stderr,
            )
            return 1
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(expected, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
