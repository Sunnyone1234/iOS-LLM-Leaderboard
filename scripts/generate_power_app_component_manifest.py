#!/usr/bin/env python3
"""Generate the lifecycle-neutral digest manifest for Power App modules."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "apps" / "ios"
APP_KIT_ROOT = ROOT / "apps" / "PowerAppKit"
OUTPUT_PATH = APP_ROOT / "component-manifest.json"
APP_PROJECT = APP_ROOT / "PowerBenchmarkApp.xcodeproj"
SIGNING_CONFIGURATION = APP_ROOT / "Configuration" / "Signing.xcconfig"
RELEASE_IDENTITY = APP_ROOT / "Configuration" / "ReleaseIdentity.json"
RELEASE_CONFIGURATION = (
    APP_ROOT / "Configuration" / "ReleaseIdentity.generated.xcconfig"
)

COMPONENT_ROOTS = {
    "resultsStore": APP_KIT_ROOT / "Sources" / "PowerResultsStore",
    "submissionKit": APP_KIT_ROOT / "Sources" / "PowerSubmissionKit",
    "githubSubmission": (
        APP_KIT_ROOT / "Sources" / "PowerGitHubSubmission"
    ),
    "releasePreflight": (
        APP_KIT_ROOT / "Sources" / "PowerReleasePreflight"
    ),
    "runCheckpointStore": (
        APP_KIT_ROOT / "Sources" / "PowerRunCheckpointStore"
    ),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _aggregate(paths: list[Path], source_root: Path) -> dict[str, Any]:
    if not paths:
        raise ValueError(
            f"component has no files: {_relative(source_root)}"
        )
    files = [
        {"path": _relative(path), "sha256": _sha256(path)}
        for path in sorted(paths)
    ]
    canonical = json.dumps(
        files,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "sourceRoot": _relative(source_root),
        "files": files,
        "sha256": hashlib.sha256(canonical).hexdigest(),
    }


def _pin(path: Path) -> dict[str, str]:
    return {"path": _relative(path), "sha256": _sha256(path)}


def render_manifest() -> str:
    project_text = (APP_PROJECT / "project.pbxproj").read_text(
        encoding="utf-8"
    )
    if "DEVELOPMENT_TEAM =" in project_text:
        raise ValueError(
            "personal DEVELOPMENT_TEAM must not be stored in project.pbxproj"
        )
    shell_sources = list(
        (APP_ROOT / "PowerBenchmarkApp").glob("*.swift")
    )
    shell_sources.append(
        APP_ROOT / "Power2ProductIdentity.generated.swift"
    )
    shell_sources.append(
        APP_ROOT / "Power2CandidateCatalog.generated.swift"
    )
    shell_sources.append(
        APP_ROOT / "PowerBenchmarkApp" / "Info.plist"
    )
    shell_sources.append(SIGNING_CONFIGURATION)
    shell_sources.append(RELEASE_IDENTITY)
    shell_sources.append(RELEASE_CONFIGURATION)
    components = {
        "appShell": _aggregate(shell_sources, APP_ROOT),
        **{
            name: _aggregate(
                list(source_root.glob("*.swift")),
                source_root,
            )
            for name, source_root in COMPONENT_ROOTS.items()
        },
    }
    value = {
        "schemaVersion": "power-app-component-manifest-1.0.0",
        "productID": "power",
        "xcodeProject": _pin(APP_PROJECT / "project.pbxproj"),
        "infoPlist": _pin(
            APP_ROOT / "PowerBenchmarkApp" / "Info.plist"
        ),
        "certificationScheme": _pin(
            APP_PROJECT
            / "xcshareddata"
            / "xcschemes"
            / "PowerCertification.xcscheme"
        ),
        "officialScheme": _pin(
            APP_PROJECT
            / "xcshareddata"
            / "xcschemes"
            / "PowerOfficial.xcscheme"
        ),
        "signingConfiguration": _pin(SIGNING_CONFIGURATION),
        "releaseIdentity": _pin(RELEASE_IDENTITY),
        "releaseConfiguration": _pin(RELEASE_CONFIGURATION),
        "resolvedDependencies": _pin(
            APP_PROJECT
            / "project.xcworkspace"
            / "xcshareddata"
            / "swiftpm"
            / "Package.resolved"
        ),
        "supportPackage": _pin(APP_KIT_ROOT / "Package.swift"),
        "supportPackageDependencies": _pin(
            APP_KIT_ROOT / "Package.resolved"
        ),
        "components": components,
    }
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail instead of rewriting a stale generated manifest",
    )
    args = parser.parse_args(argv)
    try:
        expected = render_manifest()
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if args.check:
        try:
            actual = OUTPUT_PATH.read_text(encoding="utf-8")
        except OSError:
            actual = ""
        if actual != expected:
            print(
                "error: apps/ios/component-manifest.json is stale",
                file=sys.stderr,
            )
            return 1
        return 0

    OUTPUT_PATH.write_text(expected, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
