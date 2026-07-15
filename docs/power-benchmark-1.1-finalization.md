# Power Benchmark 1.1 Finalization Checklist

This checklist prepares the formal Power 1.1 release. It does not itself grant
ranking, publication, tagging, or release authorization.

## RC freeze

- [x] Protocol `1.1.0-rc.1` frozen.
- [x] Result schema and base dependency pinned.
- [x] Validation-report schema and decision invariants pinned.
- [x] Independent validator and reason registry pinned.
- [x] Ranking policy pinned and fail-closed.
- [x] Fixtures, metric definitions, plans, registry, runtime, and App identity pinned.
- [x] Reference App 0.13.0 build 16 compiles in Release configuration.
- [x] Python contract and validator test suite passes.

## Intake and ranking boundary

- [x] Result/report digest and identity consumer implemented.
- [x] Stale, missing, unsupported, or mismatched reports fail closed.
- [x] RC reports cannot create measured or recommended ranking rows.
- [ ] Final `1.1.0` ranking policy prepared from the adopted RC without silently
  reinterpreting RC reports.
- [ ] Final report regeneration/revalidation plan reviewed.

## Physical-device evidence

- [ ] Six new RC raw results exist for the frozen three-model/two-workload matrix.
- [ ] Every result reports App 0.13.0 build 16 and source commit `f5b863c…`.
- [ ] Every result passes structural and protocol validation.
- [ ] Six hash-bound validation reports exist.
- [ ] Every result/report pair passes the independent consumer.
- [ ] Failures and replacement runs, if any, are retained and documented.
- [ ] Environment observations and deviations are reviewed.

## Release package

- [ ] Raw result inventory is complete and contains no duplicate result IDs.
- [ ] SHA-256 checksum file covers every raw result and validation report.
- [ ] Privacy review confirms no account, device name, UDID, serial number,
  personal prompt, or unrelated user data is present.
- [ ] Consistency review confirms exact model revisions, runtime, device, OS,
  workload, fixture, App, and protocol identities.
- [ ] Metric eligibility and behavior status are presented separately.
- [ ] Known limitations are complete.
- [ ] Release notes contain no unsupported performance or quality claim.
- [ ] Website/ranking change is generated from adopted reports, not handwritten.
- [ ] Full automated tests and reference App build pass at the release commit.

## Approval and publication

- [ ] Maintainer reviews the final package and exact checksums.
- [ ] Maintainer explicitly approves official-result adoption.
- [ ] Maintainer explicitly approves which metric-eligible results enter ranking.
- [ ] Maintainer explicitly authorizes merge, `1.1.0` tag, GitHub Release, and
  public leaderboard update.
- [ ] Release is published only after all prior boxes are complete.

Until the final approval is recorded, Power 1.0 remains the active public
release and Power 1.1 RC evidence remains non-official.
