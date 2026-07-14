#!/usr/bin/env python3
"""Reject the one known erroneous automated commit identity.

This guard is intentionally narrow. It does not restrict community contributor
names or email addresses beyond the exact identity involved in the documented
2026-07-14 authorship correction.
"""

from __future__ import annotations

import argparse
import subprocess
import sys


FORBIDDEN_IDENTITIES = {("Codex", "codex@openai.com")}


def commits_in_revision(revision: str) -> list[tuple[str, str, str]]:
    command = [
        "git",
        "log",
        "--format=%H%x1f%an%x1f%ae%x1e",
    ]
    command.append("--all" if revision == "--all" else revision)
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    commits: list[tuple[str, str, str]] = []
    for record in result.stdout.split("\x1e"):
        fields = [field.strip() for field in record.split("\x1f")]
        if len(fields) == 3 and fields[0]:
            commits.append((fields[0], fields[1], fields[2]))
    return commits


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--range",
        dest="revision",
        default="--all",
        help="Git revision or range to inspect (default: all refs)",
    )
    args = parser.parse_args()

    commits = commits_in_revision(args.revision)
    violations = [
        commit
        for commit in commits
        if (commit[1], commit[2]) in FORBIDDEN_IDENTITIES
    ]
    if violations:
        for commit_hash, author_name, author_email in violations:
            print(
                f"forbidden commit identity: {commit_hash} "
                f"{author_name} <{author_email}>",
                file=sys.stderr,
            )
        print(
            "Use the human contributor's verified Git author identity; see "
            "docs/provenance/2026-07-14-history-correction.md.",
            file=sys.stderr,
        )
        return 1

    print(f"Commit identity check passed for {len(commits)} commit(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
