# Power Benchmark 1.0 Foundation

## Status

Power Benchmark 1.0 Foundation is the active pre-release standardization
track for Phase 1 Power. It is not an official benchmark release, does not
authorize official results, and must not be tagged or published as version
1.0.

The completed Power + Ship Pilot v0.1 matrix is retained as historical
foundation evidence. The Pilot proved that the App, raw-result, validation,
and presentation path can operate on a physical iPhone. The maintainer chose
not to publish a Pilot tag or GitHub Release. Pilot results remain
non-official and cannot be relabeled or promoted into Power 1.0 results.
Future migration documentation may map their historical identities, but must
not change their eligibility or provenance.

## Foundation Objective

The Foundation phase turns the working Pilot evidence path into a versioned,
reviewable benchmark contract. It closes the gaps that would otherwise make a
1.0 result ambiguous, irreproducible, or impossible to validate independently.

Foundation work is limited to the existing Power benchmark. It does not
redesign Product Architecture, add a Build deliverable, create a Ship score,
or expand the benchmark merely to increase workload count.

## Frozen Candidate Scope

Exactly two existing workload IDs are candidates for Power Benchmark 1.0:

| Workload ID | 1.0 role | Foundation classification |
| --- | --- | --- |
| `b-ux-001-short-interaction` | Short-interaction responsiveness | Stable candidate |
| `b-pipe-001-sustained-generation` | Sustained decode and thermal-transition evidence | Stable candidate |

The following workloads remain Experimental and are not part of the 1.0
Foundation release contract:

- `b-pipe-002-input-length-sweep`;
- `b-ux-002-context-assistance`.

No workload ID is renamed. The current `0.2.0-pilot` workload versions remain
historical Pilot identities. A future 1.0 candidate version must be frozen
explicitly after its protocol ambiguities are resolved; existing Pilot files
must retain their original identity.

These Foundation classifications are release-planning decisions only. They do
not rewrite the lifecycle status stored in the current workload manifests.

## Contract Layers

Power 1.0 must freeze these layers together:

1. **Benchmark release identity**: an immutable release manifest pins every
   compatible workload, measurement mode, metric definition, result schema,
   validator, and minimum runner version.
2. **Execution contract**: workload fixtures, generation settings, cache
   policy, environment admission, attempt order, failure behavior, and metric
   boundaries are unambiguous.
3. **Evidence contract**: the App exports exact execution identity, raw
   attempts, failures and not-run attempts, device/runtime/model metadata, and
   the observations required to recalculate official metrics.
4. **Validation contract**: public schemas and semantic validators reject
   incompatible identities, recalculate supported metrics, and return an
   explicit validation decision without rewriting submitted evidence.
5. **Publication contract**: comparison groups, evidence levels, corrections,
   withdrawals, deprecations, and release history are defined before an
   official leaderboard is enabled.

## Foundation Work Order

### F0 — Historical baseline

Complete.

- Six genuine App 0.6.0 exports exist for three exact model artifacts, one
  physical `iPhone15,3`, and both candidate workloads.
- The Pilot generator accepts all six inputs and retains their raw evidence.
- The Pilot was not tagged or published as a GitHub Release.

### F1 — Contract inventory and alignment

Complete.

- Document the App-emitted `suite-b-result-bundle-0.3` historical schema.
- Align schema references, semantic validator support, App export identity,
  and regression tests.
- Record every remaining protocol, evidence, and governance gap without
  changing the candidate workload IDs.

Completing F1 does not make schema 0.3 or any Pilot result official.

### F2 — Protocol freeze

Complete.

- Resolve timing, token-count, stop, null, failure, OOM, cancellation, memory,
  and thermal edge cases for both candidate workloads.
- Freeze per-metric eligibility and aggregation rules.
- Publish explicit migration rules from the historical Pilot identities.
- Require bounded, independently recalculable evidence for the
  First-renderable proxy TTFT without treating it as a screen-render boundary.

Foundation App 0.7.0 build 9 and result envelope
`suite-b-result-bundle-0.4` were used to exercise the bounded trace contract
during F2. The frozen release-candidate protocol is
`suite-b-power@1.0.0-rc.1`; its normative text, machine-readable identity, and
migration rules are under `benchmarks/suite-b-on-device-performance/`. The App
and 0.4 envelope remain non-official development identities; their successor
release-candidate schema and validator were frozen separately in F3.

