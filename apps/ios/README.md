# Power 2 iOS App candidate

This directory now contains the clean Power 2 candidate App Shell. It has
separate Test and Results tabs, consumes the generated product identity, and
uses `PowerAppKit` for exact-byte result storage. It links the complete
candidate `PowerRunnerKit` implementation so generic iOS Release builds verify
the real dependency graph.

The project has three explicit build kinds:

- **Developer** — the normal Debug and Release configurations, displayed on
  device as **Power Benchmark Dev**. It can inspect the App and local UI but
  cannot measure or submit ranking evidence.
- **Certification** — the maintainer-only physical-device smoke-test
  configuration. It can write candidate evidence but cannot submit or rank it.
- **Official** — the contribution configuration. An exact generated App
  candidate may measure and create a real result-only pull request. Trusted
  repository state, rather than a lifecycle flag compiled into the binary,
  decides whether that result is a non-publishable rehearsal or accepted
  public evidence.

The compiled kind and the `PowerBuildKind` value embedded in `Info.plist` must
agree. Overriding one build setting cannot turn a Developer build into an
Official build.

App version, build number, Bundle IDs, and the distinct on-device names have
one tracked source:
`apps/ios/Configuration/ReleaseIdentity.json`. Regenerate the Xcode settings
after changing it:

```bash
python3 scripts/generate_power_app_release_identity.py
```

The generated configuration, source identity, App component manifest, result
envelope, and repository validator are hash-bound. Do not type those values
again in the Xcode project or release-candidate generator.

Apple signing is deliberately outside the pinned project. Copy the example
once and edit only the ignored local file:

```bash
cp apps/ios/Configuration/LocalSigning.example.xcconfig \
  apps/ios/Configuration/LocalSigning.xcconfig
```

Then replace `YOUR_TEAM_ID` and
`CURRENT_APP_COMPONENT_MANIFEST_SHA256` in `LocalSigning.xcconfig`. Obtain the
second value with:

```bash
shasum -a 256 apps/ios/component-manifest.json
```

That local source-revision line is what makes **Run** in Xcode produce the
exact Certification or Official candidate instead of a deliberately locked
build with an unspecified source identity. Do not select a team in the Xcode
target editor because that writes a personal `DEVELOPMENT_TEAM` back into the
hashed project file. `Signing.xcconfig` is tracked and pinned;
`LocalSigning.xcconfig` is ignored and never enters an App, Runner, Program,
Target, or measurement identity.

The separate `PowerCertification` scheme is a maintainer-only physical-iPhone
smoke-test path. It executes the exact models, workloads, Runner, Program, and
Target pinned by the activation candidate and saves a candidate evidence envelope
locally. It is compiled only for `iphoneos`, requires the exact generated App
component-manifest SHA-256 at build time, and cannot submit or rank the
resulting evidence:

```bash
APP_SOURCE_REVISION="$(
  shasum -a 256 apps/ios/component-manifest.json | awk '{print $1}'
)"
xcodebuild \
  -project apps/ios/PowerBenchmarkApp.xcodeproj \
  -scheme PowerCertification \
  -configuration Certification \
  -destination 'platform=iOS,name=YOUR_IPHONE' \
  POWER_SOURCE_REVISION="$APP_SOURCE_REVISION" \
  build
```

Do not archive, distribute, or describe this build as a released benchmark
App. Its `2.0.0-certification` identity and candidate certificate ID exist only
to bind pre-release physical-device review to exact source. Unlike a Git commit
alone, the component manifest covers the complete App shell, generated
candidate files, support modules, Xcode project, build schemes, dependency
locks, and shared signing boundary; personal signing remains outside it.

To complete the physical-device checkpoint:

1. Build and install the `PowerCertification` scheme on a physical iPhone
   using the exact `POWER_SOURCE_REVISION` command above.
2. Open **Test**, select a pinned model and workload, prepare the model, and
   run the Certification smoke test without thermal assistance.
