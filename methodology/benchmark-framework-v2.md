# Benchmark Framework v2 Architecture

## Status

Framework v2 remains a repository-wide design draft and Framework v1 remains
the accepted format outside the Power Foundation track. For Suite B Power,
F2 and F3 now freeze the non-official `suite-b-power@1.0.0-rc.1` protocol,
migration, schema, release-manifest, and validator contracts. The reference App
does not emit that contract until F4. Release-candidate results are never
official leaderboard results.

## Why v2 Exists

Framework v1 uses one `task` object for prompts, measurement procedures,
metrics, and evaluation. That is workable for code-generation tasks but too
ambiguous for physical-device benchmarks. Framework v2 separates what is run,
how it is measured, and what evidence is produced.

## Canonical Objects

| Object | Meaning | Stable identity example |
| --- | --- | --- |
| Track | Product question shared by multiple suites | `embedded-intelligence` |
| Suite | Independent evaluation domain | `suite-b-on-device-performance` |
| Task | A scored or assessed capability, mainly for Suites A/C/D | `suite-a-swift-codegen-001` |
| Workload | Exact input and requested behavior executed by a runner | `b-ux-001-short-interaction` |
| Measurement mode | Timing, cache, repetition, and environment boundaries | `b-mode-warm-resident-v1` |
| Metric | One value with a fixed formula and unit | `pipeline_ttft_ms@1` |
| Model profile | Public model identity plus immutable deployable artifact | `qwen3-0.6b-mlx-4bit@1` |
| Runtime adapter | Runtime implementation and evidence contract | `mlx-swift-lm@3.31.4` |
| Benchmark release | Compatible workload, metric, schema, and runner versions | `suite-b-0.1-draft` |
| Result bundle | Summary plus raw attempts and environment evidence | UUID |
| Trust level | Review and reproduction state, separate from performance | `community-submitted` |

## Identity and Versioning Rules

- A display name is not an artifact identity.
- A model profile records the base model, exact artifact, immutable revision,
  quantization, format, tokenizer, and chat-template identity.
- A workload version changes when its prompt, fixture, requested behavior, or
  output policy changes materially.
- A measurement-mode version changes when a timing boundary, cache rule,
  warm-up rule, run count, aggregation rule, or eligibility condition changes.
- A metric version changes when its numerator, denominator, timing boundary,
  unit, or treatment of failed runs changes.
- Results from incompatible versions must not share one ranking table.

## Result Bundle Shape

A v2 result bundle has five layers:

1. identity: release, workload, model profile, runtime, device, and runner;
2. configuration: prompt hash, generation settings, cache and repetition rules;
3. environment: OS, build, debugger, power, and thermal observations;
4. evidence: every attempted run, raw token events, failures, and samples; and
5. derived views: medians, percentiles, degradation, and eligibility decisions.

Derived values must be reproducible from raw evidence when the runtime exposes
the required events. Missing observations remain `null`; they are not guessed.

## Trust Levels

Trust is not a performance score.

| Level | Meaning | Default leaderboard |
| --- | --- | --- |
| Draft | Local, incomplete, or protocol-development evidence | No |
| Community Submitted | App-generated bundle passed structural validation | No |
| Reproduced | Compatible independent run confirms the observation | Eligible for reproduced views |
| Verified | Maintainer checks identity, raw evidence, and protocol compliance | Eligible for default verified views |
| Maintainer Reference | Maintainer-operated reference run with documented custody | Eligible for reference views |

## Suite B Composition

Suite B is workload-centric. TTFT, prefill, decode, memory, and thermal are
metrics collected from the same run; they are not independent benchmark tasks.

Suite B contains two workload categories:

- user-experience workloads describe recognizable iOS app interactions; and
- pipeline profiles isolate scaling, sustained generation, and runtime behavior.

The public view is model-first and workload-specific. Full artifact, runtime,
device, and evidence identity remains available in result details. Suite B does
not define a single aggregate score.

## v1 Migration

- Existing Suite A/C/D task IDs remain task IDs.
- Existing Suite B metric-task drafts are marked superseded, not silently
  reinterpreted.
- Useful definitions from those drafts move into versioned metric definitions.
- The current `suite-b-pilot-001` remains non-official pilot evidence and maps
  to the draft sustained-generation pipeline profile.
- Framework v1 validators continue to validate v1 results during transition.
- A separate v2 validator handles workload manifests and Suite B result bundles.
