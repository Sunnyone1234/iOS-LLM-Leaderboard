# Official iOS Benchmark App

This directory is reserved for the official community benchmark app.

The app is data-collection infrastructure for iOS-LLM-Leaderboard. It is not a
starter app for developers to copy into unrelated products.

## Purpose

The app should allow an iOS developer to:

1. install the official runner on a physical device;
2. select a compatible model profile and benchmark release;
3. run a locked, reproducible procedure;
4. review local results and every field proposed for submission;
5. submit a result bundle with minimal manual work.

The project cannot depend on one maintainer owning every iPhone and iPad model.
The app is the intended path for community device coverage.

## MVP Scope

- physical iPhone support first;
- automatic public device and OS metadata;
- versioned model profiles;
- MLX Swift as the first runtime adapter;
- local benchmark execution with no network dependency during measured phases;
- progress, cancellation, and failure reporting;
- summary and raw-run result export;
- contributor review before upload;
- local use without mandatory submission.

## Intended Submission Flow

1. The app exports a versioned result bundle.
2. A submission service or GitHub App validates the upload.
3. A pull request or bot-managed repository submission is created.
4. Repository automation performs structural and semantic checks.
5. The result enters the appropriate evidence level.

The app must not write directly to the default branch.

## Data Boundary

Expected benchmark metadata:

- public device model and chip;
- OS version and build;
- benchmark app and release version;
- model artifact, quantization, and runtime identity;
- inference settings;
- timing, token, memory, thermal, and failure evidence;
- integrity hash.

The app should not collect Apple ID, serial number, UDID, personal prompts,
user documents, or unrelated app data.

## Architecture Direction

The runner should use a runtime adapter boundary so that benchmark semantics do
not depend on MLX Swift.

Later adapters may support:

- llama.cpp;
- Core ML;
- Apple Foundation Models where equivalent measurements are possible;
- future Apple-platform runtimes.

## Current Implementation

The repository now includes a minimal SwiftUI Xcode project targeting iPhone
on iOS 26 or later. It provides:

- separate Prepare Model and Run Benchmark operations for the locked plan;
- public device, OS, and thermal-state inspection;
- a runtime-neutral `LanguageModelRuntime` boundary;
- a runner that executes one warm-up followed by five measured attempts; and
- unit tests proving that warm-up and failed attempts remain distinguishable.

Prepare Model obtains the pinned revision manifest, verifies every required
MLX model/tokenizer file in the revision-specific Hugging Face cache, downloads
missing files when necessary, and loads the model without inference. If that
App session downloads model files, measurement remains disabled until the user
fully closes and relaunches the App, then prepares the cached model again. A
manifest or cache verification failure produces `unknown` and never silently
admits a measurement. The App does not generate simulated measurements and
does not upload results.

The current runner calculates TTFT, MLX-reported prefill throughput, decode
throughput, token-interval percentiles, sampled process physical footprint, and
thermal state. It preserves warm-up and measured token events in a local pilot
bundle, shows median measured-run values, and exports the raw JSON through the
system share sheet.

The result view also shows first-to-last performance degradation and expandable
details for every measured attempt. Warm-up evidence is displayed separately
and remains excluded from summary aggregation. The on-screen thermal state is
refreshed after a run and on pull-to-refresh instead of remaining at its
launch-time value. A run can start only from the system-reported `nominal`
state. If the state reaches `critical`, the current generation is retained and
remaining generations are recorded as `notRun` instead of being started.

App version `0.6.0` build `8` exposes two directly selectable pilot workloads
and exactly three fixed model profiles: Qwen3 0.6B 4-bit, Qwen3 1.7B 4-bit,
and Qwen3 4B 3-bit. Selecting a workload or model clears prior preparation and
result state, so the exact artifact must be prepared again with that workload's
generation and measurement plan before Run Benchmark is enabled. The App
rejects a run when either identity is outside the fixed Pilot registry.

