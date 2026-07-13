# Thermal Stability

> **Superseded draft:** Thermal state and sustained degradation are now
> versioned metrics collected within Suite B pipeline profiles. See
> [Protocol v2](protocol-v2.md) and [Metric Definitions](metrics.md).

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
| status | deprecated |
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

Canonical input constraints:

- Target prompt length: 128-512 tokens.
- Target generated output length per run: 256-768 tokens.
- Use the same prompt, output settings, and stop conditions for every repeated run.
- The prompt should be stable and should not contain private data.

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

Default warm-up procedure:

- Load the model once before the repeated-run sequence if the runtime has a distinct model-load step.
- Run one unrecorded warm-up generation using the same prompt and output settings.
- Record initial thermal state before measured runs begin.
- Document whether the repeated-run sequence starts from cold device conditions, warm device conditions, or an uncontrolled state.

Default measurement procedure:

- Run at least 3 measured generations where practical.
- Use a documented repeated-run schedule, including rest intervals.
- Report per-run TTFT, decode throughput, peak memory, and thermal state when available.
- Report median values for primary performance metrics and describe degradation from first measured run to final measured run.
- Record whether failed, interrupted, throttled, or out-of-memory runs were excluded and why.

Timing and degradation boundaries:

- Each measured run starts when the prompt is submitted to the runtime and stops when generation completes or reaches the stop condition.
- Thermal state should be recorded before the sequence, before each run when available, after each run when available, and after the final run.
- Performance degradation should be reported as the change between early-run and late-run metrics using the same metric definition.
- Clearly label thermal observations as system-reported, externally measured, or qualitative.

## Expected Output

Submit a Framework v1 result JSON under `results/raw/` that records thermal state in `metrics.thermal_state` and includes per-run notes or raw artifact paths showing performance behavior across repeated runs.

When available, include TTFT, decode tokens per second, peak memory, and token interval metrics for each run as raw artifacts or structured notes.

Primary metric:

- `metrics.thermal_state`

Optional secondary metrics:

- per-run `metrics.ttft_ms`
- per-run `metrics.decode_tokens_per_second`
- per-run `metrics.peak_memory_mb`
- p50 / p95 / p99 token interval metrics when available
- degradation notes from first measured run to final measured run

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
- Required model, runtime, device, quantization, OS, prompt length, output length, warm-up, repeated-run schedule, thermal observation method, and measurement metadata are present.

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
- median aggregation method for primary performance metrics when available
- degradation calculation or qualitative degradation notes
- failed, interrupted, throttled, or out-of-memory run handling
- raw logs or artifact paths when available

## Reviewer Notes

Thermal stability is sensitive to environment and device state. Reviewers should treat qualitative thermal observations as useful context, not controlled laboratory measurements, unless the submission documents an instrumented method. Do not compare results unless model, runtime, quantization, device, OS version, prompt band, output band, warm-up procedure, repeated-run schedule, thermal observation method, and measurement method are comparable.
