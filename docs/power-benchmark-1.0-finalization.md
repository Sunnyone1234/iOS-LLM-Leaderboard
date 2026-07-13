# Power Benchmark 1.0 Finalization

## Status

The complete Power Benchmark 1.0 package is prepared for final maintainer
review. Publication, official-result status, the default ranking, the
`1.0.0` tag, and the GitHub Release remain disabled until that review is
approved.

This finalization does not change a workload, benchmark rule, model, result
schema, validator, or App implementation.

## Exact RC adoption without rerun

The final package reuses the six genuine F5 results because the executable and
normative contracts that determine their meaning did not change after those
runs:

| Contract | Adopted identity | Changed after F5? |
| --- | --- | --- |
| Reference App | `0.8.0` build `10`, source `2f105ff463bc9b281b19655ba711b1ca7dee8759` | No |
| Benchmark protocol | `suite-b-power@1.0.0-rc.1` | No |
| Result schema | `suite-b-power-result-1.0.0-rc.1` | No |
| Semantic validator | `suite-b-power-validator@1.0.0-rc.1` | No |
| Workloads | B-UX-001 and B-PIPE-001 at `1.0.0-rc.1` | No |
| Metric and eligibility rules | Frozen F2/F3 rules | No |

The raw JSON files and validation reports remain in their original RC1
directory with their original identities and bytes. The final publication
layer does not copy, edit, or relabel them. Instead,
[`evidence-adoption.json`](../results/suite-b-power-1.0/evidence-adoption.json)
binds each result by path, SHA-256, `resultID`, `sessionID`, workload, and model
artifact. The final generator recomputes validation and rejects any mismatch.

This is the required reproducibility boundary: no rerun is needed when the
benchmark semantics and runner are identical, but source provenance must stay
visible and immutable.

## Final package

- [release manifest](../benchmarks/suite-b-on-device-performance/releases/suite-b-power-1.0.0.json);
- [evidence-adoption manifest](../results/suite-b-power-1.0/evidence-adoption.json);
- [normalized leaderboard data](../results/suite-b-power-1.0/normalized-results.json);
- [Markdown leaderboard](../results/suite-b-power-1.0/LEADERBOARD.md);
- [release notes](../results/suite-b-power-1.0/RELEASE-NOTES.md); and
- [SHA-256 manifest](../results/suite-b-power-1.0/SHA256SUMS).

The package contains six physical-device results. Five have an eligible
primary metric and form the candidate ranking. The Qwen3 0.6B Short Interaction
result is preserved but unranked because all five responses failed the frozen
response-conformance gate.

## Release checklist

### Benchmark and evidence

- [x] Exactly the two frozen Power workloads are included.
- [x] No benchmark, workload, schema, validator, model, or App change is
      introduced.
- [x] Six genuine physical-device results are retained without modification.
- [x] All six results pass structural and protocol validation.
- [x] Every ranked metric is independently recalculated from raw evidence.
- [x] The ineligible response outcome remains visible and unranked.
- [x] Source RC1 identities remain visible in data and presentation.
- [x] Raw evidence, validation reports, adoption manifest, and generated files
      are covered by SHA-256 verification.

### Presentation and documentation

- [x] The website reads only the Power 1.0 normalized dataset.
- [x] Candidate and active ranking states are distinct.
- [x] Sortable UX and sustained-generation tables use their frozen primary
      metrics.
- [x] Raw evidence is linked from every displayed row.
- [x] No global score or Ship score is introduced.
- [x] Known limitations and the no-rerun decision are documented.

### Final maintainer authorization

- [ ] Confirm all seven contributor declarations below.
- [ ] Approve the final release manifest and complete generated package.
- [ ] Authorize official-result status for the six adopted results.
- [ ] Authorize the five eligible rows for the default ranking.
- [ ] Authorize the `1.0.0` GitHub Release and tag.

## Contributor declarations to confirm

For the six maintainer-run F5 results, the maintainer must confirm that:

1. the runs used a physical device;
2. the maintainer is authorized to submit the evidence;
3. every public metadata field was reviewed;
4. each raw JSON file is the unmodified App export;
5. the package contains no personal data;
6. benchmark evidence is contributed under CC BY 4.0; and
7. submission does not by itself guarantee acceptance, verification, or
   ranking.

The public contributor identity is `YizeSun`. The final approval must also
state the applicable conflict-of-interest category and statement.

## Known limitations

- Coverage is one `iPhone15,3`, one OS build, MLX Swift LM, and one model
  family with three exact artifacts.
- First-renderable proxy TTFT is an adapter observation, not a display-frame or
  screen-paint measurement.
- Five measured sustained attempts do not support a general battery-life or
  long-duration thermal claim.
- The benchmark does not establish minimum supported hardware, compatibility
  with untested runtimes, or App Store approval.
- License metadata is informational and not legal advice.

## After approval

Final publication is a mechanical activation step: record confirmed
declarations, set the final manifest publication/result/ranking/tag flags,
regenerate and verify the same package, merge it, create the `1.0.0` tag and
GitHub Release, and verify the deployed leaderboard. Only then does the project
begin the separate Ship implementation phase.
