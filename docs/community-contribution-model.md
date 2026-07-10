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

An earlier MVP may export a bundle and open a prepared contribution flow before
full one-tap upload is implemented.

## Evidence Levels

| Level | Meaning | Default ranking |
| --- | --- | --- |
| Draft | Incomplete or local-only evidence | No |
| Community Submitted | One submission passes structural checks | No |
| Reproduced | Independent compatible evidence exists | Candidate |
| Verified | Full release, workload, configuration, and evidence rules pass | Yes |
| Maintainer Reference | Maintainer run using the official reference procedure | Yes, labeled |

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

- define maintainers and review authority;
- publish a code of conduct;
- publish benchmark proposal and release rules;
- add issue and pull-request templates;
- add automated schema and semantic validation;
- define conflict-of-interest disclosure;
- define correction, withdrawal, and deprecation procedures.
