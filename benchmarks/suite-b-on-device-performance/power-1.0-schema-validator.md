# Power Benchmark 1.0 Schema and Validator Freeze

## Status

F3 freezes the non-official release candidate `suite-b-power@1.0.0-rc.1`.
The immutable release manifest is
[`releases/suite-b-power-1.0.0-rc.1.json`](releases/suite-b-power-1.0.0-rc.1.json).
It pins the protocol, metric definitions, both fixtures, result schema,
validation-report schema, reason-code registry, and semantic validator by
SHA-256.

This is not a release, tag, official result format, or ranking authorization.
The manifest requires reference App 0.8.0 or later, whose implementation is
the next F4 work item.

## Frozen contracts

- `schemas/suite-b-power-result-1.0.0-rc.1.schema.json` defines submitted
  execution identity, configuration, environment, attempts, raw evidence, and
  recalculable derived values.
- `scripts/validate_suite_b_power_result.py` enforces the release identity and
  protocol semantics, recalculates every candidate ranked metric, and checks
  submitted derived values without modifying the result.
- `schemas/suite-b-power-validation-report-1.0.0-rc.1.schema.json` keeps
  structural validity, protocol conformance, per-metric eligibility, evidence
  review, and ranking eligibility as separate decisions.
- `power-1.0-validation-reasons.json` is the frozen reason-code registry.

The result contract retains raw prompt-evaluation duration, token events,
bounded First-renderable proxy trace, process-footprint samples, and thermal
observations. A metric that cannot be recalculated from those observations is
`null` and ineligible. Failed, cancelled, OOM, and not-run attempts remain in
the six-record sequence and never contribute a performance value.

## Validation

Run the frozen semantic validator locally:

```bash
python3 scripts/validate_suite_b_power_result.py result.json
```

Write the independent validation report to another file:

```bash
python3 scripts/validate_suite_b_power_result.py \
  result.json --output validation-report.json
```

Exit code `0` means the submitted bytes are structurally valid and protocol
conformant. A valid release-candidate result still returns
`validWithWarnings`, evidence level `unreviewed`, and ranking eligibility
`false`. Exit code `1` means structural or protocol validation failed; exit
code `2` means the file could not be read or parsed.

The validator also verifies every asset digest in the release manifest before
evaluating a result. Changing a pinned file therefore requires a new release
candidate manifest and compatible identity, not an in-place reinterpretation.

## Remaining boundary

F3 defines the contract that F4 must implement. It does not update the App,
create real 1.0 evidence, run a device matrix, implement CI, enable submission,
or publish a leaderboard result. Historical Pilot and Foundation validators
remain available for their original immutable bytes.
