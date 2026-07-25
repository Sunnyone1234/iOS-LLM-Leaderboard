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

- `repoctl.py verify-power-candidate` verifies the active Power 2 pointer,
  immutable App release and activation evidence, plus the fail-closed
  `next.json` release plan and exact current Runner candidate source. The
  historical command name is retained for CI continuity; verification is
  read-only.
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
  Runtime Adapter sources into `candidate-component-manifest.json`. It never
  rewrites the active Runner snapshot.
- `generate_power_next_release.py` binds that candidate to the current
  measurement contract and next App build in a fail-closed release plan. No
  Runner certificate or App release is invented before reviewed physical
  evidence exists.
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
- `issue_power_next_runner_certificate.py` consumes one passing Certification
  review, preserves the exact result and review bytes plus Runner/App/runtime
  snapshots, issues a new immutable Runner certificate, creates the next
  release-candidate stack, and advances only the fail-closed `next.json`.
- `stage_power_next_app_release.py` snapshots the exact App component
  manifest after a successful generic Official build and records the
  immutable App release candidate in `next.json`. It leaves the physical App
  rehearsal pending and cannot open intake. Replacing a staged candidate is
  explicit: `--supersede-existing` also requires the prior exact physical
  result and passing review, then retains both with a pinned supersession
  record instead of overwriting history.
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

## Power 2 active state

The current review command is:

```bash
python3 scripts/repoctl.py verify-power-candidate
python3 scripts/generate_power2_product_identity.py --check
python3 scripts/generate_power2_app_catalog.py --check
python3 scripts/generate_power_next_release.py --check
python3 scripts/repoctl.py validate-power-package PACKAGE \
  --pr-author HANDLE \
  --evaluated-at 2026-07-23T12:00:00Z \
  --validator-source-revision GIT_SHA
```

For each future closed next-release cycle, the maintainer-only progression is:

```bash
python3 scripts/issue_power_next_runner_certificate.py \
  CERTIFICATION_RESULT.json CERTIFICATION_REVIEW.json
# Repeat with --write only after inspecting the dry-run output.

xcodebuild -project apps/ios/PowerBenchmarkApp.xcodeproj \
  -scheme PowerOfficial -configuration Official \
  -destination 'generic/platform=iOS' CODE_SIGNING_ALLOWED=NO build

python3 scripts/stage_power_next_app_release.py \
  --generic-ios-release-build-passed
# Repeat with --write only after inspecting the dry-run output.
```

If a reviewed rehearsal exposes a pre-activation source defect, stage the
replacement only after its generic build passes:

```bash
python3 scripts/stage_power_next_app_release.py \
  --generic-ios-release-build-passed \
  --supersede-existing \
  --superseded-result EXACT_RESULT.json \
  --superseded-review EXACT_REVIEW.json
# Inspect, then repeat with --write.
```

Both commands preserve immutable inputs, refuse conflicting overwrites, keep
`current.json` untouched, and leave public intake closed for the candidate.
The physical Official result is reviewed separately before any atomic release
and pointer update.

After that exact replacement result passes, the maintained upgrade operation
is a dry run by default:

```bash
python3 scripts/repoctl.py activate-power-next EXACT_RESULT.json \
  --reviewed-at 2026-07-25T15:00:00Z \
  --activated-at 2026-07-25T15:01:00Z \
  --validator-source-revision GIT_SHA
# Inspect, then repeat with --write in the same reviewed activation commit.
```

It preserves the previous `current.json` bytes beside the new activation
evidence, issues an immutable App release, advances `current.json`, records the
completed `next.json` plan, and updates the active registry as one file set.
It refuses a result from the superseded App candidate.

A successful result means that the active contract stack is internally
complete and independent from Power 1.1. It verifies four exact model
artifacts, the source- and physical-evidence-bound Runner certificate,
supported Official build 5 App release, retained activation result and review,
and open public intake. The certification catalog remains a deterministic
projection of the pinned assets. `scripts/power` targets only Power 2.

`repoctl.py activate-power` is retained only for auditing the one-time initial
activation. Later releases use `next.json`, new immutable certificate/release
records, and an atomic current-pointer update; the initial activation command
must not be reused.

Only after reviewing that output should a maintainer repeat it with `--write`.
The resulting files are reviewed and merged together; there is no partial
intake-opening command.
