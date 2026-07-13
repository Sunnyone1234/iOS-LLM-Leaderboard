# Power + Ship Pilot v0.1

## Status

Power + Ship Pilot v0.1 is a completed, untagged historical evidence milestone
for Product Phase 1. It validated the smallest credible end-to-end evidence
path for on-device AI deployment on Apple platforms. The maintainer decided
not to publish a Pilot tag or GitHub Release and moved the active target to
[Power Benchmark 1.0 Foundation](power-benchmark-1.0-foundation.md).

The Pilot is narrower than Suite B 1.0. It is non-official evidence work and
does not authorize a default leaderboard, verified ranking, or general claim
about model or device performance. Its results remain historical Pilot
evidence and cannot be relabeled as Power 1.0 results. Existing workload,
suite, task, protocol, schema, and directory identities remain unchanged.

Build remains a Product Phase 2 Research Track. No Build task, protocol, runner,
schema, or result is required for this Pilot.

## Pilot Question

Can the project execute two fixed Suite B workloads on a small set of physical
iPhone configurations, preserve usable Power evidence, generate a simple
configuration-level leaderboard, and turn the same evidence into an honest
Ship view without inventing unsupported deployment claims?

## Frozen Scope

### Power workload candidates

Pilot v0.1 contains exactly these Suite B workload IDs:

| Workload | Pilot role | Current status |
| --- | --- | --- |
| `b-ux-001-short-interaction` | User-facing responsiveness under a fixed short interaction | Stable Pilot candidate; remains non-official until every Pilot gate passes |
| `b-pipe-001-sustained-generation` | Sustained decode and first-to-last degradation evidence | Stable Pilot candidate; remains non-official until every Pilot gate passes |

The Pilot uses the existing `0.2.0-pilot` workload versions. App 0.5.0 Stage 1
evidence uses `suite-b-result-bundle-0.2`; App 0.6.0 adds exact fixed-profile
metadata in `suite-b-result-bundle-0.3`. This does not activate either as an
official standard.

### Initial data matrix

The intended first dataset is deliberately small:

- 2–3 exact model artifacts;
- one reference runtime;
- 1–2 physical iPhone model identifiers; and
- both selected workloads where each configuration is compatible.

The matrix describes the desired publication evidence. It does not authorize
placeholder rows when a physical result is missing.

The fixed reference-device matrix is:

| Size class | Exact artifact | Quantization | Physical status |
| --- | --- | --- | --- |
| Small | `mlx-community/Qwen3-0.6B-4bit@73e3e38d981303bc594367cd910ea6eb48349da8` | 4-bit | Both workloads completed on `iPhone15,3` |
| Medium | `mlx-community/Qwen3-1.7B-4bit@3b1b1768f8f8cf8351c712464f906e86c2b8269e` | 4-bit | Both workloads completed on `iPhone15,3` |
| Larger | `mlx-community/Qwen3-4B-3bit@c4e8054c71facfa84f781cdb7c1ffab3f09f89bf` | 3-bit | Both workloads completed on `iPhone15,3`; measured memory evidence retained |

These are fixed Pilot profiles, not a generalized model catalog. All three use
the same MLX Swift LM reference runtime and the same two workload identities.

### Experimental workloads

These current Suite B workloads remain **Experimental** and are outside Pilot
v0.1:

| Workload | Reason for exclusion |
| --- | --- |
| `b-pipe-002-input-length-sweep` | Token-exact, multi-point calibration and cross-runtime compatibility are not frozen for the Pilot |
| `b-ux-002-context-assistance` | Token-exact context construction, quality-gate behavior, and execution identity are not frozen for the Pilot |

Experimental workloads may remain in the repository and in development tools.
They must not be presented as Pilot workloads, included in Pilot comparison
views, or accepted as Pilot-eligible evidence. Experimental is the Pilot release
classification; it does not rewrite the manifests' existing validation-lifecycle
values.

### Ship output

Pilot Ship output is a deployment evidence profile for the same configuration
used by the two Power workloads. It may report only reviewable facts, including:

- exact model artifact, revision, format, and quantization;
- exact runtime, dependency revisions, backend, device, and OS build;
- verified model preparation, cache, offline-execution, and distribution facts;
- a focused Swift integration recipe that matches the tested runtime profile;
- license and attribution source metadata;
- measured constraints linked back to Suite B evidence; and
- explicit unsupported, unverified, and unknown capabilities.

Pilot v0.1 does not add a Suite D or Suite E benchmark task. Ship does not
recalculate Suite B metrics, create a deployment score, or turn license,
privacy, or App Store metadata into a legal conclusion.

## Legacy Suite Mapping

Build, Power, and Ship are public product tracks layered over the existing
suite organization. This mapping does not rename or move any directory and does
not change any suite or workload ID.

