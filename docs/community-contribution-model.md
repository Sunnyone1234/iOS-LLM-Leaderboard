# Community contribution model

## Goal

Let iOS developers contribute reviewable physical-device evidence without
manually constructing benchmark JSON or learning the whole repository.

## Current flow

```text
official App → one physical-device run → untouched result export
→ contributor manifest → pull request → CI validation
→ maintainer merge → live community view
```

The App does not upload directly or write to `main`. The current contributor
creates a two-file package with:

```bash
python3 scripts/power.py submit /path/to/result.json \
  --github YOUR_GITHUB_HANDLE \
  --accept-declarations
```

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
frozen Power contract, and a live-ranking preview. Validation does not mutate
the result, assign Maintainer Reference status, or change an immutable release.

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

## Future convenience

A future service may create the same pull request after an in-App review. It
must preserve the two-file evidence boundary, contributor ownership, public
validation, and maintainer merge. Automation may reduce clicks; it must not
weaken reproducibility or bypass review.

Historical Framework v1 and Power 1.0 submission paths remain in versioned
directories for auditability. They are not the current public contribution
route.

See [Power 1.1 quickstart](../contributor-kit/power-1.1-quickstart.md) and
[live ranking policy](power-community-ranking.md).
