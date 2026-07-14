# Power Community Reproduction and Live Ranking v1

## Status

This policy defines the live community view layered on top of the immutable
Power Benchmark 1.0 release. It changes no workload, result schema, validator,
App, metric, or published Power 1.0 file.

The live view deliberately uses a low-friction community trust model. App
Attest, UDID, serial number, and persistent device fingerprints are not
required or collected.

## Accepted community input

A community result enters the live dataset after its two-file Power package:

1. is opened by the GitHub account named in
   `contributor.githubHandle`;
2. passes the frozen package and Power result validators; and
3. is merged into `main` by a maintainer.

The maintainer also reviews the pull request's
[Power 1.0 environmental observations](../benchmarks/suite-b-on-device-performance/power-1.0-environment-control.md).
Temperature, case, and placement are non-blocking context in the current draft.
A result declared as deliberately cooled, heated, or otherwise thermally
assisted, or left `unknown`, is not merged into the ordinary live intake. It
remains reviewable in its pull request until the declaration is clarified or a
separately labeled intake path is implemented. The current generator has no
post-merge environmental exclusion field; the frozen result and submission
schemas are unchanged.

The pull-request check compares the declared handle with the PR author
case-insensitively. A merged valid package may appear in the live community
view while its formal evidence level remains `unreviewed`. Formal,
hash-bound evidence transitions remain governed by the frozen Power review
contract and are not assigned by the live-ranking generator.

## Exact comparison cell

Independent contributors are counted only inside an exact comparison cell.
The cell includes:

- source benchmark release;
- workload ID, version, category, fixture hash, and measurement mode;
- runner and App version, build, and source commit;
- every locked generation setting;
- model artifact, revision, content hash, quantization, format, and tokenizer;
- runtime version, resolved revision, backend, and dependency versions; and
- device machine identifier, physical memory, OS version, and OS build.

Changing any of these fields creates a different comparison cell. The same
GitHub account can therefore contribute independently to any number of
different workloads, models, devices, runtimes, operating systems, or other
configurations.

## Contributor counting and repeated runs

GitHub handle matching is case-insensitive. Within one exact comparison cell:

- one GitHub account counts as one contributor;
- all valid runs remain visible and linked as evidence;
- repeated runs by one account do not increase the contributor count; and
- for each metric, repeated runs first produce a per-contributor median, then
  the live cell value is the median across contributor medians.

This gives every contributor equal weight without discarding repeat-run
evidence. A copied result is not a new run: duplicate result SHA-256, result
ID, or session ID is rejected across the complete live dataset.

## Derived live statuses

| Independent metric-eligible contributors in one cell | Live display |
| ---: | --- |
| 1 | Single contributor |
| 2 | Reproduced |
| 3 or more | Reproduced with community aggregate |

Only contributors whose result is eligible for the displayed primary metric
count toward these statuses. Metric-ineligible evidence remains linked and
included in the total run count. `Reproduced` in the live table is a
deterministic contributor-count fact. It
does not silently grant the frozen `reproduced` evidence level, Verified
status, or Maintainer Reference status.

## Variation

Primary-metric variation is the median absolute deviation across the
per-contributor metric medians, divided by their median and expressed as a
percentage. A value above 10% is labeled `High variation`.

This warning never excludes a result, changes protocol validity, or prevents
the cell from being reproduced. The raw evidence remains available so the
community can investigate thermal state, OS differences, or other causes.

## Automatic publication path

```text
App export
→ contributor-owned pull request
→ package, protocol, hash, and GitHub-handle checks
→ thermal-assistance disclosure review (`none` required for ordinary intake)
→ maintainer merge
→ exact-cell matching and contributor-weighted aggregation
→ GitHub Pages regeneration
```

The generated live files are:

- `results/suite-b-power-community/normalized-results.json`; and
- `results/suite-b-power-community/LEADERBOARD.md`; and
- `results/suite-b-power-community/COVERAGE.md`.

The published `results/suite-b-power-1.0/` package and the `1.0.0` tag remain
unchanged. The website labels the combined view as Power 1.0 plus Community
evidence and continues to link the immutable official checksums.
