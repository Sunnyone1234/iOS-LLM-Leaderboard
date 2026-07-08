# Thermal Stability

## Task Metadata

| Field | Value |
|---|---|
| task_id | suite-b-on-device-performance-005 |
| suite | Suite B: On-device Performance |
| category | Stability |
| subcategory | Thermal Behavior |
| difficulty | hard |
| task_type | measurement |
| evaluation_mode | measurement |
| version | 1.0 |
| status | draft |
| author | project-maintainers |
| created | 2026-07-09 |
| last_updated | 2026-07-09 |
| tags | thermal, stability, repeated-runs, degradation, local-inference |

## Objective

Measure thermal behavior and performance degradation across repeated local model runs on an Apple device.

## Background

Local inference can affect device temperature, sustained throughput, and user experience. Thermal stability matters for apps that run repeated generations, long sessions, or background-adjacent workflows.

## Input

Use a fixed prompt and generation setup repeated under a documented procedure. Record prompt length, output length, tokenizer used, repeat count, rest intervals, device thermal state observations, and performance metrics for each run.

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
- repeated-run schedule
- thermal observation method

## Expected Output

Submit a Framework v1 result JSON under `results/raw/` that records thermal state in `metrics.thermal_state` and includes per-run notes or raw artifact paths showing performance behavior across repeated runs.

When available, include TTFT, decode tokens per second, peak memory, and token interval metrics for each run as raw artifacts or structured notes.

## Evaluation

### Automatic Evaluation

- Verify required result fields are present.
- Verify `task.task_id` is `suite-b-on-device-performance-005`.
- Verify `task.task_version` is `1.0`.
- Verify `task.suite` is `Suite B: On-device Performance`.
- Verify `metrics.thermal_state` is present.
- Verify prompt length, output length, model, quantization, device, OS version, runtime, warm-up procedure, measurement procedure, repeated-run schedule, and thermal observation method are recorded.

### Manual Evaluation

- Review whether repeated-run procedure is documented clearly.
- Review whether thermal observations are labeled as qualitative or instrumented.
- Review whether performance degradation is described with comparable per-run metrics.
- Review whether environmental factors, power state, case usage, charging state, and background activity are documented when known.

### Pass Conditions

- A valid result JSON is provided.
- Thermal behavior is recorded without inventing measurements.
- Repeated-run procedure and run conditions are documented.
- Required model, runtime, device, quantization, OS, prompt length, output length, warm-up, and measurement metadata are present.

### Failure Conditions

- Thermal observations are missing, fabricated, or presented with unsupported precision.
- Repeated-run procedure is not documented.
- Required metadata is missing.
- The result reports degradation without per-run evidence or clear qualitative notes.

## Scoring Rubric

This draft protocol scores reproducibility and clarity of thermal stability reporting, not cooler operation.

- 10: Complete repeated-run thermal stability report with clear procedure, per-run metrics or artifacts, and all required metadata.
- 7-9: Usable thermal report with minor metadata, artifact, or environmental-context gaps.
- 4-6: Partial report with limited repeated-run detail or unclear thermal observation method.
- 1-3: Incomplete report with major reproducibility gaps.
- 0: Missing, fabricated, or unusable thermal report.

Performance numbers collected under this draft protocol must not be treated as official leaderboard rankings.

## Reproducibility Requirements

Record:

- exact prompt text or artifact reference
- prompt length and tokenizer or counting method
- requested output length and actual output token count per run when available
- model name, version, parameter size when known, and quantization
- runtime name, runtime version, backend, and model format
- device name, chip, memory when known, OS name, and OS version
- power state, charging state, case usage, and relevant system settings when known
- ambient conditions when available
- warm-up procedure
- repeated-run schedule, rest intervals, and number of runs
- thermal observation method
- per-run TTFT, decode throughput, peak memory, or token interval metrics when available
- raw logs or artifact paths when available

## Reviewer Notes

Thermal stability is sensitive to environment and device state. Reviewers should treat qualitative thermal observations as useful context, not controlled laboratory measurements, unless the submission documents an instrumented method.
