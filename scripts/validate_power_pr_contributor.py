#!/usr/bin/env python3
"""Bind newly added Power submission manifests to the pull-request author."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


def validate_contributor(
    paths: Iterable[Path],
    expected_github_handle: str,
) -> list[str]:
    errors: list[str] = []
    expected = expected_github_handle.casefold()
    for path in paths:
        try:
            manifest = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"{path}: {error}")
            continue
        actual = manifest.get("contributor", {}).get("githubHandle")
        if not isinstance(actual, str) or actual.casefold() != expected:
            errors.append(
                f"{path}: contributor.githubHandle must match pull-request author "
                f"{expected_github_handle}"
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-contributor", required=True)
    parser.add_argument("--paths-file", type=Path)
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()
    paths = list(args.paths)
    if args.paths_file:
        paths.extend(
            Path(line)
            for line in args.paths_file.read_text().splitlines()
            if line.strip()
        )
    errors = validate_contributor(paths, args.expected_contributor)
    if errors:
        print("\n".join(errors))
        return 1
    print(
        f"validated {len(paths)} new Power submission manifest(s) for "
        f"{args.expected_contributor}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
