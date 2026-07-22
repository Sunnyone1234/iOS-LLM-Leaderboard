# Power Benchmark Reference App

This directory contains the reference iPhone runner for the Power Benchmark.
It is benchmark data-collection infrastructure, not a starter application or
an inference framework.

## Current status

App `0.18.0` build `21` separates measurement from result review and upload in
native Test and Results tabs. It checks the repository's SHA-256-bound current
compatibility policy at launch, foreground entry, and immediately before model
preparation, measurement, or submission. An unavailable policy or unapproved
current runner fails closed for new measurement; an unapproved selected result
fails closed for submission. Frozen local results remain reviewable and
shareable in every state. It retains the contributor-owned GitHub PR creation,
safe result recovery, and selectable local history introduced by earlier Apps
while retaining the draft
`short-interaction-response-v2` behavior preview. It retains the frozen Power
1.1 workload IDs, fixtures, measurement boundaries, generation settings,
attempt counts, and source-result schema identity. Its App version, build, and
source commit remain exact metadata and are not relabeled as the frozen
reference runner. Power 1.1 performance evidence remains governed by its
published validator and ranking policy until a later policy release is
explicitly approved.

App `0.13.0` build `16` remains the frozen reference runner adopted by Power
1.1. It always exports technically derivable measurements, and its local
response-conformance badge is advisory only. The final release independently
derives measured-performance and recommendation eligibility.

App `0.8.0` build `10` remains the exact reference source for the published
six-result Maintainer Reference matrix and for reproducing its three existing
Qwen comparison cells. App `0.9.0` build `11`, App `0.10.0` build `12`, App
`0.10.1` build `13`, and App `0.11.0` build `14` remain historical exact source
identities for Power 1.0 results created with them. App 0.13.0 must not be
substituted when an exact Power 1.0 reproduction is intended.

Apps 0.8.0 through 0.11.0 emit the adopted Power 1.0 source result contract
`suite-b-power-result-1.0.0-rc.1`. App 0.12.0 remains the historical Power 1.1
draft runner. Apps 0.13.0 through 0.18.0 emit
`suite-b-power-result-1.1.0-rc.1`. Every raw App export sets
`officialResultEligible` to `false`; no App export assigns its own publication,
trust, or ranking status. Repository validation and release policy do. A
picker entry is never evidence by itself.

## Power 1.1 execution scope

The production control surface exposes exactly two workload identities:

- `b-ux-001-short-interaction@1.1.0-rc.1`;
- `b-pipe-001-sustained-generation@1.1.0-rc.1`.

The loader rejects any other plan identity or version. Experimental
`b-pipe-002-input-length-sweep` and `b-ux-002-context-assistance` resources are
retained for repository history and compatibility, but App 0.18.0 cannot
execute them through its production controls.

The three pinned Qwen3 profiles have Maintainer Reference evidence:

- `mlx-community/Qwen3-0.6B-4bit`;
- `mlx-community/Qwen3-1.7B-4bit`;
- `mlx-community/Qwen3-4B-3bit`.

App 0.18.0 also exposes eight pinned artifacts with accepted single-contributor
physical-iPhone community evidence:

- `mlx-community/Llama-3.2-1B-Instruct-4bit`;
- `mlx-community/gemma-3-1b-it-qat-4bit`;
- `mlx-community/granite-3.3-2b-instruct-4bit`;
- `mlx-community/SmolLM3-3B-4bit`;
- `mlx-community/LFM2-1.2B-4bit`;
- `mlx-community/exaone-4.0-1.2b-4bit`;
- `mlx-community/bitnet-b1.58-2B-4T-4bit`;
- `mlx-community/Llama-3.2-3B-Instruct-4bit`.

Every picker entry pins its exact artifact revision, size, license, tokenizer,
and locked MLX Swift LM runtime requirements. Accepted measurements remain in
the repository evidence layer; a picker entry is not itself a ranking result.
Failed and OOM runs remain useful evidence and must be preserved.

Selecting a different workload or model clears preparation and result state.
The exact artifact must be prepared again before measurement is admitted. If a
different model identity has already been prepared or attempted in the current
App process, preparation stops and requires the contributor to fully close and
relaunch the App. This prevents multiple model-weight sets from affecting the
same process-level measurement session.

