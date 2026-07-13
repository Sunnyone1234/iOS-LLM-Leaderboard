# Suite B Power Benchmark 1.0 Protocol

## Status and scope

Protocol `suite-b-power@1.0.0-rc.1` is the frozen F2 release-candidate
execution contract. It does not authorize official results or a 1.0 release.
The machine-readable companion is
[`power-1.0-protocol.json`](power-1.0-protocol.json).

Exactly two existing workload IDs are in scope:

| Workload execution identity | Role |
| --- | --- |
| `b-ux-001-short-interaction@1.0.0-rc.1` | warm-resident short-interaction responsiveness |
| `b-pipe-001-sustained-generation@1.0.0-rc.1` | sustained pipeline generation and thermal-transition evidence |

`b-pipe-002-input-length-sweep` and `b-ux-002-context-assistance` remain
Experimental. Suite IDs, workload IDs, and historical files are unchanged.

Normative requirements use **must**. A field that is unavailable or
metric-ineligible must be `null`; zero, an empty string, a fabricated event,
or a value copied from another boundary is never a substitute.

## Common execution contract

Each workload session must:

1. use a physical iPhone, a Release build, no attached debugger, Low Power
   Mode off, battery power, at least 50% starting charge, and a `nominal`
   session-start thermal state;
2. verify the pinned model revision and fixture bytes before measurement;
3. perform no model download during the measurement session;
4. load model weights once, then execute one warm-up attempt followed by five
   measured attempts in indices `0...5`;
5. keep the loaded weights, tokenizer, and compiled-kernel caches resident,
   while creating a fresh conversation and KV cache for every attempt;
6. use the pinned generation configuration and perform no automatic retry,
   substitution, outlier deletion, or imputation;
7. insert no rest interval between attempts; and
8. retain one record for every planned attempt, including failed, cancelled,
   out-of-memory, and not-run attempts.

The warm-up is evidence but is excluded from every published aggregate. A
session that fails an admission requirement is retained and validation may
succeed structurally, but it is ranking-ineligible.

## Workload contracts

### Short Interaction

The fixture SHA-256 is
`69b3cd45fb67e1882dabdc082636298123e01081c097af65b3fd133b19ccbc84`.
The model input is produced with the pinned tokenizer and chat template,
including special tokens, with Qwen3 thinking disabled. Its actual post-template
token count must be between 64 and 256 inclusive. Greedy generation stops at
model EOS or 128 generated tokens, whichever occurs first. Stop tokens are not
included in raw token events.

The generated response must retain the existing workload behavior: no more
than two sentences, state that the note is safe on this iPhone, and state that
it will sync when connectivity returns. Response conformance is a workload
eligibility gate, not a performance metric. F4 must make that decision
reviewable; until then, Foundation App exports cannot become 1.0 results.

`short-interaction-response-v1` makes that existing requirement deterministic.
The validator normalizes the retained generated text with Unicode NFKC,
case-folds it, and collapses whitespace. It counts each nonempty segment ended
by `.`, `!`, or `?`, plus a nonempty trailing segment, as one sentence. The
normalized response must be nonempty and contain at most two sentences. The
local-safety claim requires substring `safe` and at least one of `iphone`,
`device`, or `local`. The sync-return claim requires substring `sync`, at least
one of `connect`, `network`, or `online`, and at least one of `return`,
`restore`, `available`, `back`, or `again`. These are substring checks on the
normalized text. All Short Interaction ranked metrics require this gate to
pass, and the exact generated text must be retained for review.

The first-renderable proxy starts when the App accepts the canonical request
and ends when cumulative raw-token decoding first completes a prefix containing
a Unicode scalar outside the whitespace set frozen in `protocol-v2.md`. The
bounded `first-renderable-decoded-prefix-v1` trace is normative. The metric is
not screen presentation time and must never be labeled screen-visible or
human-perceived TTFT.

### Sustained Generation

The fixture SHA-256 is
`b865ad1a1993bfd7bf097b85f7c5585e44f1384fa291b9c05426c6051caba996`.
The pinned prompt directive disables thinking. Greedy generation stops at
model EOS or 512 generated tokens. Stop tokens are not included in raw token
events. Every attempt remains usable for metrics supported by its evidence;
an earlier model EOS is recorded as a completed early stop and is not silently
converted into failure or a 512-token completion.

The five measured attempts are one no-rest sustained sequence. It supports a
first-to-last degradation signal and observed thermal transitions; it does
not support a claim of complete thermal stability or battery efficiency.

Generation settings are workload-specific and exact. Short Interaction uses
`top_p = 1`, `top_k = 0`, `seed = 0`, no repetition penalty, thinking disabled
through the chat-template context, and chat-template identity
`artifact-tokenizer-config-enable-thinking-false`. Sustained Generation uses
explicit `null` for `top_p`, `top_k`, `seed`, and repetition penalty, disables
thinking through the prompt directive, and uses chat-template identity
`artifact-tokenizer-config`. A runtime that cannot represent these settings is
incompatible; it must not silently substitute defaults.

## Clock and token evidence

All duration evidence must use one monotonic clock and integer nanoseconds.
Wall-clock timestamps identify the execution but must not calculate metrics.

