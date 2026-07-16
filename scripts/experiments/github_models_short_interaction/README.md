# GitHub Models Short Interaction experiment

**Status: experimental and non-normative.** This experiment is not part of
Power 1.2, the official App, submission acceptance, CI, or leaderboard ranking.

It tests whether a hosted instruction model can act as a conservative review
layer for responses that a deterministic policy cannot verify. It evaluates
semantic content and response-format compliance separately so semantic rescue
does not silently waive benchmark instructions.

This is the retained hosted-GPT branch of the two-stage experiment. It has no
NLI dependency and does not contain the discontinued local NLI evaluator.

## Isolation and privacy

- Only the supplied text cases are sent to GitHub Models.
- Authentication is read from `GITHUB_TOKEN`, `GH_TOKEN`, or `gh auth token` in
  memory; credentials are never written to a report.
- Generated reports belong outside the repository.
- The included real cases point to already tracked public result evidence.
- Do not run this experiment on private or embargoed submissions without the
  contributor's consent.
- The experiment cannot recreate TTFT, throughput, memory, or other
  measurements that an older App result did not preserve.

GitHub Models is a rate-limited prototype service. Its catalog exposes a model
version, but the inference request selects the model ID rather than an immutable
weight revision. A seed is best-effort and does not guarantee deterministic
replay. The report therefore archives model catalog metadata, prompt hashes,
parameters, provider metadata, and every individual judgment.

## Run

First authenticate `gh` with access to GitHub Models (`models: read`). No Python
packages beyond the standard library are required.

```bash
python3 scripts/experiments/github_models_short_interaction/evaluate.py --dry-run
python3 -m unittest \
  scripts/experiments/github_models_short_interaction/test_evaluate.py -v

python3 scripts/experiments/github_models_short_interaction/evaluate.py \
  --model openai/gpt-4.1-mini \
  --output /tmp/github-models-short-interaction-synthetic.json

python3 scripts/experiments/github_models_short_interaction/evaluate.py \
  --real-cases \
  --model openai/gpt-4.1-mini \
  --output /tmp/github-models-short-interaction-real.json
```

The expected labels are withheld from the API prompt. Reports compare the
returned `semanticDecision` and `behaviorDecision` against the maintainer labels
only after inference. `cases.jsonl` is a balanced synthetic corpus maintained
inside this experiment; `real_cases.jsonl` records the source path for every
already public response it includes.

## Interpretation

Good results are evidence for further evaluation, not permission to change a
Power release. Before promotion, the project would still need an independently
reviewed adversarial corpus, repeated runs, cross-model agreement analysis,
privacy and cost policy, a version-drift policy, and explicit normative review.
