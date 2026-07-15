# Community submissions

## Current Power 1.1 intake

New physical-device results use immutable two-file packages:

```text
submissions/suite-b/power-1.1.0/draft/<submission-id>/
├── submission.json
└── result.json
```

Create and validate one with:

```bash
python3 scripts/power.py submit /path/to/result.json \
  --github YOUR_GITHUB_HANDLE \
  --accept-declarations
python3 scripts/power.py validate \
  submissions/suite-b/power-1.1.0/draft/<submission-id>
```

`result.json` must remain byte-for-byte the App export. The separate manifest
records contributor, final release, conflict, environment, license, and result
hash identity. CI validates it but does not rewrite the result, grant Verified
status, or modify the frozen Power release.

See the [Power 1.1 quickstart](../contributor-kit/power-1.1-quickstart.md).

## Historical paths

- `power-1.0.0-rc.1/` preserves published Power 1.0 source-contract packages
  and hash-bound review history.
- `draft/` and `reviews/community-submitted/` preserve the earlier Framework
  v1 Pilot workflow.

They remain for validation, audit, correction, and reproduction. Do not use
them for a new Power 1.1 contribution.
