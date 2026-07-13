# Suite B Protocol v2

## Status

The v2 architecture remains a design umbrella. The two Power 1.0 candidate
workloads now have a frozen F2 execution contract in
[`power-1.0-protocol.md`](power-1.0-protocol.md) and explicit
[`migration rules`](power-1.0-migration.md). Neither document authorizes
official results; the F3 schema and validator are still required.

## Benchmark Question

For a pinned model artifact, runtime, and iPhone, how responsive, fast,
memory-efficient, and stable is local inference under a versioned workload?

## Workload Categories

### User-experience workloads

These begin with canonical text and report both pipeline and user-visible
boundaries when the adapter can observe them.

| ID | Scenario | Input target | Output policy | Primary view |
| --- | --- | --- | --- | --- |
| `b-ux-001-short-interaction` | Short in-app request with a concise response | 64-256 actual model-input tokens | Natural stop, maximum 128 tokens | Responsiveness |
| `b-ux-002-context-assistance` | Ask for a concise answer from a fixed local document | 1,024 or 2,048 actual model-input tokens | Natural stop, maximum 128 tokens | Context processing |

The `b-ux-001-short-interaction@0.2.0-pilot` prompt, response requirement,
generation settings, and visible-content policy are frozen as a validated
non-official pilot. Its post-chat-template token count, thinking-mode setting,
first-renderable-content boundary, and natural-stop behavior were checked on
the pinned reference adapter and a physical iPhone 14 Pro Max. The private
device result was not added to the repository.

For this candidate, Qwen3 thinking is explicitly disabled through the chat
template. User-visible TTFT begins when the App accepts the canonical request
and ends when cumulative raw-token decoding, with special tokens skipped,
first produces non-whitespace content that is available to the render path.
An adapter that cannot observe and prove that boundary reports the metric as
`null`; it must not substitute Pipeline TTFT.

#### First-renderable proxy TTFT evidence

Foundation adapter policy `first-renderable-decoded-prefix-v1` makes this
proxy independently recalculable without retaining a full per-token text
trace:

1. `adapter-request-accepted` is the monotonic-clock origin.
2. The adapter records generation start relative to that origin. Existing raw
   token events remain relative to generation start.
3. Beginning with raw token event zero, the adapter cumulatively decodes the
   observed token IDs with special tokens skipped. For each evaluated prefix,
   it records token index and ID, request-relative token receipt, decoded
   prefix, request-relative decode completion, and the renderability decision.
4. A prefix is renderable when it contains a Unicode scalar outside this
   frozen whitespace set: `U+0009...U+000D`, `U+0020`, `U+0085`, `U+00A0`,
   `U+1680`, `U+2000...U+200A`, `U+2028...U+2029`, `U+202F`, `U+205F`, and
   `U+3000`. This preserves the reference App's Foundation
   `whitespacesAndNewlines` behavior while giving non-Swift validators an
   explicit cross-language rule.
5. The proxy ends at decode completion for the first renderable prefix. That
   inclusive entry is retained and no later prefix is evaluated or stored.
6. At most 32 prefix entries are evaluated and retained. If the generation
   continues beyond 32 non-renderable prefixes, the trace outcome is
   `captureLimitReached` and the proxy TTFT is `null`. If generation ends
   within the retained prefix without renderable content, the outcome is
   `noRenderableContent` and the metric is also `null`.

The trace and raw token events use the same monotonic clock. A validator must
check token identity and the relation
`request-relative receipt = generation start + token-event elapsed`, recompute
each renderability decision from the decoded prefix, and derive the metric
from the first qualifying entry. A submitted aggregate or final output string
is not a substitute for this evidence.

This bounded trace is intentionally scoped to the first-renderable boundary.
It avoids repeated cumulative decoding and prefix storage after the metric is
known, while the 32-entry cap bounds the exceptional no-content path. It does
not observe SwiftUI rendering, display presentation, or human perception and
must never be labeled screen-visible TTFT.

### Pipeline profiles

These intentionally isolate or stress inference behavior. They must not be
presented as ordinary app-user scenarios.

