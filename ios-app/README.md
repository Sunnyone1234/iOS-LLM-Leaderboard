# Power Benchmark Reference App

This directory contains the reference iPhone runner for the Power Benchmark.
It is benchmark data-collection infrastructure, not a starter application or
an inference framework.

## Current status

App `0.8.0` build `10` is the F4 reference-App candidate for
`suite-b-power@1.0.0-rc.1`.

It emits the frozen F3 result contract
`suite-b-power-result-1.0.0-rc.1`, but the benchmark release is still a release
candidate. Every export sets `officialResultEligible` to `false`. F5 physical
device verification, independent evidence review, ranking authorization, and
publication have not started.

## Frozen execution scope

The production control surface exposes exactly two workload identities:

- `b-ux-001-short-interaction@1.0.0-rc.1`;
- `b-pipe-001-sustained-generation@1.0.0-rc.1`.

The loader rejects any other plan identity or version. Experimental
`b-pipe-002-input-length-sweep` and `b-ux-002-context-assistance` resources are
retained for repository history and compatibility, but App 0.8.0 cannot
execute them through its production controls.

The selectable model artifacts remain the three pinned Qwen3 profiles already
declared by the Foundation:

- `mlx-community/Qwen3-0.6B-4bit`;
- `mlx-community/Qwen3-1.7B-4bit`;
- `mlx-community/Qwen3-4B-3bit`.

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

During the release-candidate stage, a conforming result is expected to be
`validWithWarnings`: evidence remains unreviewed and ranking remains
unauthorized until later release gates.

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

Build and test commands used for F4 are:

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

## Known F4 boundaries

- F4 does not produce or approve physical-device benchmark results; that is
  F5.
- MLX Swift LM is the only reference runtime adapter in this candidate.
- First-renderable proxy TTFT is a bounded adapter/decode measurement, not a
  screen-render timestamp or a claim of user-visible latency.
- Five no-rest measured generations expose observed degradation and thermal
  transitions; they do not establish complete thermal stability or battery
  efficiency.
- Jetsam or other unexplained process loss is preserved conservatively as
  unclassified failure unless trusted evidence identifies OOM.
- Submission review, reproduction, governance, and publication remain F6
  work.

Historical App 0.6.0/0.7.0 bundle formats remain supported by historical
ingestion and validation paths, but they are not the default App 0.8.0 export
and cannot be promoted into Power 1.0 evidence.
