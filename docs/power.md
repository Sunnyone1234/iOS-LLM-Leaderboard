# Power benchmark

Power measures an exact embedded model configuration on an Apple target. It
does not rank a model name in isolation:

```text
Power Evidence
  = Program Version
  × Target Profile Version
  × Model Artifact Revision
  × Runtime Configuration
  × Runner Certificate
  × App Release
  × Raw Attempts
```

## Current status

Power 2 is in its final activation checkpoint. The text-generation-performance
Program, physical-iPhone Target, four exact model artifacts, Runner
certificate, App shell, trusted intake, and ranking engine are implemented.
Automated checks and generic Official/Certification Release builds pass.
The exact Official build 4 physical-device end-to-end result is still required
before an immutable App release and `products/power/current.json` can be issued.

Until those two records are issued together:

- public intake remains closed;
- Developer and Certification builds cannot produce ranking evidence;
- the Official build is a non-publishable release candidate; and
- Power 1.1 remains only a read-only historical release, not a compatibility
  input to Power 2.

The authoritative activation state is
[`products/power/candidate.json`](../products/power/candidate.json). After
activation, the only public pointer is `products/power/current.json`.

## Benchmark cell

The first implemented cell is:

```text
text-generation-performance@2.0.0
× apple-iphone-physical@1.0.0
```

The Program owns workload meaning, measurement modes, metrics, fixtures, and
schemas. The Target owns physical-device admission and environment capture.
The Runner certificate binds the exact Runner Core, text Program Module,
iPhone Target Adapter, MLX Runtime Adapter, and evidence serialization used to
execute that cell.

New image, 3D, iPad, or macOS work is added as a new Program or Target slot.
It does not branch or silently change the text/iPhone cell.

## Evidence and decisions

Every result preserves warm-up and measured attempts, failures, cancellations,
OOMs, ordered timing evidence, memory samples, thermal state, exact model and
runtime identity, device and OS build, inference settings, and the identities
of its Program, Target, Runner, and App.

Validation keeps these decisions separate:

- structural validity and digest integrity;
- Program and Target contract conformance;
- supported Runner certificate and App release;
- contributor identity and duplicate detection;
- behavior conformance;
- recommendation eligibility;
- per-metric ranking eligibility.

A valid failed or metric-ineligible attempt can therefore remain accepted
evidence without appearing in a ranking. Pipeline TTFT is never relabeled as
user-visible first-renderable time. There is no global Power score.

## Ranking and reproduction

Each view compares only an exact compatible comparison identity. One
case-insensitive GitHub account counts once per cell:

- one distinct contributor: accepted evidence;
- two: independently reproduced;
- three or more: contributor-weighted aggregation.

The UI may group a compatible display family, but exact OS build, model
revision, runtime, inference configuration, workload, measurement mode, and
Runner certificate remain in the evidence identity.

## Contribution flow

The Official App saves every completed result separately. The Results tab lets
the contributor select the exact saved result to share or submit. Direct
GitHub submission uses OAuth Device Flow, creates a branch from the current
upstream head, writes only the two-file package, and opens a pull request
without modifying the contributor fork's default branch.

Trusted `pull_request_target` CI executes only the base-repository validator.
It reads candidate evidence as data, classifies it as automatic acceptance,
manual review, or rejection, and leaves normal code/documentation pull
requests unaffected. Automatic merge requires both `Power submission intake`
and `Validate commit identity` on the current PR head.

Use the [Power contributor guide](../contributor-kit/power.md). The equivalent
public CLI is:

```bash
python3 scripts/power submit /path/to/result.json \
  --github YOUR_GITHUB_HANDLE \
  --accept-declarations
python3 scripts/power validate PATH
python3 scripts/power preview --output /tmp/power-preview
```

## Normative sources

This page explains the method. Machine authority is versioned and pinned by:

- the [Power candidate/current pointer](../products/power/);
- the [text Program manifest](../products/power/programs/text-generation-performance/versions/2.0.0-draft.2/manifest.json);
- the [physical-iPhone Target](../products/power/targets/apple-iphone-physical/versions/1.0.0-draft.1/manifest.json);
- the [Runner certificate](../products/power/runner-certificates/power2-runner-87f62feecc2b.json);
- the versioned [intake](../products/power/policies/intake/1.0.0-draft.1.json)
  and [ranking](../products/power/policies/ranking/1.0.0-draft.2.json)
  policies; and
- the architecture and migration audit in
  [repository-architecture.md](repository-architecture.md).

Historical Power 1.0 and 1.1 manifests, raw evidence, and checksums remain at
their original paths for auditability. No active Power 2 pointer references
them.