| ID | Profile | Controlled variable | Primary view |
| --- | --- | --- | --- |
| `b-pipe-001-sustained-generation` | Repeated long generation from a fixed prompt | Five consecutive 512-token-limit attempts | Decode and thermal degradation |
| `b-pipe-002-input-length-sweep` | Fixed generation across token-exact inputs | 32, 128, 512, and 2,048 input tokens | Prefill and TTFT scaling |

The Input Length Sweep first performs an unmeasured fixture-calibration step.
The pinned tokenizer and chat template prepare deterministic candidate text,
and the adapter reads `LMInput.text.tokens.size` before generation. A point is
accepted only when that value exactly matches its target. Calibration does not
warm up through inference, does not produce a performance result, and blocks
measurement if any target is unavailable; nearest-length substitution is not
permitted.

The legacy `suite-b-pilot-001` runner has been frozen as
`b-pipe-001-sustained-generation@0.2.0-pilot`. The fixed prompt, deterministic
generation settings, one-warm-up plus five-measured procedure, no-rest order,
fresh KV cache per attempt, metric formulas, and raw evidence requirements are
versioned together. It remains non-official and five measured runs must not be
presented as a complete thermal-stability characterization.

## Standard Session Rules

The Benchmark App loads the four current workload execution identities from
the versioned plan registry. Foundation App 0.7.0 evidence is written using
the non-official `suite-b-result-bundle-0.4`; the common `sessions` array
contains one entry for a single-session workload or one entry per token-exact
point.
Workload-specific quality evidence is optional inside the common attempt shape
and does not change the timing formulas.

Unless a workload declares a stricter compatible mode:

1. verify the exact revision manifest and required cached artifact files;
2. if preparation downloads model files, require a full App restart before measurement;
3. after relaunch, verify the cache again and load without inference;
4. begin only when the system thermal state is `nominal`;
5. use a Release build with no debugger attached;
6. require battery power (`unplugged`), at least 50% starting charge, and Low
   Power Mode off; record battery level and charging state;
7. load model weights once per session;
8. run one unrecorded warm-up with the same configuration;
9. run five measured attempts;
10. create a new conversation and KV cache for every attempt;
11. retain loaded weights and tokenizer resources between attempts;
12. retain every failed, cancelled, OOM, early-stop, and not-run attempt;
13. perform no automatic retry; and
14. use the median of successful eligible measured attempts, requiring at
    least three.

No rest interval is used for sustained-generation profiles. User-experience
workloads may require independent nominal-start sessions when the purpose is
cold perceived responsiveness rather than thermal endurance.

## Generation Configuration

Every result records:

- sampling enabled;
- temperature, top-p, top-k, and seed, including explicit `null` values;
- repetition penalty when supported;
- maximum output tokens;
- model EOS and explicit stop sequences;
- reasoning or thinking mode;
- chat-template identity; and
- whether stop tokens are included in raw token evidence.

The reference deterministic mode uses greedy decoding (`temperature = 0`). A
runtime that cannot express a required setting is incompatible with that
workload version; it must not silently substitute another behavior.

## Cache Rules

Model weights remain resident after loading. Prompt and decoded-output KV cache
must not cross attempt boundaries. Tokenizer and compiled-kernel caches may
remain warm after the declared warm-up. Adapters record whether each rule was
verified, assumed, or unavailable.

## Environment Eligibility

A result bundle may be structurally valid but ineligible for a particular view.
Eligibility is stored as decisions with machine-readable reason codes.

Default reasons include:

- `pilot_protocol_not_official`
- `debugger_attached`
- `non_release_build`
- `low_power_mode_enabled`
- `initial_thermal_state_not_nominal`
- `incomplete_attempt_records`
- `insufficient_successful_measured_runs`
- `measurement_boundary_unverified`
- `workload_hash_mismatch`
- `runtime_configuration_incomplete`

Thermal transition during a sustained run is evidence, not a reason to discard
completed attempts. A critical state prevents later attempts and those planned
attempts remain as `notRun` records.

## Result Views

Suite B has no global score. Compatible results may be viewed by:

- workload and workload version;
- physical device model;
- model name, with artifact and quantization as supporting identity;
- runtime and runtime version;
- metric definition version; and
- trust level.

The default public presentation is model-first. Pipeline curves and raw
configuration belong in engineering and evidence views.
