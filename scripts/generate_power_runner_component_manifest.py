#!/usr/bin/env python3
"""Generate the digest manifest for the next Power 2 Runner candidate.

The active Runner manifest is a released identity and must not be rewritten
when source development continues. This generator writes a separate,
lifecycle-neutral candidate manifest. Certification and release state belong
to the release plan and Runner certificate, not to this source digest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "apps/PowerRunnerKit"
OUTPUT_PATH = PACKAGE_ROOT / "candidate-component-manifest.json"
PACKAGE_MANIFEST_PATH = PACKAGE_ROOT / "Package.swift"
COMPONENTS = {
    "evidenceEnvelope": "PowerEvidence",
    "runnerCore": "PowerRunnerCore",
    "programModule": "PowerTextProgram",
    "targetAdapter": "PowerAppleTarget",
    "runtimeAdapter": "PowerMLXRuntime",
}
DEPENDENCY_LOCK_PATH = PACKAGE_ROOT / "Package.resolved"
RUNTIME_IDENTITY_PATH = PACKAGE_ROOT / "runtime-identity.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _component(name: str) -> dict[str, Any]:
    source_root = PACKAGE_ROOT / "Sources" / name
    paths = sorted(source_root.glob("*.swift"))
    if not paths:
        raise ValueError(f"component has no Swift sources: {name}")
    files = [
        {"path": _relative(path), "sha256": _sha256(path)}
        for path in paths
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


def render_manifest() -> str:
    value = {
        "schemaVersion": "power-runner-component-manifest-1.0.0",
        "productID": "power",
        "packageManifest": {
            "path": _relative(PACKAGE_MANIFEST_PATH),
            "sha256": _sha256(PACKAGE_MANIFEST_PATH),
        },
        "resolvedDependencies": {
            "path": _relative(DEPENDENCY_LOCK_PATH),
            "sha256": _sha256(DEPENDENCY_LOCK_PATH),
        },
        "runtimeIdentity": {
            "path": _relative(RUNTIME_IDENTITY_PATH),
            "sha256": _sha256(RUNTIME_IDENTITY_PATH),
        },
        "components": {
            key: _component(module)
            for key, module in COMPONENTS.items()
        },
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
                "error: apps/PowerRunnerKit/"
                "candidate-component-manifest.json is stale",
                file=sys.stderr,
            )
            return 1
        return 0

    OUTPUT_PATH.write_text(expected, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
