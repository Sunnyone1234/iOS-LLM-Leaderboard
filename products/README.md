# Product contracts

This directory is the normative home for the clean-break product
architecture.

- `power/` owns Power Programs, Targets, policies, runner certificates, and
  release pointers.
- `ship/` will own separate Ship Programs and policies when its migration is
  approved.

Released contracts and manifests are CC BY 4.0. Executable App and tool code
remains MIT-licensed in `apps/` and `scripts/`.

Power 2 is active. [`power/current.json`](power/current.json) is its only
public authority and opens intake for the exact pinned stack, Runner
certificate, and supported Official App release. `power/candidate.json`
retains the initial pre-activation review surface; `power/next.json` records
the completed subsequent activation and is not a second public pointer.

Nothing in this directory imports, translates, validates, ranks, or promotes
Power 1.0 or 1.1 evidence. Those releases remain a read-only historical plane
indexed by the
[Power 1.x archive manifest](../benchmarks/suite-b-on-device-performance/releases/power-1.x-archive.json).