### F3 — Release schema and validator freeze

Complete.

- Add immutable benchmark-release identity to the official-candidate result
  contract.
- Freeze a complete public JSON Schema and semantic validator.
- Recalculate every official metric from retained evidence or remove the
  metric from official comparison.
- Define validation status and reason codes without conflating structural
  validity, metric eligibility, evidence level, and ranking eligibility.

Release candidate `suite-b-power@1.0.0-rc.1` now pins the F2 protocol, metric
definitions, fixtures, complete result schema, validation-report schema,
reason-code registry, and semantic validator by SHA-256. The validator
recalculates each candidate ranked metric from retained evidence and always
keeps evidence review and ranking authorization false at this stage.

### F4 — Reference App hardening

Complete.

- Make the App execute only identities compatible with the selected benchmark
  release.
- Export the frozen result contract.
- Preserve completed, failed, cancelled, OOM, and not-run attempts, including
  crash-safe recovery where the official contract requires it.
- Keep contributor review local and avoid collecting private device or account
  identifiers.

App `0.8.0` build `10` now locks the production interface to the two frozen
workload identities, embeds its exact source commit, emits
`suite-b-power-result-1.0.0-rc.1`, retains raw recalculation evidence, and
preserves all frozen terminal outcomes. Atomic checkpoints recover interrupted
sessions conservatively without guessing OOM. Swift-produced fixtures for both
workloads pass the frozen F3 validator with no structural or protocol errors.

This is implementation verification only. It creates no benchmark result and
does not authorize ranking. See
[`power-benchmark-1.0-f4-reference-app.md`](power-benchmark-1.0-f4-reference-app.md).

### F5 — Release-candidate verification

Complete for the declared single-device, single-runtime matrix.

- Run the frozen App on physical devices without changing the release
  contract.
- Validate every submitted bundle with the frozen validator.
- Complete the declared model, runtime, and device coverage matrix with no
  placeholder or simulated result.
- Perform independent metric, integrity, privacy, documentation, and
  reproducibility review.

Six genuine App 0.8.0 build 10 exports cover the three pinned model artifacts
and both frozen workloads on a physical `iPhone15,3`. All six are structurally
valid and protocol-conformant under the frozen F3 validator. Five cells have
eligible metrics. The Qwen3 0.6B Short Interaction cell completed all attempts
but failed its frozen response-conformance gate, so its null metrics are
retained as an ineligible capability outcome rather than hidden or rerun.

The complete evidence, recalculation, integrity, privacy, and reproducibility
review is recorded in
[`power-benchmark-1.0-f5-device-verification.md`](power-benchmark-1.0-f5-device-verification.md).

### F6 — Governance and publication

Next.

- Freeze the submission bundle and contributor declarations.
- Define acceptance, review, reproduction, correction, withdrawal,
  deprecation, and release-history rules.
- Produce Power Benchmark 1.0 RC1 for review.
- Publish and tag 1.0 only after explicit maintainer approval.

## Power Benchmark 1.0 Release Gate

Power Benchmark 1.0 is publishable only when all of the following are true:

- the release contains exactly the two frozen candidate workload IDs;
- protocol text has no unresolved normative ambiguity for an official metric;
- the immutable release manifest pins every execution and validation identity;
- the result schema and semantic validator are frozen and tested together;
- the reference App emits that exact contract and rejects incompatible plans;
- required raw evidence can independently reproduce every ranked metric;
- failures, cancellations, OOMs, early stops, and not-run attempts have a
  frozen taxonomy and are never silently discarded;
- validation, evidence level, reproduction, and ranking eligibility are
  separate explicit decisions;
- the declared physical-device verification matrix is complete and contains
  no fabricated or placeholder measurement;
- submission, review, correction, withdrawal, deprecation, and release-history
  documentation is complete;
- known limitations and unsupported claims are published; and
- the final package passes integrity, privacy, documentation, validator, App,
  and reproducibility review.

Until every gate passes, repository results and the interactive leaderboard
remain explicitly non-official evidence.

## Change Control

Foundation changes must be incremental and reviewable. They may clarify or
version contracts, but they must not silently reinterpret historical evidence.
Any material change to a workload prompt, generation rule, timing boundary,
metric formula, eligibility decision, or execution procedure requires a new
version while preserving the existing workload ID and migration history.
