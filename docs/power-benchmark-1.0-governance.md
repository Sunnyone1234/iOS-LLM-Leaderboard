# Power Benchmark 1.0 Governance

## Status and scope

This policy governs `suite-b-power@1.0.0-rc.1` submissions, review,
reproduction, corrections, withdrawals, deprecation, and publication. It does
not change the frozen workload, metric, result-schema, validator, or App
contracts.

RC1 remains non-official. This policy defines possible evidence transitions
without authorizing a default ranking, GitHub Release, or version tag.

## Governing principles

- Raw App evidence is immutable.
- Structural validity, protocol conformance, metric eligibility, evidence
  level, and ranking eligibility are separate decisions.
- Failed, cancelled, OOM, not-run, early-stop, and response-ineligible attempts
  are retained.
- A valid result may have no eligible metric.
- Review records bind immutable files by SHA-256 and never rewrite them.
- Every public claim is limited to the exact model, runtime, device, OS,
  configuration, workload, and release represented by the evidence.
- License metadata is factual evidence, not legal advice.

## Roles and authority

Repository maintainers are listed in [`MAINTAINERS.md`](../MAINTAINERS.md).
Only a maintainer with merge authority may accept an evidence transition,
publish a correction or withdrawal record, deprecate evidence, authorize a
ranking, or approve a benchmark release.

CI and scripts report facts. They cannot grant trust. A merged review record
is the auditable decision; a pull-request approval without such a record does
not change evidence level.

## Evidence levels

| Evidence level | Required evidence | Default ranking after an official release |
| --- | --- | --- |
| `unreviewed` | Local or Draft package | No |
| `community-submitted` | Valid immutable package plus accepted initial review | No |
| `reproduced` | Community-submitted evidence plus compatible independent accepted evidence | Candidate view only |
| `verified` | Maintainer review of identity, raw recalculation, privacy, declarations, and publication claims | Yes, eligible metrics only |
| `maintainer-reference` | Maintainer-run reference evidence receiving the same integrity and privacy review | Yes, eligible metrics only, visibly labeled |

Evidence level describes confidence in the evidence process, not model
quality. `verified` does not turn an ineligible metric into an eligible one.

For RC1, every review record must retain:

```text
releaseOfficial = false
rankingAuthorized = false
defaultLeaderboardEligible = false
```

## Review transitions

The frozen review record permits only these forward transitions:

| Review type | From | To |
| --- | --- | --- |
| Initial review | `unreviewed` | `community-submitted` |
| Reproduction review | `community-submitted` | `reproduced` |
| Verification review | `community-submitted` or `reproduced` | `verified` |
| Maintainer reference review | `unreviewed` or `community-submitted` | `maintainer-reference` |

Transitions are append-only. Review records are validated in timestamp order
and must bind the exact submission manifest and result digests.

An initial review requires all of the following:

- package layout, UUIDs, and SHA-256 are consistent;
- the frozen result schema passes;
- the frozen semantic protocol validator passes;
- contributor declarations are complete;
- the conflict disclosure has been reviewed; and
- no prohibited personal data is present.

Metric ineligibility does not fail initial review. Its reason codes and null
aggregates remain visible.

## Independent reproduction

Reproduction requires a second accepted submission that:

- belongs to the same benchmark release, workload version, fixture,
  measurement mode, inference configuration, model artifact/revision,
  runtime/backend/dependencies, device model, OS build, and memory class;
- has a distinct result ID and execution session ID;
- is submitted by a different public GitHub handle; and
- has already reached at least `community-submitted`.

Because the privacy contract deliberately excludes UDID and serial number,
the project cannot cryptographically prove that two submissions used different
physical units. The independent-contributor rule is the public, reviewable
proxy and must be described as such.

Reproduction does not require equal metric values. Large differences remain
evidence to investigate; they are not silently averaged or discarded.

## Compatible comparison and publication

Public comparisons may aggregate only evidence with the same comparison
identity defined above. Model-only rows are a presentation convenience and
must link to the exact underlying configuration.

After a release is explicitly authorized:

- `community-submitted` evidence remains outside default ranking;
- `reproduced` evidence may appear in a candidate view;
- `verified` and `maintainer-reference` evidence may appear by default only
  for individually eligible metrics; and
- withdrawn, deprecated, incompatible, or superseded evidence is excluded.

No single Power or Ship aggregate score is authorized.

## Corrections

Accepted files are never edited in place. A correction requires:

1. a new submission package with new submission, result, and session IDs when
   execution evidence changes;
2. an issue or pull request explaining the error and scope;
3. a lifecycle entry linking old and new immutable digests;
4. removal of the old evidence from active comparison; and
5. retention of the old record as `superseded`, unless privacy removal applies.

Documentation-only corrections that do not alter evidence or interpretation
may update prose through a normal pull request and must not change raw files.

## Withdrawal

A contributor may request withdrawal using the GitHub account named in the
submission. A maintainer may also withdraw evidence for integrity, policy,
license, or privacy reasons. The decision records the requester, date, reason
category, affected submission/result IDs, and reviewer.

Withdrawal immediately excludes the evidence from active views. Raw evidence
normally remains as an auditable withdrawn record. When retention would expose
personal data, credentials, or legally restricted content, maintainers remove
the sensitive bytes and retain a non-sensitive tombstone containing hashes and
the reason category.

## Deprecation

Deprecation applies when a release, workload, runtime path, validator, or
evidence class is no longer suitable for active comparison. Deprecation never
silently reinterprets historical measurements. The release history must state:

- affected identities and versions;
- effective date;
- technical reason;
- active-view impact; and
- replacement or migration path, if one exists.

Major changes to prompts, timing boundaries, formulas, eligibility, or
execution require a new version. Historical evidence retains its original
identity and decision history.

## Release history and approval

Release history is append-only and lives beside the release manifests under
`benchmarks/suite-b-on-device-performance/releases/`. Each entry records
status, scope, known limitations, superseded versions, and publication or
withdrawal decisions.

Publishing a GitHub Release, creating a tag, changing
`officialResultEligible`, or authorizing ranking requires explicit maintainer
approval after the complete RC checklist passes. Preparing or merging an RC
package is not publication approval.

## Conflicts, appeals, and conduct

Affiliated submissions are allowed when disclosed. Maintainers must record
their own material conflict and should request an additional reviewer where
one is available. Maintainer-reference runs are always visibly labeled.

A contributor may appeal a decision by opening an issue that cites the
submission and review IDs and identifies the disputed rule or evidence. The
appeal cannot modify raw files; any change is recorded as a new review or
lifecycle event.

All participation is subject to [`CODE_OF_CONDUCT.md`](../CODE_OF_CONDUCT.md).