The App exports raw bundle schema
`suite-b-result-bundle-0.3`. The additive model identity records the exact
artifact source, revision, tokenizer identity, repository size, license source,
and compatibility constraints. The Pilot ingestion path retains support for
the genuine App 0.5.0 build 7 schema-0.2 Stage 1 evidence. The envelope uses the
same envelope for B-PIPE-001, B-PIPE-002, B-UX-001, and B-UX-002 and records
model-preparation evidence
alongside the frozen non-official B-PIPE-001 workload identity, Pipeline TTFT
boundary, generation and cache configuration, underlying
MLX dependency identity, battery state, and Low Power Mode. It also records
separate decisions for
session validity, cold performance, sustained performance, thermal stability,
and official leaderboard eligibility. A transition from `nominal` through
`fair` to `serious` is valid thermal evidence; it is not filtered out for
being slower. Official eligibility remains false while the protocol is a
non-official pilot.

The bundled `suite-b-plan-registry-0.2` is the execution source of truth for
workload identity, runner kind, run counts, output limit, token-exact points,
fixture hashes, thinking mode, and availability of the First-renderable proxy
TTFT. Legacy
bundle schemas remain validator-compatible but are no longer the default App
export.

B-PIPE-002 and B-UX-002 remain visibly labeled Experimental and non-official in
the App. They are not part of the two-workload Power + Ship Pilot v0.1 release
path.

App admission requires `unplugged` battery power, at least 50% charge at the
start of each measured workload, Low Power Mode off, and nominal thermal state.
Charging, full/external power, unknown power state, unknown battery level, or a
starting level below 50% blocks measurement with explicit reason codes.

After reviewing a completed result, a contributor can enter a public name or
GitHub handle, confirm the privacy and license declarations, and export
`suite-b-community-submission-0.1`. The package embeds the exact result bytes
and SHA-256 digest, remains Draft, and performs no network upload.

The bundle is written after the complete session, not after each individual
attempt. Per-attempt checkpoint recovery and Framework v1 repository export
remain follow-up MVP steps, so this build must not yet be used to publish
official results.

Open `BenchmarkApp.xcodeproj` in Xcode, select an Apple Development team, and
choose a physical iPhone. The first pilot environment is an iPhone 14 Pro Max
running iOS 26.5 with Xcode 26.5 (17F42).

### Measurement preflight

Run the benchmark without LLDB attached: open **Product → Scheme → Edit
Scheme → Run → Info**, turn off **Debug executable**, and then run the app on
the physical iPhone. The app detects an attached debugger, disables the Run
button, and explains how to detach it. This avoids an Xcode 26.5 debugger
detach failure observed after MLX/Metal inference; launching and stopping the
same app without inference does not reproduce that failure.

Exported pilot bundles record whether a debugger was attached, the Debug or
Release build configuration, Low Power Mode, battery level and charging state,
and the app version and build. The current runner requires a Release build,
detached debugger, Low Power Mode off, and a `nominal` thermal state before it
enables measurement.

The Run button additionally requires successful preparation from an already
complete cache in the current App session. It never downloads or loads the
model. Prepare Model performs no warm-up or measured generation; Run Benchmark
performs the one warm-up and five measured attempts.

B-PIPE-001 reports Pipeline TTFT: MLX chat-template application and tokenization
complete before its monotonic generation clock starts. It does not report or
infer screen-visible TTFT. B-UX-001 retains the historical
`userVisibleTTFTMilliseconds` field, but Pilot v0.1 labels it **First-renderable
proxy TTFT**: it starts at adapter request acceptance and ends when cumulative
decoding first produces non-whitespace content. It is not measured at the
screen. Pipeline TTFT remains a separate diagnostic measurement.

Release builds may inject the exact source revision with the
`GIT_COMMIT_SHA=<40-character-commit>` Xcode build setting. If that value is not
provided, the exported `appSourceCommit` remains `null`; the App never guesses a
revision.

## Current MVP Design

The first physical-iPhone harness pilot is specified in
[MVP-BENCHMARK-SPEC.md](MVP-BENCHMARK-SPEC.md). Its machine-readable plan,
fixed workload, and placeholder export fixture live under `benchmark-plans/`,
`workloads/`, and `fixtures/` respectively.

These files freeze an implementation target; they do not contain benchmark
results and do not make the draft pilot eligible for a leaderboard.

The pilot maps to the draft
`b-pipe-001-sustained-generation` profile in the
[Suite B Protocol v2](../benchmarks/suite-b-on-device-performance/protocol-v2.md).
It must not be presented as the short-interaction user-experience workload.