| Legacy suite | Product-track mapping | Pilot v0.1 relationship |
| --- | --- | --- |
| Suite A: Swift Code Generation | Build, Phase 2 Research Track | Preserved for compatibility; excluded from Pilot v0.1 |
| Suite B: On-device Performance | Power, Phase 1 | Owns Pilot measurements; only B-UX-001 and B-PIPE-001 are included |
| Suite C: Xcode Integration | Build, Phase 2 Research Track | Preserved for compatibility; excluded from Pilot v0.1 |
| Suite D: App Feature Intelligence | Potential Power quality evidence in later Phase 1 work | No Suite D task is included in Pilot v0.1 |
| Suite E: Runtime Evaluation | Ship compatibility and integration evidence in later Phase 1 work | No Suite E task is executed or scored in Pilot v0.1; the Pilot Ship profile reuses the tested Suite B configuration |

## Pilot Evidence Unit

A Pilot observation is not a model-only result. Its comparison identity is:

```text
workload and workload version
+ exact model artifact and quantization
+ model revision and format
+ runtime and backend
+ physical iPhone and OS build
+ generation configuration
+ App version and build
```

Two observations are not compared in the same group when workload, physical
device, OS, or timing boundary differs.

## Minimal Pilot Result Contract

Pilot v0.1 consumes the existing App result envelope rather than introducing a
new generalized schema. Each input must contain:

- workload ID and version;
- exact model artifact, revision when available, quantization, and format;
- runtime name, version, and backend;
- physical-device machine identifier and iOS version/build;
- App version and build;
- generation and measurement configuration;
- one warm-up and five attempt-level records, including failures or not-run
  outcomes that the completed App session retained;
- attempt metrics and token events needed by the Pilot generator;
- derived session summary; and
- local session/performance eligibility and reason codes.

The ingestion command rejects malformed or incompatible files, verifies the
raw-token metrics it can recalculate, checks session summaries, and writes a
normalized Pilot dataset. Missing App source commit, artifact size, license,
offline-state proof, or other Ship metadata is reported as `Unknown` or a
warning; it is not silently invented.

## Stage 1 Physical-iPhone Runbook

Stage 1 uses the pinned `mlx-community/Qwen3-0.6B-4bit` profile and produces
exactly one raw B-UX-001 export and one raw B-PIPE-001 export from the same
physical iPhone. Simulator output is test-only and must never be placed in the
Pilot `raw/` directory.

**Status:** passed on 2026-07-13. Both unmodified App exports from an iPhone 14
Pro Max (`iPhone15,3`) were accepted: 2 normalized, 2 eligible, 0 rejected.
This proves the single-model export-to-ingestion path; it does not complete the
six-result matrix. Those two App 0.5 exports are retained separately under
`results/suite-b-pilot-v0.1/stage-1-smoke/` and are not part of the final
comparison input.

Before measuring, charge the iPhone above 50%, turn off Low Power Mode, let the
device cool to the system-reported `nominal` thermal state, and disconnect
external power. In Xcode, select the physical iPhone and edit the BenchmarkApp
scheme so Run uses the **Release** configuration with **Debug executable**
turned off. The optional `GIT_COMMIT_SHA` build setting may contain the exact
source commit; when omitted, ingestion records a source-identity warning rather
than guessing it.

Use this checklist without changing the frozen attempt plan:

1. Build and install BenchmarkApp on the physical iPhone with the Release
   scheme, then launch it without an attached debugger.
2. Confirm the App reports Release, Low Power Mode off, battery at least 50%,
   battery state unplugged, and thermal state nominal.
3. Select `B-UX-001 · Short Interaction` with the pinned Qwen3 0.6B profile.
4. Tap **Prepare Model**. If this is the first download and the App requests a
   restart, fully close and relaunch the App, then select B-UX-001 and prepare
   again until it reports a verified cached model.
5. Tap **Run Benchmark** once and allow the fixed one warm-up plus five measured
   attempts to finish. Do not rerun merely to obtain a better result.
6. Tap **Export Raw JSON** and save/share the original file without editing its
   contents. Do not use the Legacy Draft Submission export.
7. Select `B-PIPE-001 · Sustained Generation`; switching workloads correctly
   invalidates the prior prepared state.
8. Tap **Prepare Model** again and wait for the verified cached-model state.
9. Reconfirm the admission state, tap **Run Benchmark** once, and let all
   planned attempts finish.
10. Tap **Export Raw JSON** and save/share the second original file.
11. Place both unmodified JSON files in
    `results/suite-b-pilot-v0.1/raw/`.
12. Run `python3 scripts/generate_suite_b_pilot.py`, then inspect
    `pipeline-report.json`, `normalized-results.json`, `LEADERBOARD.md`, and
    `SHIP-EVIDENCE.md` before treating Stage 1 as passed.

