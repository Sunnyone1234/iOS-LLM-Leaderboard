# Power community reproduction and live ranking

## Scope

The live view layers merged community evidence on top of the immutable Power
1.1 release. It changes no workload, source result schema, App measurement,
published result, checksum, or release tag. Historical valid Power 1.0
community packages remain visible under their original identity.

## Accepted current input

A current result enters the live dataset after its two-file Power 1.1 package:

1. is opened by the GitHub account named in `contributor.githubHandle`;
2. passes package, hash, source-result, exact-runner compatibility, and
   protocol validation; and
3. is merged into `main` by the repository's evidence-only automation or a
   maintainer.

The PR intake automation reads candidate JSON from the pull-request git object
while executing only trusted base-branch code. It accepts up to ten new
packages in one PR and assigns one of three outcomes:

| Outcome | Conditions | Repository action |
| --- | --- | --- |
| `power:auto-accept` | Evidence-only additions; author binding, hashes, declarations, frozen protocol, primary metric, ordinary environment, and duplicate checks all pass; no conflict is disclosed | Squash-merge after required checks |
| `power:manual-review` | The package is structurally valid, but a conflict or thermal/environmental assistance is disclosed | Preserve the evidence for maintainer review; do not auto-merge |
| `power:rejected` | Invalid/missing files, non-submission changes, contributor mismatch, unapproved runner identity, protocol or primary-metric failure, duplicate evidence, or more than ten packages | Fail intake and do not merge |

The merge worker runs only after trusted intake and commit-identity workflows
complete. It attempts the squash merge only for an open, non-draft PR carrying
`power:auto-accept`; repository rules still enforce all required checks. After
the merge it explicitly dispatches the ranking workflow, because GitHub does
not emit a second workflow run for ordinary events caused by `GITHUB_TOKEN`.
This automation assigns no formal Verified or Maintainer Reference status.

The `main` ruleset should require the uniquely named **Power submission
intake** and **Validate commit identity** checks, allow squash merges, and
require zero approving reviews. The intake workflow runs for every pull
request so the required check is never left pending by a path filter; PRs that
do not touch the current Power intake return `not_applicable` without labels or
automatic merge. Do not require the path-filtered ranking and Suite B checks
globally, because unrelated PRs would otherwise wait for checks that never
start. The repository-level **Allow auto-merge** option may remain enabled, but
the evidence worker does not depend on it.

The package records thermal assistance. `none` may enter the ordinary live
ranking; deliberate cooling, deliberate heating, other assistance, or
`unknown` remains evidence but is excluded from ordinary ranking calculations.

## Exact comparison cell

Independent contributors count together only when all comparison identity
fields match, including:

- source benchmark release and workload/fixture/mode;
- runner, App version/build/source commit;
- generation settings;
- model artifact/revision/content hash/quantization/tokenizer;
- runtime version/revision/backend/dependencies; and
- device machine identifier, physical memory, OS version, and OS build.

Changing one field creates a different exact cell. The website may group patch
releases for a simpler default display, but exact evidence identities remain
separate in the dataset.

Compatibility policy 1.1.4 preserves the App 0.13.0 reference, exact App
0.16.0 build 19 approval, and both exact App 0.17.0 build 20 source identities.
It also approves App 0.18.0 build 21 only at protected-merge commit
`8920a423f4b4abff4e34a2d8a128a3962899258e`. It does not reinterpret App
0.14.0 or 0.15.0 evidence and it does not pre-approve later App commits.

## Contributor counting

- GitHub handle matching is case-insensitive.
- One account counts once per exact cell.
- The same account may count in any number of different cells.
- All valid repeated runs remain linked as evidence.
- A copied result is rejected by duplicate SHA-256, result ID, or session ID.
- Each metric first takes a median per contributor, then a median across those
  contributor medians.

| Eligible contributors | Live display |
| ---: | --- |
| 1 | Single contributor |
| 2 | Reproduced |
| 3 or more | Reproduced with community aggregate |

Metric-ineligible or environmentally assisted evidence remains in the run and
evidence counts but does not supply the displayed metric or eligible
contributor count.

## Variation

Primary-metric variation is median absolute deviation across per-contributor
medians, divided by their median. Above 10% is labeled `High variation`.
Variation is a warning, not an automatic exclusion.

## Automatic publication

```text
App export → contributor-owned PR → trusted CI triage and ranking preview
→ automatic or maintainer merge → deterministic generation → one GitHub Pages deploy
```

Generated files:

- `results/suite-b-power-community/normalized-results.json`;
- `results/suite-b-power-community/LEADERBOARD.md`;
- `results/suite-b-power-community/COVERAGE.md`.

Maintainers can request the same current preview through the **Power community
ranking** workflow. The retained public `scripts/power.py preview` command is
an immutable Power 1.1.1 asset; trusted CI uses the separately pinned 1.1.4
adapter without changing that historical command.

The live view does not grant a formal evidence-level transition. Verified and
Maintainer Reference remain separate review and release decisions.
