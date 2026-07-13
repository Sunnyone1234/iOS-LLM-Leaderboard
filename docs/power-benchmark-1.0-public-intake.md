# Power Benchmark 1.0 Public Intake

## Status

Power Benchmark 1.0 public result intake is **open**.

- Opened: `2026-07-13`
- Maintainer authorization: `YizeSun`
- Official benchmark release: `suite-b-power@1.0.0`
- Submission source contract: `suite-b-power@1.0.0-rc.1`
- Reference App: `0.8.0` build `10`

Power 1.0 adopted the RC1 protocol, workloads, result schema, validator, and
reference App without changing their semantics. New submissions therefore keep
the exact RC1 source identity emitted by the App. They are reviewed as evidence
for the published Power 1.0 standard; their source bytes and identities are
never relabeled.

The original [RC1 submission guide](power-benchmark-1.0-submission.md) and
[governance policy](power-benchmark-1.0-governance.md) are SHA-256-pinned
release assets. Their pre-approval status wording is retained byte-for-byte for
reproducibility. This document is the later maintainer authorization that opens
intake; it changes operational status only and does not rewrite either frozen
asset.

## Accepted package

One contribution contains exactly:

```text
submissions/suite-b/power-1.0.0-rc.1/draft/<submissionID>/
├── submission.json
└── result.json
```

`result.json` must be the unmodified App export. `submission.json` records the
contributor declarations, public GitHub handle, conflict disclosure, result
identity, and SHA-256 binding. Screenshots, device names, account identifiers,
logs, and manually entered measurements are not accepted.

After reviewing the App export and confirming all seven declarations, create a
package from the repository root:

```bash
python3 scripts/create_suite_b_power_submission.py \
  /path/to/app-export.json \
  --output-root submissions/suite-b/power-1.0.0-rc.1/draft \
  --contributor YOUR_GITHUB_HANDLE \
  --conflict-category none \
  --conflict-statement "No conflict of interest disclosed." \
  --accept-declarations
```

Use the real conflict category and statement when an affiliation exists. Then
validate the generated package:

```bash
python3 scripts/validate_suite_b_power_submission.py \
  submissions/suite-b/power-1.0.0-rc.1/draft/<submissionID>
```

Open a pull request containing only the new two-file package and select
**Power 1.0 Draft package (adopted RC1 contract)** in the pull-request
template. The frozen RC1 guide remains the normative package definition where
this authorization does not explicitly change operational status.

## Trust and ranking boundary

Opening intake authorizes contributors to submit reviewable evidence. It does
not authorize any individual submission as official, verified, or ranked.

1. Every package begins as `unreviewed`.
2. CI checks structure, protocol conformance, integrity, and declarations.
3. A maintainer review record is required for an evidence-level transition.
4. The frozen RC1 review record keeps publication and ranking flags false.
5. Adding community evidence to an active Power leaderboard requires a
   separate, hash-bound publication decision; the immutable `1.0.0` release
   package and tag are never rewritten.

These rules continue to govern formal evidence levels and the immutable
official release. The later
[Power Community Reproduction and Live Ranking policy](power-community-ranking.md)
adds a separate, explicitly labeled live community view. A valid package
merged into `main` may enter that view automatically without changing its
formal evidence level or the Power 1.0 release package.

For the live view, the declared GitHub handle must match the pull-request
author. Different GitHub accounts count as independent contributors inside an
exact comparison cell. The same account may contribute to any number of
different cells; repeated runs by that account within one cell do not increase
the independent-contributor count.

Failed, cancelled, OOM, not-run, early-stop, and metric-ineligible attempts are
valid evidence when preserved by the App. Contributors must not rerun a test
merely to hide an unfavorable outcome.

## Frozen scope

Public intake does not change:

- B-UX-001 or B-PIPE-001;
- the Power protocol, result schema, semantic validator, or reason codes;
- App 0.8.0 build 10;
- model profiles, runtime settings, measurement counts, or eligibility rules;
- the published Power 1.0 evidence set or rankings; or
- Ship Deployment Profiles 1.0.

The existing `power-1.0.0-rc.1` path remains deliberate compatibility and
provenance, not an indication that Power 1.0 itself is unpublished.
