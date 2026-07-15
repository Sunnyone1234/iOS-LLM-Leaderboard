# Power 1.2 Behavior Policy Draft

> Status: development only. This document does not publish Power 1.2, change
> Power 1.1 results, or authorize a new ranking policy.

Power 1.1 correctly separates measured performance from behavior verification,
but its frozen `short-interaction-response-v1` policy recognizes a narrow set
of literal English words. A response can therefore be semantically suitable
while receiving `not_verified`, for example when it says that a note is
`securely stored` instead of `safe`.

The draft `short-interaction-response-v2` policy improves deterministic
coverage without introducing an LLM judge. Its canonical machine-readable
definition is:

- `benchmarks/suite-b-on-device-performance/policies/short-interaction-response-v2.json`

## Scope

The draft changes only behavior assessment:

- local persistence accepts versioned terms including `safe`, `secure`,
  `saved`, `stored`, `preserved`, and `kept`;
- deferred synchronization accepts `sync` and `upload` expressions tied to a
  connectivity-return condition;
- explicit negative phrases can produce `contradicted`;
- an unmatched expression remains `not_verified`, which is not a claim that
  the answer is semantically incorrect; and
- the existing three-of-five measured-attempt threshold remains unchanged.

The draft does not change prompts, fixtures, attempt counts, timing boundaries,
metric formulas, measurement eligibility, or performance-ranking eligibility.
It affects recommendation eligibility only.

## Version and evidence boundary

Power 1.1 and its existing validation reports remain immutable. The App 0.14
local preview and the standalone draft evaluator consume the same policy file,
but no v2 assessment becomes official until a versioned validator/report
release, review matrix, and maintainer approval are complete.

The draft evaluator is:

```bash
python3 scripts/validate_short_interaction_response_v2.py \
  "Your note is securely stored on this device. It will sync when connectivity returns."
```

Before activation, the project must verify Swift/Python parity, freeze positive,
negative, and ambiguous examples, publish the validator/report identities, and
decide whether historical raw evidence may receive a new report without
mutating its original report.
