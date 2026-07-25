# Power community acceptance, reproduction, and ranking

## Scope

This document explains the current Power 2 community view. The normative
ranking contract is the hash-pinned ranking policy referenced by
[`products/power/current.json`](../products/power/current.json). Power 1
community datasets remain historical and are not input to this view.

## Admission before ranking

A contribution becomes repository evidence only after its current Power 2
two-file package:

1. is opened by the GitHub account declared in `submission.json`;
2. passes trusted package, hash, schema, current-stack, source-declaration,
   physical-target, duplicate, and result-only-scope checks; and
3. is merged by the evidence-only automation or a maintainer.

Intake and ranking remain separate. Structurally valid failure, cancellation,
OOM, assisted-environment, or metric-ineligible evidence can be Accepted and
retained without supplying a displayed metric.

## Source-built trust states

The locally signed Official configuration self-declares its App release
identity. Trusted CI verifies that the declaration and submitted bytes match
the current repository contracts; it does not attest the installed binary.

| Distinct eligible contributors in an exact cell | Display state |
| ---: | --- |
| 1 | Accepted |
| 2 | Reproduced |
| 3 or more | Contributor-weighted |

`Accepted` means admissible single-contributor evidence, not independently
verified performance. `Reproduced` is derived only from two distinct eligible
GitHub accounts. Three contributors enable aggregation across one reduced
value per contributor. There is no global Power score.

## Exact comparison identity

Contributors count together only when every comparison field required by the
current policy matches, including:

- Program, Target, workload, workload version, and measurement mode;
- Runner certificate;
- exact model artifact, revision, quantization, and tokenizer;
- Runtime version, revision, backend, and dependency identity;
- device machine identifier, OS version, and OS build; and
- inference configuration.

Changing any field creates a different exact cell. The UI may group compatible
display families, but grouping never rewrites evidence identity.

## Metric reduction

- One GitHub account counts once per exact cell.
- All accepted repeated runs remain traceable.
- Each metric first takes the median of eligible runs per contributor.
- The displayed value is then the median across contributor medians.
- Metric direction is defined by the pinned Program and ranking policy.
- Thermal assistance other than `none` remains evidence but is excluded from
  the ordinary view.

Behavior eligibility, recommendation eligibility, and each metric's ranking
eligibility are separate decisions. Pipeline TTFT is never relabeled as
user-visible first-renderable time.

## Automation

```text
App or scripts/power package
→ contributor-owned result PR
→ Power submission intake + commit identity
→ evidence-only merge
→ scripts/power preview
→ one GitHub Pages deployment
```

The auto-merge worker is triggered after either required check completes. Runs
for the same fork branch are serialized; the first run that observes both
successful checks may squash-merge, and a later peer exits successfully if the
PR is already closed. Normal code and documentation PRs receive
`not_applicable` intake and are never evidence-auto-merged.

The repository ruleset should require:

- **Power submission intake**;
- **Validate commit identity**;
- pull-request merges; and
- no review approval as a universal condition if fully automatic evidence
  acceptance is desired.

Use `python3 scripts/power preview --output /tmp/power-preview` to reproduce the
current derived view locally.
