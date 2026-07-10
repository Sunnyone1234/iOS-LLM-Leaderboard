# Benchmark Harness MVP Specification

## Status

This document freezes the first harness pilot closely enough to implement and
test the runner. It is not an official benchmark release. Results produced by
this pilot are not eligible for an official leaderboard.

### Measurement Foundation Phase 1 Closure

The measurement-foundation phase was accepted on 2026-07-11. The accepted
baseline separates model preparation from performance measurement and has
been exercised on a physical iPhone with a locally retained 0.5 result bundle.
That private device result passed the repository validator and was not added
to the repository.

The closure covers:

- revision-specific cache verification before model loading;
- a mandatory process restart after any download;
- a local-only preparation pass before measurement admission;
- plan-driven model, prompt, runtime, generation, and run-count identity;
- one warm-up followed by five independent measured attempts;
- raw token-event, environment, preparation, eligibility, and summary evidence;
- recalculation and validation of supported metrics from the raw bundle; and
- backward-compatible validation of the earlier pilot bundle versions.

This closure does not make the pilot official and does not freeze a user
experience workload. `b-ux-001-short-interaction`, user-visible TTFT, further
pipeline profiles, community submission, and leaderboard presentation remain
later work.

The machine-readable plan is
`ios-app/benchmark-plans/suite-b-pilot-001.json`.

## Scope

The pilot validates one physical-iPhone path:

1. verify the complete pinned artifact revision in the Hugging Face cache;
2. download and load it during Prepare Model when necessary;
3. require a relaunch after any model download;
4. prepare and load the verified cached model without inference;
5. run one unrecorded warm-up and five measured generations;
6. retain every attempt, including failures and cancellation;
7. save raw event, preparation, and environment evidence locally; and
8. export a reviewable non-official pilot result bundle.

Prepare Model and Run Benchmark are separate operations. Model preparation
never emits performance evidence, and the benchmark path never downloads or
loads a model.

The pilot is decode-oriented. Decode throughput is its primary metric. TTFT,
prefill throughput, sampled process memory, thermal state, and token intervals
are secondary observations from the same run. It does not combine Suite B
tasks into a score.

Under the Suite B v2 design, this pilot maps to the draft
`b-pipe-001-sustained-generation` pipeline profile. It is not a
short-interaction user-experience workload.

## Reproducibility Identity

A run is invalid unless its evidence records:

- plan ID and version;
- prompt content hash;
- model artifact ID and immutable revision;
- downloaded artifact content hash;
- tokenizer and chat-template identity;
- MLX Swift LM package version and resolved commit;
- app version, build number, and source commit;
- public device model identifier;
- iOS version and build; and
- generation, cache, and run-count settings.

The artifact content hash remains `null` in the plan until the downloader has
materialized and verified the complete artifact. It must not be guessed.

## Model Preparation Admission

Cache verification retrieves the file manifest for the exact 40-character
artifact revision and filters the same `*.safetensors`, `*.json`, and `*.jinja`
files required by the pinned MLX loader. Every required revision-specific
cache path must exist and match the manifest file size. This is recorded as
`huggingface_revision_manifest_cached_file_size_v1`.

If the manifest cannot be retrieved or the cache cannot be inspected, cache
state is `unknown` and measurement is blocked. A missing snapshot directory,
one matching file, elapsed download time, or successful model load is not by
itself treated as proof of a complete cache.

If preparation downloads any model file, the App records the download and
requires a full process restart. After relaunch, the user runs Prepare Model
again; only a complete cache verified before preparation and a successful
local-only model load admit performance measurement.

## Timing Events

All durations use a monotonic clock. Wall-clock timestamps may be recorded for
audit purposes but must not be used to calculate performance metrics.

Each attempt can emit these ordered events:

| Event | Required | Meaning |
| --- | --- | --- |
| `attempt_started` | yes | Runner begins the attempt. |
| `prompt_submitted` | yes | Prepared input is submitted for evaluation. |
| `prefill_started` | when exposed | Runtime begins prompt evaluation. |
| `prefill_completed` | when exposed | Runtime completes prompt evaluation. |
| `token_generated` | once per generated token | Runtime reports a generated token. |
| `generation_completed` | on success | A documented stop condition is reached. |
| `attempt_failed` | on failure | Attempt ends with an error. |
| `attempt_cancelled` | on cancellation | User or system cancellation ends the attempt. |

