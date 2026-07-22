# Community contribution model

## Goal

Let iOS developers contribute reviewable physical-device evidence without
manually constructing benchmark JSON or learning the whole repository.

## Current flow

```text
official App → one physical-device run → untouched result export
→ contributor manifest → pull request → CI validation
→ automatic acceptance or maintainer review → live community view
```

A configured App can create the contributor-owned fork, evidence commit, and
pull request through GitHub device authorization. It never writes directly to
`main`. App 0.17.0 builds without the public OAuth Client ID may export the raw
result for backup, but must be configured and rebuilt before submission. The
retained `scripts/power.py` command is pinned to compatibility policy 1.1.1
and is not a bypass for a runner added by policy 1.1.2.

The package lives under
`submissions/suite-b/power-1.1.0/draft/<submission-id>/`. `result.json` is
byte-for-byte the App export. `submission.json` binds it to the final Power 1.1
release, contributor, conflict disclosure, environment disclosure, and license
declarations.

The pull-request author must match the declared GitHub handle. App Attest,
UDID, serial number, and persistent device fingerprints are not required.

## Privacy boundary

Expected public technical fields include device model, OS version/build, App
and benchmark release, model artifact and runtime identity, inference settings,
raw measurements, thermal observations, failures, and integrity hashes.

The App and package must not collect Apple ID, serial number, UDID, device
name, personal prompts, user documents, or unrelated app data.

## Validation and publication

CI validates package shape, raw hash binding, contributor declarations, the
frozen Power contract, the versioned exact-runner allowlist, duplicate
identity, and a live-ranking preview. Clean
evidence-only PRs are labeled `power:auto-accept` and may auto-merge after
required checks. Valid conflict or environmental-assistance disclosures route
to `power:manual-review`; invalid, incompatible, duplicated, or mixed-scope
PRs route to `power:rejected`. Validation does not mutate the result, assign
Maintainer Reference status, or change an immutable release.

The original App 0.13.0 reference remains valid. Current policy 1.1.2 also
accepts App 0.16.0 build 19 and App 0.17.0 build 20 only at their approved App
source commits and runtime identity. App 0.15.0 evidence remains
`runner_incompatible`; a second
contributor or manual review cannot convert an unapproved runner into valid
evidence.

Merging a valid package makes it eligible for the live community evidence view
when its primary metric and ordinary thermal policy are eligible. Deliberate
cooling, deliberate heating, other assistance, or unknown assistance is
retained but not included in the ordinary live ranking.

## Evidence language

| Display or evidence term | Meaning |
| --- | --- |
| Unreviewed | Valid merged package without a formal trust transition |
| Single contributor | One metric-eligible GitHub account in an exact cell |
| Reproduced | Two or more independent eligible accounts in an exact cell |
| Community aggregate | Three or more independent eligible accounts |
| Verified | A separate formal review confirms the required release and evidence rules |
| Maintainer Reference | Maintainer-run reference evidence published by a release decision |

The live `Reproduced` label is a deterministic contributor-count fact. It does
not silently rewrite the formal trust level.

One case-insensitive GitHub account counts once per exact comparison cell and
may contribute to any number of different cells. Repeated eligible runs are
retained, then reduced to one per-contributor median before cross-contributor
aggregation.

## Automation boundary

The in-App flow preserves the two-file evidence boundary, contributor
ownership, and public validation. Automatic merge applies only to new package
files that pass all ordinary ranking gates. Disclosed conflicts and assisted
environments remain human decisions; frozen runner incompatibility and invalid
evidence cannot be overridden by the App.

Historical Framework v1 and Power 1.0 submission paths remain in versioned
directories for auditability. They are not the current public contribution
route.

See [Power 1.1 quickstart](../contributor-kit/power-1.1-quickstart.md) and
[live ranking policy](power-community-ranking.md).
