# Scripts

## Public entry point

The only public Power command is:

```bash
python3 scripts/power submit RESULT.json --github HANDLE --accept-declarations
python3 scripts/power validate \
  submissions/power/text-generation-performance/2.0.0/draft/ID
python3 scripts/power preview
```

It is a thin Power 2 façade over the same package, validation, and ranking
implementation used by trusted CI. It never dispatches by legacy Power
version. The extensionless path deliberately avoids rewriting the SHA-256
pinned historical `scripts/power.py`; Power 1.0 and 1.1 scripts remain
historical audit assets only.

## Current implementation tools

- `repoctl.py verify-power-candidate` verifies the clean-break Power 2
  activation candidate, every pinned candidate asset, fixture digest, Target,
  policy, model-cohort boundary, and the absence of active Power 1.1
  dependencies. It is a maintainer migration command and does not open intake.
- `repoctl.py activate-power` reviews one exact Official physical-device
  result and renders the immutable App release, retained raw evidence,
  `current.json`, and active registry as one set. It is a dry run unless
  `--write` is supplied, and it refuses older App builds or an already active
  product.
- `repoctl.py validate-power-package` invokes the new dependency-free trusted
  validation engine with explicit PR author, evaluation timestamp, trusted
  source revision, and optional accepted-result digests. Public tools resolve
  `products/power/current.json` after activation and otherwise fail closed
  against the candidate.
- `generate_ios_app_release_identity.py` generates the App version/build
  xcconfig and Swift Power identity constants from
  `ios-app/Config/release-identity.json`; CI uses `--check` to reject drift.
- `generate_power_mlx_dependency_identity.py` verifies the direct MLX,
  Hugging Face, and tokenizer pins in
  `apps/PowerRunnerKit/Package.resolved`, then embeds the complete lock-file
  digest in the Runtime Adapter evidence identity.
- `generate_power_runner_component_manifest.py` hashes the separate Power 2
  evidence, Runner Core, text Program Module, iPhone Target Adapter, and MLX
  Runtime Adapter sources.
- `generate_power_release_candidates.py` binds those exact Runner components
  and the complete App component manifest into separate closed certification
  and release identities. It deterministically materializes the active Runner
  certificate only from the pinned passing Certification review; it never
  issues an App release or opens intake.
- `generate_power2_product_identity.py` generates lifecycle-neutral Swift
  identity from the candidate pointer before release and the active pointer
  after cutover. It deliberately does not compile repository intake state
  into the App.
- `generate_power2_app_catalog.py` verifies the inactive candidate hash chain
  and generates the exact model, workload, and fixture catalog used only by
  the physical-iPhone `PowerCertification` smoke-test scheme. It does not
  issue a runner certificate, App release, or public submission permission.
- `review_power2_certification_result.py` applies the trusted Power 2 engine
  to one physical-iPhone Certification result using only the closed candidate
  identities. Its report is always non-publishable and non-ranking.
- `review_power2_app_release_result.py` applies the trusted engine to one exact
  Official App release-candidate result during the closed end-to-end
  rehearsal. Its report is also always non-publishable and non-ranking.
- `validate_suite_b_power_1_1_submission.py` validates historical Power 1.1
  packages and is not called by a current public command or workflow.
- `validate_suite_b_power_1_1_compatible_result.py` applies the versioned exact
  runner/runtime allowlist before reusing the frozen Power 1.1 validator.
- `validate_suite_b_power_1_1_final_result.py` derives final Power 1.1
  eligibility from adopted RC1 evidence and remains pinned and immutable.
- `generate_power_community_ranking.py` builds the historical Power 1.1
  evidence dataset and is not a current workflow entry.
- `generate_ship_profiles.py` builds Ship evidence profiles.

Power 1.1.2 through 1.1.4 retain version-suffixed validation, triage, and
ranking adapters. They load frozen implementations without changing pinned
bytes. They are archive assets, not a parallel contributor flow.

## Versioned and historical tools

Other scripts preserve release generation, pilot processing, Framework v1,
Power 1.0, RC validation, review records, and audit workflows. Some are pinned
by release manifests and must not be modified. They are implementation and
audit assets, not additional contributor entry points.

Before changing a release-specific script, check whether a manifest under
`benchmarks/**/releases/` pins its SHA-256. Create a new versioned asset instead
of altering a pinned file.

## Power 2 activation candidate

The current review command is:

```bash
python3 scripts/repoctl.py verify-power-candidate
python3 scripts/generate_power2_product_identity.py --check
python3 scripts/generate_power2_app_catalog.py --check
python3 scripts/generate_power_release_candidates.py --check
python3 scripts/repoctl.py validate-power-package PACKAGE \
  --pr-author HANDLE \
  --evaluated-at 2026-07-23T12:00:00Z \
  --validator-source-revision GIT_SHA
```

A successful result means that the candidate contract stack is internally
complete and independent from Power 1.1. It reports four exact rerun-candidate
models, an active source- and physical-evidence-bound Runner certificate, and
a closed App build 4 release candidate. Automated verification passes; the
exact build 4 physical-device end-to-end checkpoint remains pending.
The certification catalog check additionally proves that the App's closed
smoke-test catalog is a deterministic projection of those pinned assets; it
does not certify a run.
`scripts/power` already targets only Power 2. Public intake remains
fail-closed until the immutable App release and active pointer are issued
together.

After the exact build 4 raw result is exported, the complete activation dry
run is:

```bash
python3 scripts/repoctl.py activate-power /path/to/raw-result.json \
  --reviewed-at 2026-07-24T12:00:00Z \
  --activated-at 2026-07-24T12:01:00Z \
  --validator-source-revision "$(git rev-parse HEAD)"
```

Only after reviewing that output should a maintainer repeat it with `--write`.
The resulting files are reviewed and merged together; there is no partial
intake-opening command.
