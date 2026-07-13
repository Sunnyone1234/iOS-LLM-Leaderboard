# Power Benchmark 1.0 RC1 Review Package

## Decision status

`suite-b-power@1.0.0-rc.1` is ready for maintainer review as a release
candidate. It is not an official release, does not authorize ranking, and must
not be tagged or published without an explicit maintainer decision.

This package completes the F6 governance implementation candidate. It does not
change the F2/F3 protocol, result schema, validator, workload, metric, or App
contracts and does not rewrite F5 evidence.

## Candidate contents

The RC1 review package binds:

- the immutable F3 release manifest and every pinned protocol asset;
- App 0.8.0 build 10 at source commit
  `2f105ff463bc9b281b19655ba711b1ca7dee8759`;
- the six-result F5 physical-device verification evidence and checksums;
- the Power RC1 two-file submission manifest and package creator;
- semantic package validation using the frozen Power result validator;
- hash-bound evidence-review transitions and independent reproduction checks;
- maintainer authority, contributor conduct, privacy, conflict disclosure,
  corrections, withdrawal, deprecation, and release-history rules; and
- this release gate, known-limitations inventory, and publication boundary.

The machine-readable publication candidate manifest is
`benchmarks/suite-b-on-device-performance/releases/suite-b-power-1.0.0-rc.1-publication-candidate.json`.

## Release checklist

### Frozen benchmark scope

- [x] Exactly B-UX-001 and B-PIPE-001 are included.
- [x] Workload, fixture, mode, metric, attempt, failure, and eligibility
      identities are frozen.
- [x] Historical Pilot evidence cannot be relabeled or promoted.
- [x] The result schema and semantic validator are pinned together.

### Reference implementation and evidence

- [x] App 0.8.0 build 10 executes only compatible release identities.
- [x] Completed, failed, cancelled, OOM, and not-run outcomes are retained.
- [x] Raw evidence independently recalculates every candidate metric.
- [x] The declared three-model, one-runtime, one-device F5 matrix is complete.
- [x] Raw files and validator reports have verified SHA-256 checksums.
- [x] Integrity and privacy review found no prohibited identifier.
- [x] The 0.6B Short Interaction response failure remains ineligible evidence.

### Submission and evidence governance

- [x] The official-candidate package contains an untouched result plus a
      separate contributor declaration manifest.
- [x] Package identity, digest, schema, protocol, declarations, privacy, and
      conflict disclosure are validated before review.
- [x] Passing intake leaves evidence unreviewed and ranking-ineligible.
- [x] Evidence transitions are separate, append-only, hash-bound records.
- [x] Independent reproduction requires compatible evidence, different public
      contributors, and distinct result/session IDs.
- [x] Metric eligibility remains separate from evidence level.
- [x] Correction, withdrawal, privacy removal, deprecation, appeal, and release
      history procedures are documented.
- [x] Maintainer authority and the code of conduct are published.

### Automation and documentation

- [x] Repository CI validates both historical Pilot and Power RC1 paths.
- [x] Empty intake is valid and cannot change evidence or ranking state.
- [x] Submission and review regression tests cover integrity, declarations,
      metric-ineligible evidence, and reproduction independence.
- [x] Contribution and pull-request documentation identify RC1 as non-official.
- [x] Known limitations and unsupported claims are published.

### Explicit decisions still required

- [ ] The maintainer approves the RC1 review package.
- [ ] The maintainer chooses whether to publish RC1 as a non-official release
      candidate or authorize creation of distinct final `1.0.0` identities.
- [ ] Any F5 result intended for an evidence level receives an explicit
      contributor manifest and hash-bound review; F5 files are not silently
      promoted.
- [ ] Any official default ranking is authorized separately and includes only
      metrics whose eligibility decision is true.
- [ ] A GitHub Release and version tag are created only after approval.

## Validation performed

The F6 candidate must pass:

```bash
python3 -m unittest discover -s tests

python3 scripts/validate_suite_b_power_submission.py \
  submissions/suite-b/power-1.0.0-rc.1/draft

python3 scripts/validate_suite_b_power_reviews.py \
  --submissions submissions/suite-b/power-1.0.0-rc.1/draft \
  --reviews submissions/suite-b/power-1.0.0-rc.1/reviews

cd results/suite-b-power-1.0.0-rc.1/f5-device-verification
shasum -a 256 -c SHA256SUMS
```

The submission and review directories intentionally contain no fabricated
example result. Empty intake proves the governance path without creating trust
or leaderboard data.

## Known limitations

- F5 covers one iPhone model, OS build, runtime, and model family.
- F5 is verification evidence, not a substitute for contributor declarations
  or evidence-level review.
- The frozen validator reports F5 evidence as `unreviewed` and ranking false.
- Qwen3 0.6B Short Interaction has no eligible metric because every response
  failed the frozen lexical conformance gate.
- First-renderable proxy TTFT is measured in the adapter and is not a display
  frame or screen-paint measurement.
- Five measured sustained attempts are not a broad thermal, battery-life, or
  long-duration stability claim.
- The benchmark does not prove minimum supported hardware, App Store approval,
  offline distribution, or compatibility with untested runtimes.
- License fields are source metadata and do not constitute legal advice.
- RC1 enables no global score and no Ship deployment score.

## RC1 versus final 1.0

RC1 identities contain the literal version `1.0.0-rc.1`. They cannot be
renamed in place to `1.0.0`. If the maintainer approves a final 1.0 release,
the project must create final versioned manifests/schemas/validator/App
identity without changing semantics, preserve RC1 history, and collect new
result exports for any official final-identity rows.

Publishing RC1 as an openly reviewable candidate is a smaller decision and
does not itself authorize final 1.0 results or ranking.

## Recommended maintainer decision

Review and merge the F6 candidate first while retaining all publication flags
as false. Then choose one explicit next action:

1. publish the exact RC1 package as non-official for wider review; or
2. approve final 1.0 identity preparation and its required final App/result
   verification.

Neither action is implied by approving this document or merging its pull
request.
