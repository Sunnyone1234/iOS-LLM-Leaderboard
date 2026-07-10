# Benchmark Result Specification

Benchmark results should be stored as JSON files under `results/raw/`.

Official leaderboard generation should only use validated result files. Demo-placeholder results must not be used in official leaderboard generation.

## Canonical Result JSON

```json
{
  "schema_version": "1.0",
  "result_id": "2026-07-09-suite-a-swift-codegen-001-gpt-example",
  "task": {
    "task_id": "suite-a-swift-codegen-001",
    "task_version": "1.0",
    "suite": "Suite A: Swift Code Generation",
    "category": "SwiftUI",
    "subcategory": "List Deletion"
  },
  "model": {
    "model_name": "Example Model",
    "provider": "Example Provider",
    "model_version": "unknown",
    "access_type": "api",
    "parameter_size": null,
    "quantization": null
  },
  "runtime": {
    "runtime_name": null,
    "runtime_version": null,
    "backend": null,
    "model_format": null
  },
  "device": {
    "device_name": null,
    "chip": null,
    "memory_gb": null,
    "os_name": null,
    "os_version": null
  },
  "execution": {
    "date": "YYYY-MM-DD",
    "evaluator": "name-or-github-handle",
    "run_type": "manual",
    "temperature": null,
    "seed": null,
    "prompt_tokens": null,
    "output_tokens": null,
    "notes": ""
  },
  "suite_b_measurement": {
    "prompt_token_band": null,
    "output_token_band": null,
    "warmup_procedure": null,
    "measurement_procedure": null,
    "measured_run_count": null,
    "aggregation_method": null,
    "cold_or_warm_start_state": null,
    "timing_boundaries": null,
    "failed_or_interrupted_run_handling": null,
    "per_run_metrics": []
  },
  "output": {
    "raw_output_path": null,
    "summary": "",
    "structured_output": null
  },
  "evaluation": {
    "score": null,
    "max_score": 100,
    "passed": null,
    "automatic_checks": [],
    "manual_review": [],
    "failure_reasons": [],
    "reviewer_notes": ""
  },
  "metrics": {
    "ttft_ms": null,
    "prefill_tokens_per_second": null,
    "decode_tokens_per_second": null,
    "peak_memory_mb": null,
    "energy_joules": null,
    "thermal_state": null,
    "p50_token_interval_ms": null,
    "p95_token_interval_ms": null,
    "p99_token_interval_ms": null
  },
  "provenance": {
    "source": "manual-submission",
    "commit_sha": null,
    "raw_artifact_paths": [],
    "reproduction_notes": ""
  },
  "license_confirmation": {
    "contributor_agrees_to_repo_license": true
  }
}
```

## Required Result Fields

Every result must include:

```text
schema_version
result_id
task.task_id
task.task_version
task.suite
model.model_name
model.provider
execution.date
execution.evaluator
evaluation.score
evaluation.max_score
evaluation.passed
license_confirmation.contributor_agrees_to_repo_license
```

If a field is not applicable, use `null`. Do not omit required fields.

## Suite B Measurement Fields

Suite B result submissions should include a `suite_b_measurement` object. For non-Suite B results, this object may be omitted or set to `null` until a future schema version standardizes suite-specific extension objects.

Fields:

- `prompt_token_band`: protocol-defined prompt token band used for the run, such as `16-64`.
- `output_token_band`: protocol-defined requested output token band used for the run, such as `32-128`.
- `warmup_procedure`: description of model load, warm-up generation, cache state, and any unrecorded warm-up runs.
- `measurement_procedure`: description of measured run count, run order, runtime settings, and measurement method.
- `measured_run_count`: number of measured runs attempted or accepted for aggregation.
- `aggregation_method`: primary aggregation method, typically `median`.
- `cold_or_warm_start_state`: whether the result measures `cold`, `warm`, `both`, or `unknown` start state.
- `timing_boundaries`: timing start/stop definitions for the measured protocol.
- `failed_or_interrupted_run_handling`: explanation of failed, interrupted, early-stopped, throttled, or out-of-memory run handling.
- `per_run_metrics`: per-run measurements when available.

Each `per_run_metrics` item may include:

```json
{
  "run_index": 1,
  "ttft_ms": null,
  "prefill_tokens_per_second": null,
  "decode_tokens_per_second": null,
  "peak_memory_mb": null,
  "thermal_state": null,
  "notes": ""
}
```

Do not invent missing per-run values. Use `null` when a metric was not collected.

## result_id Format

Suggested format:

```text
YYYY-MM-DD-task-id-model-name-short-run-id
```

Example:

```text
2026-07-09-suite-a-swift-codegen-001-gpt-example
```

## Allowed model.access_type Values

```text
api
local
xcode
hosted
unknown
```

## Allowed execution.run_type Values

```text
manual
scripted
app-export
ci
unknown
```

## Allowed provenance.source Values

```text
manual-submission
benchmark-app
maintainer-run
ci
imported
demo-placeholder
```

Demo placeholder results must not be used in official leaderboard generation.

The canonical example uses a 0–100 maximum for a general scored task. A
suite-specific task may define another maximum. Suite B draft reproducibility
rubrics currently use a 0–10 scale and must not be interpreted as performance
scores.

## Suite-Specific Result Requirements

### Suite A

Recommended:

- `compile_success` check
- `unit_tests` check if applicable
- manual review for Swift idiomatic quality
- manual review for architecture/readability

### Suite B

Required:

- runtime metadata
- device metadata
- `suite_b_measurement.prompt_token_band`
- `suite_b_measurement.output_token_band`
- `suite_b_measurement.warmup_procedure`
- `suite_b_measurement.measurement_procedure`
- `suite_b_measurement.measured_run_count`
- `suite_b_measurement.aggregation_method`
- `suite_b_measurement.cold_or_warm_start_state`
- `suite_b_measurement.timing_boundaries`
- `suite_b_measurement.failed_or_interrupted_run_handling`
- the protocol primary metric, such as `metrics.ttft_ms`, `metrics.prefill_tokens_per_second`, `metrics.decode_tokens_per_second`, `metrics.peak_memory_mb`, or `metrics.thermal_state`

Recommended:

- `suite_b_measurement.per_run_metrics`
- `metrics.ttft_ms`
- `metrics.prefill_tokens_per_second`
- `metrics.decode_tokens_per_second`
- `metrics.peak_memory_mb`
- `metrics.energy_joules`
- `metrics.thermal_state`
- `metrics.p50_token_interval_ms`
- `metrics.p95_token_interval_ms`
- `metrics.p99_token_interval_ms`

### Suite C

Recommended:

- device metadata
- Xcode or IDE environment in `execution.notes` or `provenance`
- `output.summary`
- `evaluation.manual_review`

Useful criteria:

- completion usefulness
- fix correctness
- compile success after fix
- developer workflow usefulness

### Suite D

Recommended:

- `output.structured_output`
- `evaluation.automatic_checks`
- `evaluation.manual_review`

Useful criteria:

- schema validity
- extraction accuracy
- translation quality
- summarization fidelity
- safety behavior

### Suite E

Required:

- `runtime.runtime_name`
- `runtime.runtime_version`
- `runtime.backend`
- `runtime.model_format`
- `device.device_name`
- `device.os_version`
- metrics

Suite E must clearly state whether it evaluates:

- a runtime
- a model
- a model-runtime pair
