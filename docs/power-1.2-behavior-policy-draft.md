# Power 1.2 Behavior Policy Draft

> Status: development only. This document does not publish Power 1.2, change
> Power 1.1 results, or authorize a new ranking policy.

Power 1.1 correctly separates measured performance from behavior verification,
but its frozen `short-interaction-response-v1` policy recognizes a narrow set
of literal English words. A response can therefore be semantically suitable
while receiving `not_verified`, for example when it says that a note is
`securely stored` instead of `safe`.

The draft `short-interaction-response-v2` policy improves deterministic
coverage. Its canonical machine-readable definition is:

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

Power 1.1 and its existing validation reports remain immutable. The App 0.16
local preview and the standalone draft evaluator consume the same policy file,
but no v2 assessment becomes official until a versioned validator/report
release, review matrix, and maintainer approval are complete.

The draft evaluator is:

```bash
python3 scripts/validate_short_interaction_response_v2.py \
  "Your note is securely stored on this device. It will sync when connectivity returns."
```

## Retained two-stage experiment

The project also retains a separate, non-normative GitHub Models experiment:

- stage 1 runs the deterministic v2 policy locally;
- stage 2 sends only stage-1 `not_verified` responses to
  `openai/gpt-4.1-mini` for an auditable semantic review; and
- the hosted judgment records model metadata, prompt hashes, request settings,
  evidence excerpts, and separate semantic and format decisions.

The implementation is under
`scripts/experiments/github_models_short_interaction/`. It deliberately does
not include or depend on the discontinued NLI experiment. Hosted GPT review is
not currently a Power 1.1 ranking authority and can affect only a future
behavior-recommendation decision, never TTFT, throughput, memory, thermal, or
other measured-performance eligibility.

Before activation, the project must verify Swift/Python parity, freeze positive,
negative, ambiguous, and adversarial examples, publish the validator/report
identities, define privacy and GitHub Models availability fallbacks, and decide
whether historical raw evidence may receive a new behavior report without
mutating its original report.