## Measurement admission and procedure

The App admits a measurement only when all frozen conditions are satisfied:

- the exact App and runtime identity is approved by the current verified
  compatibility policy;
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

Each exported result retains the raw evidence needed by the independent RC
validator:

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

For Short Interaction, the App records a deterministic local
`responseConformance` observation using the draft v2 policy resource. The v2
preview recognizes versioned alternatives such as `safe`, `secure`, `saved`,
and `stored`, and distinguishes a policy non-match from a positive
contradiction. That observation never suppresses token, timing, memory, or
first-renderable metrics. The independent validator recomputes behavior status
from generated text and records it separately from performance eligibility.

An atomic local checkpoint is written before each attempt and after each
terminal record. If the process ends mid-session, the next launch preserves
the active attempt as `failed/process_terminated_unclassified` and all
unstarted attempts as `notRun/prior_attempt_unrecoverable`. A completed
checkpoint remains recoverable until its frozen result JSON is saved. An
unresolved checkpoint cannot be overwritten by starting another run.

## Result export and validation

Results are written atomically under the App Documents directory in
`PowerBenchmarkResults/`. The Test tab owns preparation and measurement; the
Results tab lists every valid stored result and owns review, raw sharing, and
submission. Selecting an older result never recalculates or rewrites it. A
configured build can also create a contributor-owned GitHub pull request. The App builds
the current two-file Power 1.1 package, verifies that the saved result bytes
still match the completed in-memory result, preserves `result.json`
byte-for-byte, and saves a local copy under `PowerSubmissionPackages/`.

Direct GitHub submission uses OAuth device flow and requests `public_repo` for
the one submission session. The returned scope is checked before any repository
write, and the token is held only in memory. For an existing contributor fork,
the App verifies that it belongs to this upstream repository, synchronizes its
`main` branch through GitHub's merge-upstream API, and creates the submission
branch from the synchronized fork commit. API errors identify the failing
method and path plus GitHub's request ID without exposing the token. Register
an OAuth App, enable Device Flow, and supply its public client ID as the
`GITHUB_OAUTH_CLIENT_ID` Xcode build setting. Do not add a client secret to the
iOS project. A build without this setting keeps raw sharing and the contributor
guide available but disables the direct-submit button.

The feature changes no frozen validation rule. App 0.13.0 build 16 at its exact
source commit remains the only Power 1.1 reference runner identity. Results
from an App runner not listed by the current versioned compatibility policy are
retained locally but rejected as `runner_incompatible`. Power 1.1's original
App 0.13.0 reference identity remains immutable; later exact runner identities
must be approved by a separate, versioned compatibility policy.

The mutable `power-compatible-runners-current.json` file is discovery metadata
only. It identifies a versioned published policy and its SHA-256 digest. The App
downloads and verifies that immutable policy before matching exact runner and
runtime fields; the discovery file is not itself a validation contract.

Ambient room temperature and its source, case state, placement, and thermal
assistance can be recorded as optional local observations. The App can copy a
plain-text observation block for the contribution PR. These observations never
modify the frozen result schema, admission decision, measurement, or ranking
identity. Deliberately cooled or heated evidence is reviewable but is not
eligible for the ordinary live ranking under the current policy.

The source checkout commit is embedded automatically as a read-only resource
in the built App bundle. A valid 40-character lowercase commit is required
before the App will measure. This prevents an export from claiming an unknown
App revision.

Validate an exported file from the repository root with:

```sh
python3 scripts/validate_suite_b_power_1_1_final_result.py /path/to/result.json \
  --output /path/to/validation-report.json
```

A conforming raw result receives independent structural, protocol, metric,
behavior, performance-ranking, and recommendation decisions. The App itself
does not publish or rank the result.

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
- Community evidence reflects one contributor until another GitHub contributor
  reproduces the exact comparison identity; the App does not claim independent
  reproduction merely because an artifact appears in the picker.

Historical App 0.6.0/0.7.0 bundle formats remain supported by historical
ingestion and validation paths. Power 1.0 evidence remains immutable, and no
historical App export can be relabeled or promoted into Power 1.1 evidence.
