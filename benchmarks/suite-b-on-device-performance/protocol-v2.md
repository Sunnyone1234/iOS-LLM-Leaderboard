# Suite B Protocol v2

## Status

Design draft. This protocol does not yet authorize official results.

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

Prompt content and hashes are not frozen yet. A workload cannot become active
until its redistributable fixture, prompt, tokenizer output, and expected stop
behavior are checked on the reference adapter.

### Pipeline profiles

These intentionally isolate or stress inference behavior. They must not be
presented as ordinary app-user scenarios.

| ID | Profile | Controlled variable | Primary view |
| --- | --- | --- | --- |
| `b-pipe-001-sustained-generation` | Repeated long generation from a fixed prompt | Five consecutive 512-token-limit attempts | Decode and thermal degradation |
| `b-pipe-002-input-length-sweep` | Fixed generation across token-exact inputs | 32, 128, 512, and 2,048 input tokens | Prefill and TTFT scaling |

The current `suite-b-pilot-001` maps only to the draft sustained-generation
profile. Its successful real-device run validates instrumentation; it does not
freeze the final workload.

## Standard Session Rules

Unless a workload declares a stricter compatible mode:

1. verify the exact revision manifest and required cached artifact files;
2. if preparation downloads model files, require a full App restart before measurement;
3. after relaunch, verify the cache again and load without inference;
4. begin only when the system thermal state is `nominal`;
5. use a Release build with no debugger attached;
6. record Low Power Mode, battery level, and charging state;
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
