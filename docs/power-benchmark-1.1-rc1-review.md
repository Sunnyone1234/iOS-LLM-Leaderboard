# Power Benchmark 1.1 RC1 Final Review

> Freeze update (2026-07-15): the three blockers identified by this review are
> closed by the Power 1.1 RC1 result/report schemas, direct schema-registry
> validator, complete pinned-asset manifest, strict report invariants, and App
> 0.13.0 build 16. See
> [`power-benchmark-1.1-rc1-freeze.md`](power-benchmark-1.1-rc1-freeze.md).
> Physical-device verification and formal release approval remain pending.

Date: 2026-07-15

Status: **RC freeze not yet approved**

This review evaluates whether `suite-b-power@1.1.0-draft.1` can be frozen as a
release candidate. It does not authorize publication, ranking, tagging, or the
promotion of draft evidence.

## Decision

The Power 1.1 responsibility boundary is accepted:

- the App produces raw execution evidence and every technically derivable
  metric;
- the independent validator determines structural validity, protocol
  conformance, metric eligibility, and behavior status;
- behavior status never erases a technically valid performance measurement;
- measured-performance and behavior-verified recommendation views remain
  separate; and
- Power 1.0 evidence and ranking remain immutable.

The current branch is **not ready to become `1.1.0-rc.1`**. Three contract
freeze blockers must be resolved first. Additional execution and publication
work must then be completed against the exact RC identity before Power 1.1 can
become official.

## Evidence reviewed

- six focused commits on `codex/power-1.1-protocol`;
- protocol Markdown and machine-readable protocol;
- result and validation-report schema drafts;
- validation reason registry and independent validator;
- App `0.12.0` build `15` at source commit
  `75c6d393c3f79e6d968fb8d66e796e4ce66f22ef`;
- 188 passing repository tests;
- a successful Release simulator build and complete Swift test run; and
- two physical-device design-validation results from the exact App source:
  - Sustained Generation result
    `BD20245C-14A8-4605-934B-D798D95EB2DF`, SHA-256
    `560c6e19e01f87c4220ccfe48510cd547ecf84f269686b450f5fc029d55472d7`;
  - Short Interaction result
    `85AD1D27-BE50-46AE-880F-5434AF65CF09`, SHA-256
    `7850702125b0417be2108899dad4764ed3c6a77c5f26b7bc12612403243556a9`.

Both physical-device results are structurally valid and protocol-conformant.
Every applicable performance metric is eligible. The Short Interaction result
also demonstrates the intended separation: its deterministic behavior policy
returns `not_verified`, while all six performance metrics remain eligible.
The privacy scan found no local path, account name, email address,
authorization token, cookie, signed download URL, password, or secret.

These files are draft design-validation evidence. They must not be relabeled,
mutated, or promoted into RC or official evidence.

## Confirmed properties

1. No Power 1.0 result, adoption record, release manifest, or leaderboard file
   changes in this branch.
2. The App exports technical measurements independently of its advisory
   `responseConformance` observation.
3. The validator recomputes metrics from raw timing, token, memory, thermal,
   and renderability evidence.
4. The validator recomputes Short Interaction behavior from retained generated
   text and does not trust the App's behavior badge.
5. `verified`, `not_verified`, and `contradicted` are distinct report states;
   the current behavior policy emits no positive contradiction decision.
6. A behavior status other than `verified` blocks only the recommended view,
   not a metric-specific measured-performance view.
7. Validation reports bind the exact submitted result SHA-256 and carry
   protocol, validator, and ranking-policy identities.
8. Raw App results remain non-official; ranking authority belongs to a
   separately generated validation report and release policy.

## RC freeze blockers

### B1 — Execute the declared result schema

The draft validator currently rewrites the three Power 1.1 identity fields to
Power 1.0 values and delegates structural validation to the Power 1.0 schema.
That preserves the current field shape, but the declared Power 1.1 result
schema is not itself the executable structural contract.

