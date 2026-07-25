# Community submissions

## Current Power 2 intake

New physical-device results use immutable two-file packages:

```text
submissions/power/text-generation-performance/2.0.0/draft/<submission-id>/
├── submission.json
└── result.json
```

Create and validate one with:

```bash
python3 scripts/power submit /path/to/result.json \
  --github YOUR_GITHUB_HANDLE \
  --accept-declarations
python3 scripts/power validate \
  submissions/power/text-generation-performance/2.0.0/draft/<submission-id>
```

`result.json` must remain byte-for-byte the App export. The separate manifest
records contributor, declarations, conflict, environment, license, and result
hash identity. Trusted base-repository CI validates the exact current Program,
Target, App release, Runner certificate, and contributor identity without
rewriting the result.

See the [current Power quickstart](../contributor-kit/power.md).

## Historical paths

- `power-1.0.0-rc.1/` preserves published Power 1.0 source-contract packages
  and hash-bound review history.
- `power-1.1.0/` preserves the closed Power 1.1 community intake.
- `draft/` and `reviews/community-submitted/` preserve the earlier Framework
  v1 Pilot workflow.

They remain for validation, audit, correction, and reproduction. Do not use
them for a new Power contribution. The retained paths are indexed by the
[Power 1.x archive manifest](../benchmarks/suite-b-on-device-performance/releases/power-1.x-archive.json).
