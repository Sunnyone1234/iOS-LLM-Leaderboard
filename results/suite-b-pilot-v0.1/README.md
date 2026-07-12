# Suite B Internal Pilot v0.1 Data Pipeline

This directory is a non-official, internal data path for reviewing real output
from the existing Benchmark App. It does not define an official benchmark
release, result schema, submission process, trust level, or public ranking.

The Pilot deliberately accepts only:

- `suite-b-result-bundle-0.2` from Benchmark App `0.5.0` build `7`, retained
  for the completed single-model Stage 1 path;
- `suite-b-result-bundle-0.3` from Benchmark App `0.6.0` build `8`, with one of
  the three fixed model profiles;
- `b-ux-001-short-interaction@0.2.0-pilot`; and
- `b-pipe-001-sustained-generation@0.2.0-pilot`;
- the pinned MLX Swift LM `3.31.4` / MLX `0.31.6` reference runtime.

Do not place community-submission wrappers, hand-authored results, demo data,
simulated measurements, or placeholder measurements in `raw/`.

## Current dataset

The final Pilot matrix contains six genuine App 0.6.0 build 8 exports from one
iPhone 14 Pro Max (`iPhone15,3`): three exact model artifacts across both Pilot
workloads. The current pipeline report is 6 normalized, 6 eligible, 0
ineligible, and 0 rejected. The two earlier App 0.5.0 smoke exports are retained
under `stage-1-smoke/` and are not included in generated comparisons.

Review [the release notes](RELEASE-NOTES.md) for scope, headline evidence,
validation, privacy review, and known limitations. Verify the final raw and
generated artifacts with [SHA256SUMS](SHA256SUMS).

## Generate the Pilot views

Copy unmodified App result JSON files into `raw/`, then run:

```bash
python3 scripts/generate_suite_b_pilot.py
```

To use temporary or review directories:

```bash
python3 scripts/generate_suite_b_pilot.py \
  --input /path/to/app-results \
  --output /path/to/pilot-output
```

The command writes:

- `normalized-results.json`: validated configuration identities and
  recalculated comparative fields;
- `pipeline-report.json`: accepted, eligible, and rejected counts plus errors;
- `LEADERBOARD.md`: workload- and device-separated Pilot comparisons plus a
  non-ranked section for valid partial or ineligible evidence; and
- `SHIP-EVIDENCE.md`: facts directly present in eligible result bundles, using
  Verified, Supported, Unsupported, Unknown, and Warning statuses.

The command exits nonzero when any input JSON is rejected. An empty input
directory is successful and produces explicit “no eligible Pilot results”
outputs.

## What is checked

The pipeline enforces the two frozen Pilot identities and their current App
version/build, reference runtime, plan, measurement, generation, fixture,
environment, and 1+5 attempt contract. It verifies raw-token TTFT, decode, and
token-interval calculations, then recalculates the available medians, outcome
counts, final thermal state, and B-PIPE-001 first-to-last changes.

Structurally valid but environment- or evidence-ineligible runs remain in the
normalized file with reason codes; they do not enter the comparison or Ship
views. Failed and not-run attempts are retained rather than filtered from the
source evidence.

## Interpretation limits

- This Pilot is not Suite B 1.0 and must not be presented as official.
- B-UX-001 ranks responsiveness only. Its historical
  `medianUserVisibleTTFTMilliseconds` field is labeled **First-renderable proxy
  TTFT**. It is measured inside the adapter, not at the screen. The
  result envelope does not contain an automated response-quality decision. Its
  median and timing order are consistency-checked, but the exact proxy cannot
  be independently reconstructed from the exported token events.
- B-PIPE-001 contains five measured attempts; it is not a general thermal
  stability claim. Output below the RC1 plan's 256-token band is reported as a
  Pilot warning, not used as a Pilot v0.1 eligibility gate.
- Rankings never cross workload, device/OS, plan, measurement-boundary, or
  generation-configuration groups.
- Ship output contains no score. Pinned source, repository size, and license
  metadata are recorded without a legal conclusion. Inference-time network
  state, App Store readiness, minimum supported device, and distribution facts
  remain Unknown where the result bundle provides no evidence.
