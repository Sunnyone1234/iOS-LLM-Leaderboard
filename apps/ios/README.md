# Power 2 iOS App

This is the active Power 2 App Shell. It provides separate **Test** and
**Results** tabs, consumes generated stack/catalog identity, runs the certified
Power components, stores each evidence envelope independently, and opens
result-only GitHub pull requests.

The historical Power 1.1 App remains under `ios-app/` for audit only. It is
not imported, converted, or submitted here.

## Build configurations

| Configuration | Purpose | Measurement | Public submission |
| --- | --- | ---: | ---: |
| Developer | Code, UI, and integration work | No | No |
| Certification | Maintainer physical-device checkpoint for a new Runner/App candidate | Candidate evidence only | No |
| Official | Current community source configuration | Yes, only while remote current-release preflight passes | Yes, subject to trusted CI |

The compiled build kind and `PowerBuildKind` in `Info.plist` must agree.
Changing a signing team or one build setting cannot promote Developer to
Official.

## Source-built identity boundary

Contributors sign the App locally with their own Apple Team ID. The Team ID is
deliberately outside benchmark identity. An Official configuration embeds the
generated App release declaration, but this is a self-declaration by the local
build, not cryptographic attestation of the installed binary.

Before every Official measurement and submission, the App downloads:

1. `products/power/current.json`; and
2. the App release file referenced by it.

It verifies the referenced file SHA-256, then compares the active stack, App
version/build/source declaration, Bundle ID, and Runner certificate. Intake
closed, remote mismatch, invalid hash, or unavailable network locks both
measurement and submission. Repository CI remains the acceptance authority.

One eligible result is displayed as **Accepted**. Only an independently
contributed matching result raises the exact cell to **Reproduced**.

## Build the current Official configuration

Use the current `main` revision. Do not use a feature branch whose App or
Runner source has changed unless you are performing the release process below.

Create the ignored local signing file:

```bash
cp apps/ios/Configuration/LocalSigning.example.xcconfig \
  apps/ios/Configuration/LocalSigning.xcconfig
```

Set your Apple Team ID and the exact tracked App component-manifest digest:

```text
DEVELOPMENT_TEAM = YOUR_TEAM_ID
POWER_SOURCE_REVISION = output of:
  shasum -a 256 apps/ios/component-manifest.json
```

Open:

```text
apps/ios/PowerBenchmarkApp.xcodeproj
```

Select the shared `PowerOfficial` scheme, your physical iPhone, and Run. The
App must show:

- `Build kind: Official (source-built)`;
- the expected stack and App source declaration; and
- `Supported release identity declared by this source-built App`.

If the release check says update required, pull current `main`, regenerate the
tracked files if instructed by repository checks, rebuild, and retry. Do not
override the check.

## Local signing

Tracked identity is generated from:

```text
apps/ios/Configuration/ReleaseIdentity.json
```

Regenerate its Xcode settings with:

```bash
python3 scripts/generate_power_app_release_identity.py
```

`Signing.xcconfig` and all generated identities are tracked and hashed.
`LocalSigning.xcconfig` is ignored and contains only personal signing plus the
current component digest. Never select a personal team in the target editor,
because that writes it into the hashed project.

Maintainers performing the closed physical rehearsal of a staged next release
also set:

```text
POWER_RELEASE_REHEARSAL = YES
```

The tracked default is `NO`. This local flag permits measurement against the
already frozen candidate while `current.json` still names the prior release,
but it never permits GitHub submission. It is deliberately outside the App
component digest so the exact same source becomes submission-capable when its
immutable App release and `current.json` are activated; public authority still
comes only from the remote current pointer.

## Result durability

The App writes each completed envelope once under its Power 2 Results Store.
The Results tab can select and submit any saved result, not only the last run.

During a run, `PowerRunCheckpointStore` atomically records:

- the exact session context;
- the active attempt before Runtime execution;
- each terminal attempt record; and
- session completion.

After a process termination, the active attempt is recovered as failed with an
explicit interruption code and later attempts are preserved as not-run. The
App never guesses that an unknown termination was OOM. Once the final immutable
envelope is saved, the checkpoint is removed.

## GitHub submission

The Results tab preserves the selected raw result byte-for-byte. OAuth Device
Flow creates a contributor-owned branch from the exact upstream head, writes
only the current two-file package, and opens a PR. It never synchronizes or
modifies the fork's default branch.

Result PRs must remain separate from code or documentation changes. Trusted
base-repository CI reads contributor files as data and decides automatic
acceptance, manual review, or rejection.

## Changing App or Runner source

An existing App release and Runner certificate are immutable. Source edits do
not update them in place. Released component manifests are retained by their
release evidence; changed Runner source is generated into
`candidate-component-manifest.json`, while changed App source is generated
into `apps/ios/component-manifest.json` and frozen before rehearsal. Both are
bound by a fail-closed `products/power/next.json` plan before activation.

1. Make the focused source change.
2. Update tests and current documentation.
3. Increment the App build and regenerate dependency identity, the Runner
   candidate manifest, `next.json`, the App catalog/product identity, and the
   App component manifest.
4. Run Swift package tests and generic iOS Certification/Official builds.
5. If measurement components changed, build `PowerCertification` on a
   physical iPhone, run the exact checkpoint, export untouched evidence, and
   review it with `review_power2_certification_result.py` before issuing a new
   Runner certificate.
6. Set `POWER_RELEASE_REHEARSAL = YES` only in ignored
   `LocalSigning.xcconfig`, build `PowerOfficial` on a physical iPhone,
   perform the App release checkpoint, and review the untouched evidence.
7. Issue versioned immutable Runner, stack, and App release records, then move
   `current.json` in the same reviewed commit. Never modify the previous
   certificate or App release.
8. Confirm the old App now fails remote preflight and the new App passes.

The exact commands and remaining gates are recorded in
[`docs/repository-architecture.md`](../../docs/repository-architecture.md).

## Verification

```bash
swift test --package-path apps/PowerRunnerKit
swift test --package-path apps/PowerAppKit
python3 scripts/generate_power_app_release_identity.py --check
python3 scripts/generate_power_mlx_dependency_identity.py --check
python3 scripts/generate_power_runner_component_manifest.py --check
python3 scripts/generate_power_next_release.py --check
python3 scripts/generate_power2_app_catalog.py --check
python3 scripts/generate_power2_product_identity.py --check
python3 scripts/generate_power_app_component_manifest.py --check
python3 scripts/repoctl.py verify-power-candidate
```

A compiler or simulator run never counts as physical-device benchmark
evidence.
