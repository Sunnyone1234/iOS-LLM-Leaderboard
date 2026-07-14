# Power Benchmark 1.0 Public Intake

## Status

Power Benchmark 1.0 public result intake is **open**.

New contributors should start with the
[Power 1.0 contributor quickstart](../contributor-kit/power-1.0-quickstart.md).
This document remains the complete operational and trust-boundary reference.

- Opened: `2026-07-13`
- Maintainer authorization: `YizeSun`
- Official benchmark release: `suite-b-power@1.0.0`
- Submission source contract: `suite-b-power@1.0.0-rc.1`
- Reference App: `0.8.0` build `10`

Two exact App sources are authorized for public intake:

| Purpose | App identity | Exact source |
| --- | --- | --- |
| Reproduce the existing Qwen comparison cells | `0.8.0` build `10` | `2f105ff463bc9b281b19655ba711b1ca7dee8759` |
| Test the four pinned candidates in the non-ranking model catalog | `0.9.0` build `11` | `002c76ccbfed7b1c8b7c13313b887aaebf610a3e` |

App 0.9.0 is an additional community-testing source, not a rewrite of the
published Reference App or its six-result matrix. Its candidate guide is
[Test a Recommended Power Model](../contributor-kit/test-recommended-model.md).

Power 1.0 adopted the RC1 protocol, workloads, result schema, validator, and
Reference App without changing their semantics. New submissions keep the exact
source identity emitted by whichever authorized App source they build. They
are reviewed as evidence for the published Power 1.0 standard; their source
bytes and identities are never relabeled or silently grouped across App
versions.

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

The pull request should also complete the
[Power 1.0 Environmental Observation Draft](../benchmarks/suite-b-on-device-performance/power-1.0-environment-control.md).
Ambient temperature, externally measured device-surface temperature, case
state, and placement are recommended observations, not current hard admission
requirements. Deliberate external cooling or heating must be disclosed so
assisted evidence is not silently aggregated into the ordinary live ranking.
Because the current package and generator cannot encode a separate assisted
class, ordinary intake merge requires `none`; assisted and unresolved
`unknown` submissions remain reviewable in their pull requests rather than
being merged into `main`. This record does not add a third package file or
modify the frozen JSON schemas.

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

The frozen automated checks cover the seven JSON manifest declarations. The
environmental observation block is reviewed manually because CI cannot verify
physical conditions. Missing temperature, case, or placement observations do
not block ranking under this draft, and passing CI must not be represented as
verification of those observations. Before merge, the maintainer must also
confirm that thermal assistance is declared `none`; there is no automated
post-merge exclusion mechanism in the current live-ranking generator.

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
- App 0.8.0 build 10 or any existing exact comparison identity;
- the existing Qwen model profiles, runtime settings, measurement counts, or
  eligibility rules;
- the published Power 1.0 evidence set or rankings; or
- Ship Deployment Profiles 1.0.

Public intake now additionally permits App 0.9.0 build 11 at the exact source
listed above for four pinned candidate artifacts. Each accepted candidate run
creates a new exact comparison cell. This operational expansion adds no
placeholder result, changes no existing rank, and does not imply physical
iPhone compatibility before evidence is submitted.

The existing `power-1.0.0-rc.1` path remains deliberate compatibility and
provenance, not an indication that Power 1.0 itself is unpublished.
