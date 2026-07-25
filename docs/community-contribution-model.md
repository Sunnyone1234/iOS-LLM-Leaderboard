# Community contribution model

## Goal

Let iOS developers contribute reviewable physical-device Power evidence
without hand-writing benchmark JSON or learning the repository control plane.

The only current public result path is Power 2:

```text
current source checkout
→ locally signed Official configuration
→ physical-iPhone run
→ immutable two-file package
→ contributor-owned pull request
→ trusted base-repository intake
→ Accepted / manual review / rejected
→ deterministic ranking view
```

Power 1.0, Power 1.1, and Framework v1 packages, tools, and review records are
read-only audit assets. They are not compatibility inputs or alternate public
submission paths.

## Two pull-request lanes

Result PRs and ordinary repository PRs are intentionally separate.

| Lane | Scope | Automation |
| --- | --- | --- |
| Power evidence | Only complete UUID-named `result.json` + `submission.json` packages under the current Power 2 submission root | Trusted intake may label and automatically merge |
| Code, docs, policy, App, or infrastructure | Normal focused repository changes; never mixed with result packages | Normal review and required checks; no evidence auto-accept |

This separation prevents a submitted result from executing contributor code
and prevents evidence-only automation from merging unrelated repository
changes.

## Source-built identity and trust

Contributors build and sign the supported Official configuration locally with
their own Apple Team ID. Team identity is not benchmark identity. The App
embeds the repository-generated App release declaration, but a local build
cannot cryptographically prove that its installed binary came from unmodified
source.

The trust language is therefore:

| Evidence state | Meaning |
| --- | --- |
| Accepted | One eligible contributor supplied self-declared source-built evidence whose bytes, identities, declarations, and current contracts pass trusted CI |
| Reproduced | Two independent eligible GitHub accounts supplied matching evidence in the exact comparison cell |
| Contributor-weighted | Three or more independent eligible accounts permit per-contributor reduction before cross-contributor aggregation |

`Accepted` is not a verified-binary claim. Independent reproduction is the
first confidence increase. No contributor, App field, label, or manual button
may self-assign `Reproduced`.

One case-insensitive GitHub account counts once per exact cell. Repeated valid
runs remain evidence and are reduced to one per-contributor median before
cross-contributor aggregation.

## Privacy and evidence boundary

Expected public technical fields include exact device model, OS version/build,
App release declaration, Program, Target, workload, model artifact, Runtime,
Runner certificate, inference settings, attempts, failures, timing, memory,
thermal observations, and integrity hashes.

The package must not collect Apple ID, serial number, UDID, device name,
personal prompts, user documents, or unrelated App data. `result.json` is
preserved byte-for-byte. `submission.json` adds the contributor identity,
conflict and environment disclosures, declarations, and CC BY 4.0 acceptance.

## Trusted automation boundary

The App creates a new fork branch from the exact current upstream head and
opens a result-only PR. It never updates the contributor fork's default branch.

`pull_request_target` intake executes only trusted base-branch code. Candidate
files are fetched as data and never executed. Intake validates:

- the current two-file package shape and immutable result digest;
- the contributor/PR-author binding and required declarations;
- exact current Program, Target, workload, model, Runtime, Runner certificate,
  and App release declarations;
- physical-device and admission requirements;
- duplicate result/session identity;
- structural, protocol, behavior, recommendation, and per-metric eligibility;
- result-only PR scope.

Clean ordinary evidence receives `power:auto-accept`; disclosures requiring a
human decision receive `power:manual-review`; hard failures receive
`power:rejected`. Accepted failures, cancellations, OOMs, and metric-ineligible
attempts remain evidence even when they cannot supply a ranking metric.

See the [Power contributor guide](../contributor-kit/power.md) for the user
flow and [Power ranking policy](power-community-ranking.md) for aggregation.