Before RC freeze, choose and test one normative path:

- validate the Power 1.1 schema directly with an explicit registry containing
  its pinned Power 1.0 schema dependency; or
- freeze the compatibility translation as an explicit normative mechanism and
  add complete equivalence tests for every reused constraint.

The preferred RC path is direct schema execution. A pinned schema must not be
able to drift away from the validator that claims to enforce it.

### B2 — Pin the complete normative asset set

The draft manifest pins the protocol, schemas, reason registry, validator, and
Power 1.0 base-schema dependency. Unlike the Power 1.0 RC manifest, it does not
yet pin all execution-critical dependencies.

The RC manifest must additionally pin at least:

- both exact prompt fixtures;
- metric definitions inherited by Power 1.1;
- the exact reference App version, build, and source commit;
- the two executable App plan files and their workload registry; and
- the exact ranking-policy definition that the later leaderboard consumer must
  enforce.

Every pinned asset must have a verified SHA-256 in the RC manifest.
The report-consuming implementation is a post-freeze release task under P1 and
must be pinned by the official publication package rather than invented after
publication.

### B3 — Freeze strict validation-report identities and decision invariants

The draft report schema correctly fixes the protocol identity, but currently
accepts any nonempty validator version and ranking-policy version. It also
permits combinations of behavior status and reason codes that the trusted
validator would never generate.

Before RC freeze:

- make the supported validator and ranking-policy versions exact identities;
- constrain valid-result report identities without preventing a minimal report
  for structurally invalid input;
- enforce or test behavior-status/reason consistency; and
- retain the current minimal report shape without duplicating raw evidence.

## Required after RC freeze and before official Power 1.1

### P1 — Implement the report-consuming intake and ranking path

Current submission workflows, community ranking generation, Pages generation,
and review tooling support Power 1.0 only. No current consumer verifies the
Power 1.1 validation-report version, result SHA-256 binding, protocol version,
validator version, and ranking-policy version before using a decision.

The official Power 1.1 path must consume validation reports fail-closed. It
must not duplicate validator conformance rules inside leaderboard code.

### P2 — Declare and run the exact RC verification matrix

The minimum RC matrix must be declared before execution. The existing protocol
requires a new physical-device matrix but does not yet state its minimum model
count. The maintainer must approve that scope explicitly.

All accepted runs must use the exact RC App and identities. The package must
retain raw results, generated validation reports, execution notes, and
checksums. Draft results reviewed above are not promotable.

### P3 — Prepare and approve the official release package

The final package must include:

- RC manifest and complete pinned-asset verification;
- physical-device evidence adoption record;
- raw-result and validation-report checksums;
- release notes and known limitations;
- generated measured-performance and behavior-status views;
- proof that the official view consumes report decisions fail-closed; and
- explicit maintainer authorization for evidence adoption, publication,
  ranking, tag, and GitHub Release.

## Known limitation accepted for RC review

`short-interaction-response-v1` is intentionally deterministic and narrow. A
semantically correct phrase such as "sync once you reconnect" may be
`not_verified` because it does not contain one of the frozen literal
connectivity-return terms. This is not a protocol failure and does not erase
performance evidence. It only prevents a behavior-verified recommendation.

Changing that behavior policy is outside this RC freeze unless the maintainer
explicitly chooses a new policy version. The current review recommends keeping
the policy stable and documenting the limitation.

## Freeze sequence

1. Resolve B1 through B3 without changing workload IDs, fixtures, measurement
   boundaries, generation settings, or metric formulas.
2. Create `1.1.0-rc.1` protocol, schema, validator, reason-registry, ranking
   policy, App, plan, and release-manifest identities.
3. Run the complete automated test suite and verify every pinned digest.
4. Stop implementation changes to the frozen execution and validation
   contract.
5. Run P1 through P3 against the exact RC identity.
6. Request explicit maintainer release authorization.

No official Power 1.1 publication or ranking is permitted before this sequence
is complete.
