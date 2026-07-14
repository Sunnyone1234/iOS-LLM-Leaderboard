# Suite B Power Benchmark 1.1 Protocol Draft

## Status and scope

Protocol `suite-b-power@1.1.0-draft.1` is a non-official design contract for
the next Power release. It does not authorize results, ranking, publication,
or a GitHub tag. Power 1.0 remains the active published benchmark and its raw
evidence, eligibility decisions, and public ranking are unchanged.

The machine-readable companion is
[`power-1.1-protocol.json`](power-1.1-protocol.json).
The minimal internal validation-report contract is
[`suite-b-power-validation-report-1.1.0-draft.1.schema.json`](../../schemas/suite-b-power-validation-report-1.1.0-draft.1.schema.json).
The submitted App evidence contract is
[`suite-b-power-result-1.1.0-draft.1.schema.json`](../../schemas/suite-b-power-result-1.1.0-draft.1.schema.json).

Power 1.1 retains exactly the two Power 1.0 workload IDs:

| Workload identity | Role |
| --- | --- |
| `b-ux-001-short-interaction@1.1.0-draft.1` | warm-resident short-interaction responsiveness |
| `b-pipe-001-sustained-generation@1.1.0-draft.1` | sustained pipeline generation and thermal-transition evidence |

No workload category, fixture, prompt, generation setting, timing boundary,
metric formula, device requirement, or attempt count is added or changed by
this draft. Unless this document states otherwise, the execution and evidence
contract is inherited from `suite-b-power@1.0.0-rc.1`.

The 1.1 change is deliberately narrow:

> A benchmark App exports every technically derivable measurement. The
> independent submission validator decides behavior conformance, metric
> eligibility, performance-ranking eligibility, and recommendation eligibility.

## Responsibility boundary

### Benchmark App

The App is an evidence producer, not the authority that admits a submission or
updates a public ranking. It must:

1. retain one record for every planned attempt;
2. retain generated text, token events, timing evidence, the bounded
   first-renderable trace, memory samples, and thermal observations;
3. calculate and export every metric supported by the attempt's technical
   evidence;
4. export `null` only when the metric's own technical prerequisites are not
   satisfied; and
5. never set a technically derivable metric to `null` solely because generated
   text failed a behavior or response-conformance check.

The App may display a local behavior-conformance preview for operator feedback,
but that preview is advisory. It must not be trusted as the submission decision
and must not alter raw evidence or derived performance values.

### Submitted result contract

Power 1.1 preserves the complete submitted field shape of the frozen Power 1.0
result schema. No contributor-authored field is added. The new result schema
changes only the schema, release, protocol, and workload version identities and
the semantics governing existing evidence.

The existing per-attempt `responseConformance` member remains in the App JSON
for wire compatibility and immediate operator feedback, but it is explicitly
advisory. The independent validator recomputes behavior from retained generated
text and does not trust that member. Likewise, each `derivedMetrics` value and
each summary metric is independent of the App's advisory response assessment.

JSON Schema validates the result's structure. The independent semantic
validator enforces cross-field facts that JSON Schema cannot prove, including
metric recalculation and the rule that a technically derivable metric cannot be
`null` solely because behavior was not verified.

### Submission validator

The independent validator is the sole authority for submitted-result decisions.
It must recompute facts from immutable submitted evidence rather than trust an
App badge or local decision. Its report keeps these decisions separate:

- **structural validity**: the bundle matches the versioned schema;
- **protocol conformance**: execution identity and frozen settings match 1.1;
- **measurement eligibility**: each metric is supported by its own raw evidence;
- **behavior conformance**: the workload behavior is `verified`,
  `not_verified`, or `contradicted` when a behavior policy applies;
- **performance-ranking eligibility**: the primary performance metric is
  measurement-eligible and the evidence level is allowed by ranking policy;
  and
- **recommendation eligibility**: performance-ranking eligibility passes and
  behavior is `verified` when a behavior policy applies.

Validation never rewrites the submitted result. Trust or ranking transitions
remain governed by review records and cannot be granted by App output or CI
alone.

### Submission-time fact determination

The independent validator runs during submission intake and review, before a
result can be consumed by a public ranking. It produces a versioned,
immutable validation report bound to the exact submitted result SHA-256. The
report must identify the result-schema version, protocol version, validator
version, and ranking-policy version used for its decisions.

The report is the authoritative record of structural validity, protocol
conformance, per-metric measurement eligibility, behavior conformance,
performance-ranking eligibility, and recommendation eligibility. Every
non-affirmative decision retains machine-readable reason codes. A
`not_verified` or `contradicted` behavior assessment does not make otherwise
valid evidence disappear or prevent it from being retained as an accepted
submission.

The report is generated automatically by repository validation. It is an
internal derived artifact, not a second file that a contributor creates or
uploads. It contains decisions and version identities only; raw token, timing,
memory, thermal, and generated-text evidence remains exclusively in the exact
submitted result.

### Ranking-time policy application

The leaderboard is a consumer of the validation report, not a second
conformance implementation. It must not infer conformance from an App field or
reimplement the validator's rules against raw evidence. Before displaying a
result it verifies that:

