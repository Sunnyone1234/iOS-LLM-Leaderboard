# Community Contribution Model

## Goal

Enable many iOS developers to contribute real-device benchmark evidence without
requiring them to understand the repository schema or manually construct result
JSON.

## Intended Contributor Flow

1. Install the official benchmark app.
2. Select a compatible model profile and benchmark release.
3. Download required artifacts before measurement.
4. Run the locked procedure.
5. Review the result and every field that will be submitted.
6. Submit the result bundle.
7. Allow repository validation to create or update a contribution.

The target experience is one-tap submission after review.

## Submission Boundary

The app should submit benchmark evidence, not personal device identity.

Expected fields include:

- public device model and chip;
- OS version and build;
- benchmark app and release version;
- model artifact and runtime identity;
- inference settings;
- raw and aggregated measurements;
- thermal and failure observations;
- result integrity hash.

The app should not collect:

- Apple ID;
- device serial number;
- UDID;
- user documents;
- personal prompts;
- unrelated app data.

## Repository Entry

The app should not write directly to the default branch.

A submission service or GitHub App should:

1. receive the result bundle;
2. perform initial validation;
3. create a pull request or bot-managed submission;
4. attach validation findings;
5. allow public review.

The historical offline MVP exports `suite-b-community-submission-0.1`. It embeds
the exact unified result bytes as Base64, records their SHA-256 digest, and
requires review, a no-personal-data confirmation, and license acceptance. It
does not upload or create a pull request. Every App-generated package starts as
`Draft` and only requests `Community Submitted`; repository validation and
review control transitions.

```bash
python3 scripts/validate_suite_b_submission.py path/to/submission.json
```

Power 1.0 public intake preserves the App's adopted RC1 result as a standalone,
byte-exact `result.json` and adds a contributor-owned `submission.json`. This
avoids Base64 duplication and lets repository validation run the frozen Power
semantic validator directly without changing the App export. See the
[Power 1.0 public-intake guide](power-benchmark-1.0-public-intake.md) and the
pinned [RC1 package definition](power-benchmark-1.0-submission.md).

## Evidence Levels

| Level | Meaning | Default ranking |
| --- | --- | --- |
| Draft | Incomplete or local-only evidence | No |
| Community Submitted | One submission passes structural checks | No |
| Reproduced | Independent compatible evidence exists | Candidate |
| Verified | Full release, workload, configuration, and evidence rules pass | Yes |
| Maintainer Reference | Maintainer run using the official reference procedure | Yes, labeled |

The App cannot assign Reproduced, Verified, or Maintainer Reference status.

The live Power community view separately derives contributor counts from
valid merged packages. Inside one exact comparison cell, two different GitHub
accounts display as `Reproduced` and three or more enable a community
aggregate. This display is not a formal evidence-level transition. One account
counts once per cell but may participate in any number of different cells. See
[Power Community Reproduction and Live Ranking](power-community-ranking.md).

Power 1.0 intake stores immutable two-file packages under
`submissions/suite-b/power-1.0.0-rc.1/draft/`. CI emits structural, semantic,
integrity, and declaration findings but does not alter trust. Separate review
records control evidence transitions. The RC1 path is retained because it is
the exact source contract adopted by Power 1.0. Historical Pilot packages remain under
`submissions/suite-b/draft/`. See
[Community Submissions](../submissions/README.md).

Evidence level describes the submission process, not permanent truth.

## Low-friction Contribution Principles

- auto-detect metadata where public APIs allow;
- keep measured settings locked by the benchmark release;
- show progress and expected test duration;
- retain failures rather than asking contributors to repeat until fast;
- let contributors inspect data before upload;
- provide useful local results even when the contributor does not submit;
- publish device-coverage gaps that the community can help fill.

## Governance Requirements

Before public result intake:

- [x] define maintainers and review authority;
- [x] publish a code of conduct;
- [x] publish benchmark proposal and release rules;
- [x] add pull-request submission and review checklists;
- [x] add automated schema and semantic validation;
- [x] define conflict-of-interest disclosure;
- [x] define correction, withdrawal, and deprecation procedures;
- [x] receive explicit maintainer approval to open public Power intake.