Every event includes an attempt-relative monotonic duration. Token events also
include a zero-based generated-token index. Raw token text is optional and
must be excluded if it could contain private input; this pilot uses only the
repository-owned fixed prompt.

## Metric Boundaries

- Pipeline TTFT starts after MLX has applied its processor, chat template, and
  tokenizer and immediately before `generateTokensTask`; it ends when the
  adapter receives the first raw token. Tokenization is therefore excluded.
- User-visible TTFT is unavailable in this pilot and must remain `null` rather
  than being inferred from the first raw token.
- Prefill duration uses explicit runtime prefill boundaries when available.
  If MLX Swift LM does not expose a reliable boundary, the value is `null` and
  the limitation is recorded. TTFT must not be relabeled as prefill time.
- Decode duration starts at the first generated token and ends at the final
  generated token. Decode throughput excludes the first token from its token
  numerator. A run with fewer than two generated tokens has no decode value.
- Token intervals are the differences between consecutive token events.
- Peak memory is the maximum sampled current-process physical footprint within
  the documented measurement window. The sampling interval is stored with the
  run.
- Thermal state is captured before warm-up, before and after every measured
  attempt, and after the sequence. It is a system-reported category, not a
  temperature measurement.

## Attempt and Failure Rules

Warm-up uses the same prompt and generation settings as measured runs but is
never included in aggregation. The model is loaded once before warm-up. Every
generation receives a new conversation context and cache.

Every planned measured attempt gets a record. Failed, cancelled, early-EOS,
and out-of-memory attempts are retained. A reason may make a run ineligible
for a metric, but the record is never deleted. The summary uses the median of
successful eligible measured runs and requires at least three such runs.

No automatic retry is allowed in this pilot. A user can start a new benchmark
session, which receives a new result ID.

The app admits a new session only when `ProcessInfo.thermalState` is `nominal`.
The user may refresh that preflight value manually. If the state is `critical`
at an attempt boundary, the runner does not start that attempt or any later
attempt; each remaining planned attempt is retained with a `notRun` outcome
and a machine-readable reason. The runner does not discard a completed run
because its state changed to `fair` or `serious`: that transition is thermal
evidence, not grounds for selecting a more favorable result.

Local raw bundles report independent eligibility decisions for session
validity, cold performance, sustained performance, and thermal stability.
These decisions do not override the pilot's fixed ineligibility for the
official leaderboard.

The current app also requires a Release build, no attached debugger, and Low
Power Mode off. It records battery level and charging state as environment
evidence; charging is recorded rather than automatically treated as a pass or
failure during this pilot.

## Raw Run Record

Each raw attempt record contains:

- run index and `warmup` or `measured` role;
- actual prompt and output token counts;
- ordered raw token IDs, indices, and attempt-relative monotonic timestamps;
- derived metrics, with unavailable values represented by `null`;
- peak sampled process physical footprint and the 50 ms sampling interval;
- thermal state before and after the attempt;
- stop reason;
- success, failure, or cancellation status; and
- a non-sensitive error message when an attempt fails.

Full attempt start/end events, raw memory samples, timestamped thermal-change
events, structured error stages, and checkpoint recovery remain future work.
The exported `appSourceCommit` also remains `null` until the Xcode build injects
`GIT_COMMIT_SHA`; the pilot must not guess it.

Errors are data. The app must not convert a failed attempt into a zero-valued
performance metric.

## Framework v1 Repository Export

The App currently exports its pilot bundle, not a repository-ready Framework v1
result. A future repository export may use
`methodology/benchmark-result-specification.md`. Until an official pilot task
is activated, placeholder fixtures use `provenance.source` set to
`demo-placeholder` and contain no numeric measurements.

For a real local pilot run:

- `execution.run_type` is `app-export`;
- `provenance.source` is `benchmark-app`;
- aggregate values map to the top-level `metrics` object;
- per-run compatible values map to
  `suite_b_measurement.per_run_metrics`;
- the complete raw attempt bundle is referenced from
  `provenance.raw_artifact_paths`; and
- notes state that the run is a non-official pilot.

Framework v1 currently requires `evaluation.score` and `evaluation.passed` for
non-placeholder results, even though Suite B performance is not a score. The
harness must not invent these values. Before exporting a real repository-ready
result, the schema and validator need a documented measurement-only handling
rule. Local raw bundles may still be generated before that compatibility issue
is resolved.

## Privacy Boundary

The harness records only public device characteristics and benchmark evidence.
It must not record Apple ID, serial number, UDID, personal prompts, user files,
or unrelated device data.