1. the validation-report version is supported;
2. the report's result SHA-256 matches the exact submitted result;
3. the report names the expected protocol, validator, and ranking-policy
   versions; and
4. the relevant eligibility decision is affirmative.

The measured-performance view applies `performance-ranking-eligibility`; the
recommended view applies `recommendation-eligibility`. Missing, stale,
unsupported, or digest-mismatched reports fail closed and cannot affect a
ranking. A leaderboard build may invoke the independent validator as a
deterministic prerequisite, but it must consume the resulting report rather
than maintain duplicate conformance logic.

Changing a conformance or ranking policy requires a new policy version and a
new validation report. Historical reports and rankings must never be silently
reinterpreted under changed rules.

## Short Interaction behavior contract

Power 1.1 retains the frozen `short-interaction-response-v1` check while making
its role explicit. The submission validator normalizes the retained generated
text with Unicode NFKC, case-folds it, and collapses whitespace. The response
must be nonempty, contain no more than two sentences, express that the note is
safe locally, and express that synchronization will occur when connectivity
returns.

For an applicable behavior policy, the validator records exactly one of:

- **`verified`**: the frozen deterministic policy proves the required concepts;
- **`not_verified`**: the policy cannot prove all required concepts; this is
  not a claim that the response is semantically wrong; or
- **`contradicted`**: a frozen deterministic rule positively proves a conflict
  with the required behavior.

A policy non-match defaults to `not_verified`. `contradicted` may be emitted
only when the policy version defines positive contradiction evidence. Because
`short-interaction-response-v1` defines no such contradiction rule, a correct
synonym such as `secure` that does not match its literal `safe` check is
`not_verified`, not failed or contradicted.

An assessment other than `verified`:

- does not invalidate structurally valid execution evidence;
- does not erase or null a technically derivable performance metric;
- does not exclude the configuration from a metric-specific performance view;
  and
- does make the result ineligible for a behavior-verified recommendation
  view.

`short-interaction-response-v1` remains intentionally visible in evidence so a
future behavior policy can be versioned without silently reinterpreting 1.1.

## Measurement export and eligibility

Eligibility is decided per attempt and per metric. Behavior conformance is not
a technical prerequisite for any metric.

| Metric | Technical attempt requirements | Behavior gate |
| --- | --- | --- |
| Pipeline TTFT | completed; token event zero exists; generation boundary and monotonic clock verified | none |
| First-renderable proxy TTFT | Short Interaction only; completed; valid trace outcome `firstRenderableFound` | none |
| Request completion | Short Interaction only; completed; request origin and completion event retained | none |
| Prefill throughput | completed; exact prompt count; positive explicit prompt-evaluation duration | none |
| Decode throughput | completed; at least two raw events; positive first-to-last interval | none |
| Process physical footprint | completed; at least one valid in-window 50 ms sample | none |
| Decode first-to-last change | Sustained Generation only; first and last measured attempts are decode-eligible and all six planned records exist | none |
| Thermal-transition evidence | Sustained Generation only; all planned records exist and required states are not `unknown` | none |

The first-renderable proxy remains an adapter observation, not screen-render or
human-perceived latency. It requires proof of renderable decoded content, but
not proof that the completed response is semantically conformant.

Request-completion values must be displayed with actual output-token count and
stop reason because response length affects completion time. It is not the
primary responsiveness ranking metric.

## Public views

Power 1.1 defines no combined score. Public views must distinguish:

- **Measured performance**: includes measurement-eligible configurations and
  ranks only the selected metric;
- **Behavior status**: shows `Verified`, `Not verified`, or `Contradicted`
  exactly as recorded by the validator; and
- **Recommended**: includes only configurations that are both performance-
  ranking eligible and behavior verified when the policy applies.

Labels such as `fastest` refer only to the selected performance metric. They
must not be presented as `best`, `most useful`, or `recommended` without the
separate behavior decision.

## Aggregation and null handling

Power 1.1 retains the Power 1.0 aggregation formulas. Each scalar is the median
of that metric's eligible measured-attempt values, and at least three of five
measured attempts must be eligible for that metric. Percentiles use linear
interpolation R-7. Full-precision values are retained and rounding is
presentation-only.

Failed, cancelled, OOM, and not-run attempts never contribute a performance
value, but remain mandatory evidence. Missing, unavailable, nonfinite, or
technically ineligible metrics are `null`. A `not_verified` or `contradicted`
behavior assessment is not a reason to manufacture a technical `null`.

## Compatibility and migration

Power 1.0 evidence is immutable and must not be relabeled as Power 1.1. Existing
1.0 raw events may be used to test the 1.1 design, but they cannot enter an
official 1.1 ranking or be modified in place.

Power 1.1 requires:

1. a versioned result schema and the freeze of the current draft
   validation-report schema;
2. a validator that independently recomputes metrics and behavior conformance;
3. an App version that exports technically derivable metrics independently of
   behavior conformance;
4. a new physical-device verification matrix using that complete contract; and
5. explicit maintainer approval before release, ranking, publication, or tag.

Until all five exist, `suite-b-power@1.1.0-draft.1` remains a protocol draft.
