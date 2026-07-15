# Power Benchmark 1.1 Release Notes — Final Review Draft

Power 1.1 is not released yet. These notes are a review template and must not
be published until the final `1.1.0` policy and reports, contributor
declarations, limitations review, and explicit maintainer authorization are
complete.

## Intended release change

Power 1.1 preserves the two Power 1.0 workloads and their execution boundaries.
It makes one responsibility boundary explicit: the reference App exports all
technically derivable measurements, while the independent validator determines
behavior conformance and metric, ranking, and recommendation eligibility.

## Compatibility

- Power 1.0 evidence and ranking remain immutable.
- Power 1.1 draft evidence is not promoted.
- New App 0.13.0 RC executions are required.
- No combined score is introduced.
- Performance ranking and recommendation eligibility remain separate.

## Evidence status

Physical-device RC matrix: **complete**.

RC evidence accepted for review: **six of six results**.

Protocol-conformant results: **six of six**.

Expected metric eligibility: **complete for all six results**.

Behavior status for Short Interaction: two `verified`, one `not_verified`.
The `not_verified` result remains performance-metric eligible but cannot be
presented as behavior-verified or recommended.

The exact evidence inventory, observed values, thermal outcomes, checksums,
privacy review, replacement history, and limitations are recorded in
[`device-verification/REVIEW.md`](device-verification/REVIEW.md).

## Release boundary

The RC validation reports intentionally authorize neither ranking nor
publication. The formal release requires a new final `1.1.0` ranking policy and
regenerated reports bound to these same raw result digests. RC report decisions
must not be edited or silently reinterpreted.

No Power 1.1 tag, GitHub Release, official-result adoption, or leaderboard
change is authorized by this draft.
