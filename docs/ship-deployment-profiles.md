# Ship Deployment Profiles 1.0 RC1

## Purpose

Ship translates a published Power configuration into deployment guidance for
iOS developers. It does not create a new benchmark, workload, ranking, or
aggregate score.

Each profile is bound to an exact tested combination of:

- model artifact, revision, format, and quantization;
- runtime, dependency identity, and backend;
- physical device, OS build, and reference App identity;
- published Power 1.0 result IDs and raw-evidence hashes.

The profile may reuse canonical Power measurements. It must not reinterpret a
Power metric or infer support on an untested device.

## Status vocabulary

Ship RC1 uses three evidence states:

- **Verified**: directly supported by consistency-checked Power evidence or
  source metadata bound to that evidence.
- **Implementation-supported**: present in the reviewed reference
  implementation or integration recipe, but not validated as a benchmark
  claim.
- **Unknown**: the current evidence does not establish the claim.

Absence of evidence is never reported as support. `Unknown` is not equivalent
to unsupported; an unsupported claim would require explicit negative evidence.

## RC1 evidence rules

A profile can enter RC1 only when:

1. its source is the published Power Benchmark 1.0 normalized dataset;
2. every source row is Maintainer Reference evidence;
3. at least one source row is active in an official workload ranking;
4. the raw result ID and SHA-256 match the normalized source row;
5. the exact pinned artifact completed model loading without a download during
   the measurement session;
6. completed active attempts retain ordered token events; and
7. model, runtime, device, and OS identity are consistent across the profile.

The generated profile preserves every source Power row, including a valid row
that was ineligible for its workload's primary ranking metric.

## Measured constraints

Artifact repository size is publisher metadata captured by Power 1.0.

The Ship table's observed memory value is the maximum of the eligible Power
workload medians for `TASK_VM_INFO.phys_footprint`. It is neither the maximum
single sample nor a minimum RAM requirement. Raw workload summaries remain
available in each machine-readable profile.

## Claims intentionally left unknown

The current six-result evidence matrix does not establish:

- fully offline execution, because measured-phase network state was not
  recorded;
- generation cancellation behavior;
- bundling the model inside an App distribution;
- a minimum supported Apple device or OS;
- App Store acceptance or distribution readiness; or
- app-level privacy compliance.

These fields remain `Unknown` until direct, reviewable evidence exists. Ship
does not turn local inference or license metadata into a legal conclusion.

## Integration recipe boundary

The MLX Swift recipe mirrors the revision-pinned loader and runtime token stream
used by the reference App. It is provided under the repository's MIT code
license. Its presence is `Implementation-supported`, not proof that every app
architecture, cancellation policy, distribution method, or privacy design has
been tested.

## Regeneration

From the repository root:

```bash
python3 scripts/generate_ship_profiles.py
shasum -a 256 -c results/ship-1.0/SHA256SUMS
```

The generator fails closed if the Power release is not official, source hashes
change, evidence levels regress, the six-result/three-artifact identity changes,
or the verified loader and token-event conditions are absent.
