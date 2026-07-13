# Power Benchmark Reference App

This directory contains the reference iPhone runner for the Power Benchmark.
It is benchmark data-collection infrastructure, not a starter application or
an inference framework.

## Current status

App `0.9.0` build `11` is the current Power 1.0 community-testing App. It keeps
the adopted Power 1.0 workload, measurement, result, and validation contracts
unchanged while adding four explicitly untested model artifacts to the model
picker.

App `0.8.0` build `10` remains the exact reference source for the published
six-result Maintainer Reference matrix and for reproducing its three existing
Qwen comparison cells. App 0.9.0 must not be substituted when an exact
App-0.8.0 reproduction is intended.

Both versions emit the adopted source result contract
`suite-b-power-result-1.0.0-rc.1`. Every raw App export sets
`officialResultEligible` to `false`; acceptance into the separate live
community ranking occurs only after package validation, contributor review,
and merge. A picker entry is never evidence by itself.

## Frozen execution scope

The production control surface exposes exactly two workload identities:

- `b-ux-001-short-interaction@1.0.0-rc.1`;
- `b-pipe-001-sustained-generation@1.0.0-rc.1`.

The loader rejects any other plan identity or version. Experimental
`b-pipe-002-input-length-sweep` and `b-ux-002-context-assistance` resources are
retained for repository history and compatibility, but App 0.8.0 cannot
execute them through its production controls.

The three pinned Qwen3 profiles have Maintainer Reference evidence:

- `mlx-community/Qwen3-0.6B-4bit`;
- `mlx-community/Qwen3-1.7B-4bit`;
- `mlx-community/Qwen3-4B-3bit`.

App 0.9.0 also exposes four pinned candidates recommended for physical-iPhone
testing:

- `mlx-community/Llama-3.2-1B-Instruct-4bit`;
- `mlx-community/gemma-3-1b-it-qat-4bit`;
- `mlx-community/granite-3.3-2b-instruct-4bit`;
- `mlx-community/SmolLM3-3B-4bit`.

Their exact revisions, artifact sizes, licenses, runtime-registry basis, and
evidence state are recorded in
[`models/power-test-catalog.json`](../models/power-test-catalog.json). They are
marked `untested`: registration in the locked MLX Swift LM model factory does
not prove that an artifact loads, fits memory, completes a workload, or
performs well on a physical iPhone. Failed and OOM runs are useful evidence and
must be preserved.

Selecting a different workload or model clears preparation and result state.
The exact artifact must be prepared again before measurement is admitted.

## Measurement admission and procedure

The App admits a measurement only when all frozen conditions are satisfied:

- a physical iPhone is used;
- the App is a Release build with no debugger attached;
- Low Power Mode is off;
- the device is unplugged and has at least 50% charge;
- the session starts at nominal thermal state;
- the exact model revision is already cached, verified, and loaded; and
- no model download occurred in the current App session.

If preparation downloads files, fully close and relaunch the App, then prepare
the cached artifact again. The measured operation performs no download and no
model load. It executes one warm-up attempt followed by five measured attempts,
with no automatic retry or rest interval. Every attempt uses a fresh
conversation and fresh KV cache while model weights remain loaded.

Process physical footprint is sampled every 50 ms using
`TASK_VM_INFO.phys_footprint`. Thermal state comes from
`ProcessInfo.thermalState`. If an attempt begins at critical thermal state,
that attempt and every remaining planned attempt are retained as `notRun`.

## Evidence and terminal outcomes

Each exported result retains the raw evidence needed by the frozen validator:

- exact benchmark, workload, fixture, runner, model, runtime, device, OS, App,
  and source-commit identity;
- monotonic token events;
- prompt-evaluation and request-relative timing evidence;
- bounded cumulative-decoding evidence for First-renderable proxy TTFT;
- 50 ms physical-footprint samples;
- attempt boundary thermal states and observable transitions; and
- one warm-up plus five measured terminal records.

The runner distinguishes `completed`, `failed`, `cancelled`, `outOfMemory`,
and `notRun`. It classifies OOM only from an explicit trusted runtime failure
or `ENOMEM`; it never guesses that an unexplained process termination was an
OOM.

An atomic local checkpoint is written before each attempt and after each
terminal record. If the process ends mid-session, the next launch preserves
the active attempt as `failed/process_terminated_unclassified` and all
unstarted attempts as `notRun/prior_attempt_unrecoverable`. A completed
checkpoint remains recoverable until its frozen result JSON is saved. An
unresolved checkpoint cannot be overwritten by starting another run.

## Result export and validation

Results are written atomically under the App Documents directory in
`PowerBenchmarkResults/` and can be reviewed and shared locally. The App does
not upload results or write to the repository.

The source checkout commit is embedded automatically as a read-only resource
in the built App bundle. A valid 40-character lowercase commit is required
before the App will measure. This prevents an export from claiming an unknown
App revision.

Validate an exported file from the repository root with:

```sh
python3 scripts/validate_suite_b_power_result.py /path/to/result.json
```

A conforming raw result is expected to be `validWithWarnings`: evidence remains
unreviewed and ranking remains unauthorized until the contribution package is
reviewed and merged under the public-intake policy.

## Privacy boundary

The result contains public technical identity only: device machine identifier,
friendly device model, OS version/build, physical-memory capacity, and frozen
model/runtime/App metadata.

The App does not collect Apple ID, serial number, UDID, vendor identifier,
device name, account identity, personal prompts, user documents, or unrelated
App data. The only decoded text retained is output from a fixed benchmark
fixture where the frozen contract requires response or renderability evidence.

## Build and local verification

Open `BenchmarkApp.xcodeproj`, select an Apple Development team, choose a
physical iPhone, and use the Release configuration. In **Product → Scheme →
Edit Scheme → Run → Info**, turn off **Debug executable** before measuring.

A simulator can compile the App and run contract tests, but it is intentionally
rejected as benchmark evidence.

Build and test commands for the reference App are:

```sh
xcodebuild -project ios-app/BenchmarkApp.xcodeproj \
  -scheme BenchmarkApp \
  -sdk iphonesimulator \
  -destination 'generic/platform=iOS Simulator' \
  CODE_SIGNING_ALLOWED=NO build

xcodebuild -project ios-app/BenchmarkApp.xcodeproj \
  -scheme BenchmarkApp \
  -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' \
  CODE_SIGNING_ALLOWED=NO test
```

The contract tests encode both frozen workload shapes. Those Swift-produced
JSON files are also checked with the frozen F3 Python validator.

## Known boundaries

- MLX Swift LM is the only reference runtime adapter.
- First-renderable proxy TTFT is a bounded adapter/decode measurement, not a
  screen-render timestamp or a claim of user-visible latency.
- Five no-rest measured generations expose observed degradation and thermal
  transitions; they do not establish complete thermal stability or battery
  efficiency.
- Jetsam or other unexplained process loss is preserved conservatively as
  unclassified failure unless trusted evidence identifies OOM.
- App 0.9.0 candidate entries have no accepted physical-device evidence until
  contributors submit genuine exports through the public-intake process.

Historical App 0.6.0/0.7.0 bundle formats remain supported by historical
ingestion and validation paths, but they are not the current App 0.9.0 export
and cannot be promoted into Power 1.0 evidence.