The two expected filenames are App-generated and include the workload ID,
actual artifact, device identifier, and result ID. Preserve those filenames
when transferring the files. Screenshots may help diagnose a failure, but they
do not replace either raw JSON export.

## Stage 3 Three-Profile Physical-iPhone Runbook

**Status:** passed on 2026-07-13. The six unmodified App 0.6.0 build 8 exports
produced 6 normalized, 6 eligible, and 0 rejected results. Every model/workload
cell completed five measured attempts; serious final thermal state in the
medium and larger B-PIPE-001 runs is retained as valid evidence rather than
filtered out.

Install BenchmarkApp 0.6.0 build 8 on the same physical iPhone using Release
with **Debug executable** off. Then execute the following six cells exactly
once each:

| Model picker value | Workload picker value |
| --- | --- |
| Qwen3 0.6B · 4-bit · Small | B-UX-001 · Short Interaction |
| Qwen3 0.6B · 4-bit · Small | B-PIPE-001 · Sustained Generation |
| Qwen3 1.7B · 4-bit · Medium | B-UX-001 · Short Interaction |
| Qwen3 1.7B · 4-bit · Medium | B-PIPE-001 · Sustained Generation |
| Qwen3 4B · 3-bit · Larger | B-UX-001 · Short Interaction |
| Qwen3 4B · 3-bit · Larger | B-PIPE-001 · Sustained Generation |

For every cell, select the model and workload, tap **Prepare Model**, follow any
restart request after the first download, prepare again until the exact cached
artifact is verified, reconfirm the admission state, run once, and export
**Raw JSON** without editing it. Allow the phone to return to nominal thermal
state before the next cell. Do not rerun a slow or failed cell merely to improve
the result; failed, OOM, cancelled, and not-run evidence is part of the Pilot.
Send all six original `.json` files back together. Screenshots are optional and
useful only when the App reports a preparation or execution error.

## Publication Checklist

Power + Ship Pilot v0.1 is ready when:

- [x] B-UX-001 and B-PIPE-001 both execute through the production App path
      using the configuration recorded in their result files.
- [x] Pilot result identity and timing labels are accurate; the current
      B-UX-001 value is labeled First-renderable proxy TTFT and is not measured
      screen-visible latency.
- [x] The small intended matrix contains real physical-iPhone results; no
      placeholder or simulated measurement is used.
- [x] `python3 scripts/generate_suite_b_pilot.py` processes every included raw
      file and reports no rejected input.
- [x] The generated Power leaderboard compares full configurations, separates
      incompatible groups, reports attempts/failures, and contains no global
      score.
- [x] The generated Ship matrix reuses the tested configurations, uses factual
      status labels, and contains no Ship score.
- [x] Outputs and documentation are clearly marked Pilot/non-official and list
      the narrow evidence and metric limitations.

## Readiness Gates

### Pilot blockers

These issues would otherwise make Pilot output misleading or unusable:

1. The production App must execute B-UX-001 and B-PIPE-001 using the same plan
   identity and generation settings it exports.
2. The Pilot result must preserve enough identity, attempts, metrics, and
   completion/failure state for ingestion and display.
3. Pipeline TTFT must remain distinct from B-UX-001 First-renderable proxy
   TTFT; neither may be mislabeled as screen-visible latency.
4. The ingestion command must reject malformed/incompatible files, normalize
   usable evidence, and generate the Power and Ship outputs consistently.
5. Real physical-iPhone results for the intended small matrix must be collected
   and added before publication. **Satisfied:** 6/6 App 0.6 results accepted.

### Pre-1.0 blockers

These remain in the RC1 hardening backlog and do not block Pilot v0.1:

- immutable Suite B 1.0 release and migration rules;
- complete public JSON schemas and exhaustive semantic validators;
- exact outcome taxonomy, per-metric eligibility, null handling, and every
  timing/memory edge case;
- crash/OOM-safe checkpoint recovery and independently recalculable evidence
  for every official metric;
- formal submission, validation-status, trust, review, and reproduction rules;
- minimum official model/runtime/device coverage; and
- stable correction, withdrawal, deprecation, and release-history governance.

### Future scale requirements

These are intentionally outside Pilot v0.1:

- community upload, submission, trust, and automated reproduction systems;
- generalized multi-runtime infrastructure and cryptographic attestation;
- website application and CI publication automation;
- promotion of B-PIPE-002 or B-UX-002;
- iPad/Mac comparison and larger device coverage; and
- Build implementation, which remains a Phase 2 Research Track.

## Change Control

Pilot v0.1 is a learning milestone, not an immutable industry standard. Changes
needed after real-device testing must remain explicit, preserve existing IDs,
and update the relevant Pilot version rather than being hidden in wording.
