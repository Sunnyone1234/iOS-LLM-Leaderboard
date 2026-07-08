# Peak Memory

## Task Metadata

| Field | Value |
|---|---|
| task_id | suite-b-on-device-performance-004 |
| suite | Suite B: On-device Performance |
| category | Memory |
| subcategory | Peak Memory Usage |
| difficulty | medium |
| task_type | measurement |
| evaluation_mode | measurement |
| version | 1.0 |
| status | draft |
| author | project-maintainers |
| created | 2026-07-09 |
| last_updated | 2026-07-09 |
| tags | memory, peak-memory, model-load, generation, local-inference |

## Objective

Measure peak memory usage during local model load and generation on an Apple device.

## Background

Memory pressure is a practical limit for local models in iOS apps. Peak memory during load and generation affects whether an app can run reliably alongside UI, app state, media, databases, and other system activity.

## Input

Use a fixed prompt and generation setup selected by the evaluator. Record prompt length, output length, tokenizer used, and whether peak memory covers model load, generation, or both.

Measurement setup must record:

- device
- runtime
- model
- quantization
- OS version
- prompt length
- output length
- warm-up procedure
- measurement procedure
- memory measurement tool or API

## Expected Output

Submit a Framework v1 result JSON under `results/raw/` that records peak memory in `metrics.peak_memory_mb`.

The result should distinguish load-time memory, generation-time memory, and total observed peak when the measurement method supports that detail.

## Evaluation

### Automatic Evaluation

- Verify required result fields are present.
- Verify `task.task_id` is `suite-b-on-device-performance-004`.
- Verify `task.task_version` is `1.0`.
- Verify `task.suite` is `Suite B: On-device Performance`.
- Verify `metrics.peak_memory_mb` is numeric.
- Verify prompt length, output length, model, quantization, device, OS version, runtime, warm-up procedure, measurement procedure, and memory measurement method are recorded.

### Manual Evaluation

- Review whether the memory measurement tool or API is appropriate for the platform.
- Review whether the result distinguishes model load from generation when possible.
- Review whether background app activity or system conditions could materially affect the result.
- Review whether reproduction notes explain how peak memory was observed.

### Pass Conditions

- A valid result JSON is provided.
- Peak memory is measured and recorded.
- The measurement method is documented.
- Required model, runtime, device, quantization, OS, prompt length, output length, warm-up, and measurement metadata are present.

### Failure Conditions

- Peak memory is missing, non-numeric, fabricated, or estimated without explanation.
- The measurement method is undocumented.
- Required metadata is missing.
- The result does not clarify whether memory was measured during load, generation, or both.

## Scoring Rubric

This draft protocol scores measurement clarity, not lower memory use.

- 10: Complete peak memory measurement with clear scope, tool/API, timing, and metadata.
- 7-9: Usable measurement with minor metadata or artifact gaps.
- 4-6: Partial measurement with unclear scope or measurement method.
- 1-3: Incomplete measurement with major reproducibility gaps.
- 0: Missing, fabricated, or unusable measurement.

Performance numbers collected under this draft protocol must not be treated as official leaderboard rankings.

## Reproducibility Requirements

Record:

- exact prompt text or artifact reference
- prompt length and tokenizer or counting method
- requested output length and actual output token count if generation occurs
- model name, version, parameter size when known, and quantization
- runtime name, runtime version, backend, and model format
- device name, chip, memory when known, OS name, and OS version
- memory measurement tool, API, or profiler
- whether measurement includes model load, generation, or both
- power state and relevant system settings when known
- warm-up procedure
- measurement procedure and number of runs
- raw logs, screenshots, profiler exports, or artifact paths when available

## Reviewer Notes

Peak memory results can vary by runtime allocation behavior and measurement tool. Reviewers should avoid cross-run comparisons unless measurement scope and tooling are comparable.