3. Open **Results**, select the newly completed result, and use **Share Raw
   Power JSON**. Do not edit, reformat, or resave the exported bytes.
4. Give the exported JSON to a maintainer. The maintainer reviews it with:

   ```bash
   python3 scripts/review_power2_certification_result.py \
     /path/to/raw-result.json \
     --evaluated-at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
     --validator-source-revision "$(git rev-parse HEAD)"
   ```

This review is closed candidate evidence. A passing report is still
non-publishable and non-ranking; it authorizes the later certificate and App
release steps only after the raw evidence and physical run have been reviewed.

The reviewed Certification evidence has issued the active Runner certificate.
`PowerOfficial` is a separately shared scheme and Bundle ID. Build the exact
Official build 4 candidate with its generated App component-manifest digest:

```bash
APP_SOURCE_REVISION="$(
  shasum -a 256 apps/ios/component-manifest.json | awk '{print $1}'
)"
xcodebuild \
  -project apps/ios/PowerBenchmarkApp.xcodeproj \
  -scheme PowerOfficial \
  -configuration Official \
  -destination 'platform=iOS,name=YOUR_IPHONE' \
  POWER_SOURCE_REVISION="$APP_SOURCE_REVISION" \
  build
```

This exact candidate can run a benchmark and create a real result-only pull
request while intake remains closed. Trusted CI treats it as non-publishable
and non-ranking until the immutable App release and active pointer exist.
Export the newly completed raw JSON without editing it and review it with:

```bash
python3 scripts/review_power2_app_release_result.py \
  /path/to/raw-result.json \
  --evaluated-at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --validator-source-revision "$(git rev-parse HEAD)"
```

The candidate review report is always non-publishable and non-ranking. A pass
for exact build 4 authorizes the immutable App release step; it does not open
intake by itself. The maintainer then dry-runs the single atomic command:

```bash
python3 scripts/repoctl.py activate-power /path/to/raw-result.json \
  --reviewed-at 2026-07-24T12:00:00Z \
  --activated-at 2026-07-24T12:01:00Z \
  --validator-source-revision "$(git rev-parse HEAD)"
```

After reviewing the output, repeat with `--write`. That one reviewed change
retains the exact raw bytes and review, issues the immutable App release, and
opens `current.json` and the registry together. Evidence from older App builds
remains visible and shareable, but the Submit action accepts only a result
whose complete App release identity equals the running Official build.

The scheme's presence and local signing do not authorize acceptance: the
generated release identity and trusted repository pointer remain
authoritative. A contributor may install the distributed Official build or
build the exact `PowerOfficial` scheme from current source with their own
Apple Team ID. The Team ID is deliberately outside measurement identity and
does not affect admission. Building the normal Developer scheme remains
measurement-locked regardless of who signs it.

The Results tab stores every completed Power 2 envelope independently and lets
the user select the exact saved result to share or submit. Direct GitHub
submission is fully connected to those stored bytes, uses OAuth Device Flow,
creates a new UUID branch directly from the current upstream head, writes only
the two-file Power 2 package, and opens a pull request. It never synchronizes
or modifies the contributor fork's default branch. The App does not compile
repository intake lifecycle into its source identity; trusted CI remains
fail-closed unless the immutable App release and public intake are active.

The `ios-app/` tree is a historical Power 1.1 App. No Power 1.1 result is
imported, converted, displayed, or submitted by this candidate.

`Power2ProductIdentity.generated.swift` is generated from the candidate
pointer before release and the active product pointer after cutover. It
centralizes immutable stack identity without compiling repository intake
state, Program, Target, policy, or compatibility versions into handwritten
Swift:

```bash
python3 scripts/generate_power2_product_identity.py --check
```

`Power2CandidateCatalog.generated.swift` is generated from the same candidate
hash chain plus its Program and model registry. It embeds only the exact
certification catalog and pinned workload/fixture bytes:

```bash
python3 scripts/generate_power2_app_catalog.py --check
```
