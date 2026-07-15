# Power community reproduction and live ranking

## Scope

The live view layers merged community evidence on top of the immutable Power
1.1 release. It changes no workload, source result schema, App measurement,
published result, checksum, or release tag. Historical valid Power 1.0
community packages remain visible under their original identity.

## Accepted current input

A current result enters the live dataset after its two-file Power 1.1 package:

1. is opened by the GitHub account named in `contributor.githubHandle`;
2. passes package, hash, source-result, and protocol validation; and
3. is merged into `main` by a maintainer.

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
App export → contributor-owned PR → CI validation and ranking preview
→ maintainer merge → deterministic generation → one GitHub Pages deploy
```

Generated files:

- `results/suite-b-power-community/normalized-results.json`;
- `results/suite-b-power-community/LEADERBOARD.md`;
- `results/suite-b-power-community/COVERAGE.md`.

Run the same generator locally with `python3 scripts/power.py preview`.

The live view does not grant a formal evidence-level transition. Verified and
Maintainer Reference remain separate review and release decisions.