- Pipeline TTFT starts immediately before invoking the runtime generation
  path with already prepared model input and ends when the adapter receives
  raw token event zero. Chat templating and tokenization are outside it.
- First-renderable proxy TTFT uses the request-acceptance origin and bounded
  trace described above.
- Request completion starts at request acceptance and ends after the runtime
  returns its final completion or stop information to the adapter.
- Prefill duration is the runtime-reported prompt-evaluation duration for the
  same attempt. A combined generation duration is not a substitute.

`promptTokenCount` is the exact post-chat-template model-input count, including
special tokens actually evaluated. `outputTokenCount` is the number of raw
generated token events after applying the pinned stop-token exclusion policy.
Raw events are zero-based, contiguous, ordered by nondecreasing elapsed time,
and their count must equal `outputTokenCount`. Decode requires at least two
events and a strictly positive first-to-last interval.

## Attempt outcomes and stop reasons

Each planned attempt has exactly one terminal outcome:

| Outcome | Meaning | Stop reason |
| --- | --- | --- |
| `completed` | runtime returned a valid completion record | required: `endOfSequence` or `outputTokenLimit` |
| `failed` | non-OOM runtime, adapter, or evidence error | `null` |
| `cancelled` | user or system cancellation was observed | `null` |
| `outOfMemory` | allocation failure, OS memory termination recovered from durable state, or runtime OOM classification | `null` |
| `notRun` | planned attempt was never started | `null` |

An early EOS is `completed` plus `endOfSequence`; it is not a separate outcome.
A cancellation reported as a runtime stop must be normalized to `cancelled`.
Unclassified process loss is `failed`, not OOM. A `notRun` record must state
why it did not start. After `critical` thermal state is observed before an
attempt, that attempt and all later planned attempts are `notRun` with
`thermal_state_critical_before_attempt`. No terminal record may be dropped or
retried.

Current Foundation App 0.7.0 distinguishes only completed, failed, and not-run
records. Full cancellation, OOM, and crash-safe recovery are explicitly F4
implementation requirements; this protocol does not claim they already exist.

## Memory and thermal boundaries

Process memory is sampled using `TASK_VM_INFO.phys_footprint` every 50 ms. The
attempt window starts immediately before runtime generation is invoked,
includes an initial sample, ends after generation returns or throws, and
includes one final sample after cancelling the sampler. The attempt peak is
the maximum retained sample divided by 1,048,576. It is process physical
footprint, not model-only memory, incremental memory, system-wide peak, or an
exact allocation high-water mark. Missing samples produce `null`.

Thermal state is the categorical `ProcessInfo.thermalState`. Record session
start and end, every attempt start and end, and timestamped transitions when
observable. A transition after an attempt begins is evidence and does not
invalidate that completed attempt. `unknown` remains evidence but makes the
thermal-transition view ineligible. No temperature is inferred.

## Metric eligibility

Eligibility is decided per attempt and per metric. An ineligible metric is
`null` in aggregates even when observational data is retained.

| Metric | Additional attempt requirements |
| --- | --- |
| Pipeline TTFT | completed; token event zero exists; generation boundary and monotonic clock verified |
| First-renderable proxy TTFT | Short Interaction only; completed; valid trace outcome `firstRenderableFound`; response conformant |
| Request completion | Short Interaction only; completed; request origin and completion event retained; response conformant |
| Prefill throughput | completed; exact prompt count; positive explicit prompt-evaluation duration |
| Decode throughput | completed; at least two raw events; positive first-to-last interval |
| Process physical footprint | completed; at least one valid in-window 50 ms sample |
| Decode first-to-last change | Sustained Generation only; first and last measured attempts are decode-eligible and all six planned records exist |
| Thermal-transition evidence | Sustained Generation only; all planned records exist and required states are not `unknown` |

Common disqualifiers include fixture or workload identity mismatch, unverified
artifact revision, incompatible runtime setting, failed environment admission,
missing attempt records, or contradictory raw evidence. Failed, cancelled,
OOM, and not-run attempts do not contribute performance values, but their
evidence and counts remain mandatory.

## Aggregation

Each ranked scalar is the median of that metric's eligible measured-attempt
values. At least three of the five measured attempts must be eligible for that
specific metric. Different metrics may therefore have different eligible-run
sets. No global session-valid flag may manufacture per-metric eligibility.

Median and token-interval percentiles use sorted values with position
`p × (n - 1)` and linear interpolation between adjacent values (R-7). Values
are calculated at full precision; rounding is presentation-only.

Decode first-to-last change is:

```text
(decode_last / decode_first - 1) × 100
```

using measured attempt order, not the fastest and slowest attempts. Negative
means slower. If either required attempt is ineligible, the value is `null`.
Thermal state remains categorical evidence and is never averaged or scored.

## Nulls, contradictions, and validation

- Missing, unavailable, nonfinite, or metric-ineligible values are `null`.
- Zero is valid only when the underlying quantity can genuinely be zero; no
  frozen duration or throughput metric permits zero.
- A submitted summary that disagrees with raw evidence is invalid, even if the
  raw evidence itself could produce an eligible value.
- Validator output must not rewrite the submitted result.
- Structural validity, protocol conformance, metric eligibility, evidence
  level, and ranking eligibility are separate decisions.

F3 freezes the schema, release manifest, reason-code registry, and semantic
validator that enforce this protocol.
