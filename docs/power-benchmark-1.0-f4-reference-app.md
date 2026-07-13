# Power Benchmark 1.0 F4 Reference App

## Status

F4 implementation candidate; awaiting dependent pull-request review.

This work hardens App `0.8.0` build `10` against the already frozen
`suite-b-power@1.0.0-rc.1` F2/F3 contract. It does not change the protocol,
schema, validator, release manifest, workload IDs, model matrix, or benchmark
architecture. It does not start F5 physical-device verification.

## Implemented contract boundary

The production App:

1. loads only the two release-candidate workload identities and rejects other
   plans or versions;
2. requires a physical iPhone and an embedded 40-character source commit;
3. exports `suite-b-power-result-1.0.0-rc.1` with ranking eligibility false;
4. retains raw token, timing, memory, renderability, and thermal evidence;
5. preserves completed, failed, cancelled, OOM, and not-run terminal records;
6. writes atomic per-attempt checkpoints and conservatively recovers process
   interruption without guessing OOM;
7. writes the final JSON atomically before deleting its checkpoint; and
8. keeps result inspection and sharing local, with no automatic upload.

Experimental registry resources remain in their historical paths, but their
calibration and execution gates are disabled in App 0.8.0 and they are absent
from the production interface.

## Recalculation evidence

For every completed attempt, the App retains:

- generation-relative token IDs, indices, and nanosecond receipt offsets;
- request-relative generation start and prompt-evaluation duration;
- B-UX-001 request completion and bounded cumulative-decoding trace;
- 50 ms `TASK_VM_INFO.phys_footprint` samples; and
- attempt boundary thermal states plus observable timestamped transitions.

Attempt and summary metrics are calculated from this evidence. The external F3
validator recalculates them independently. Non-completed attempts expose null
derived metrics and a frozen reason code.

## Recovery semantics

The checkpoint records the frozen plan, public execution environment, model
preparation evidence, session identity, attempt-start marker, and completed
terminal records.

On recovery:

- a recorded terminal outcome is retained unchanged;
- an active unrecorded attempt becomes
  `failed/process_terminated_unclassified`;
- an attempt that never started becomes
  `notRun/prior_attempt_unrecoverable`;
- exactly six ordered terminal records are exported; and
- the checkpoint is removed only after atomic result save succeeds; and
- a new run cannot overwrite an unresolved checkpoint.

This deliberately does not infer `outOfMemory` from an unexplained process
loss. Explicit runtime OOM classification or `ENOMEM` is required.

## Privacy review

The F4 result captures public technical metadata needed for comparison and
reproduction. It does not capture UDID, serial number, vendor identifier,
device name, Apple account identity, personal prompts, or unrelated files.

The only text evidence is generated from fixed benchmark fixtures and is
limited to fields required by the frozen B-UX-001 contract.

## Verification completed in F4

- generic iOS Simulator build succeeds;
- the full App XCTest suite succeeds;
- the built App bundle contains the exact checkout commit resource;
- Swift encoders produce both frozen workload result shapes, including a
  recovered mixed-terminal attempt sequence;
- both extracted JSON test artifacts pass the frozen F3 semantic validator
  with no structural or protocol errors; and
- ranking remains false with the expected release-candidate warnings.

The JSON artifacts used here are test-only synthetic contract fixtures. They
are not repository benchmark results, are not placed in a result directory,
and must never appear on the leaderboard.

## F5 handoff

F5 may now build this exact App revision on physical devices and collect new
release-candidate evidence without changing F2/F3/F4 contracts. F5 must verify
both workload identities, validate every exported JSON externally, review raw
metric recalculation and privacy, and retain all failures.

Any code, protocol, schema, plan, workload, model, or runtime change discovered
to be necessary during F5 returns to the appropriate earlier gate and requires
a new reviewed candidate. F5 must not silently patch evidence after a run.
