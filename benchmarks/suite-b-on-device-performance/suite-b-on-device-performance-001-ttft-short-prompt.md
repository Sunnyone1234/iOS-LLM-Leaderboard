# TTFT Short Prompt

> **Superseded draft:** TTFT is now a versioned metric collected within Suite B
> workloads. See [Protocol v2](protocol-v2.md) and [Metric Definitions](metrics.md).

## Task Metadata

| Field | Value |
|---|---|
| task_id | suite-b-on-device-performance-001 |
| suite | Suite B: On-device Performance |
| category | Latency |
| subcategory | Time To First Token |
| difficulty | easy |
| task_type | measurement |
| evaluation_mode | measurement |
| version | 1.0 |
| status | deprecated |
| author | project-maintainers |
| created | 2026-07-09 |
| last_updated | 2026-07-09 |
| tags | ttft, latency, short-prompt, local-inference |

## Objective

Measure time to first token for a local model responding to a short prompt on an Apple device.

## Background

Time to first token affects how responsive an iOS app feels when a local model starts answering. This protocol isolates startup latency for a short, common interaction rather than sustained generation speed.

## Input

Use a short deterministic prompt selected by the evaluator and record the exact prompt text, prompt length, tokenizer used, and token count.

Canonical input constraints:

- Target prompt length: 16-64 tokens.
- Target output length: 32-128 tokens.
- The prompt should be a simple app-style request that does not require tools, network access, private data, or long context.
- The same prompt must be used for all measured runs in a submission.

Measurement setup must record:

- device
- runtime
- model
- quantization
- OS version
- prompt length
- requested output length
- warm-up procedure
- measurement procedure

The selected prompt should be short enough to represent a lightweight app interaction and should not include private user data.

Default warm-up procedure:

- Load the model once before measured runs if the runtime has a distinct model-load step.
- Run one unrecorded warm-up generation using the same prompt and output settings.
- Document whether the submitted TTFT measures cold start, warm start, or both.

Default measurement procedure:

- Run at least 3 measured runs where practical.
- Report per-run TTFT values when available.
- Report the median TTFT as the primary value.
- Record whether failed or interrupted runs were excluded and why.

Timing boundaries:

- TTFT timing starts when the app or runtime submits the fully prepared prompt to the inference runtime.
- The first token is counted when the first generated token is emitted by the runtime and is available to the app layer.
- Do not include UI rendering, network access, manual copy/paste, or post-processing time unless explicitly documented.

## Expected Output

Submit a Framework v1 result JSON under `results/raw/` that records TTFT in `metrics.ttft_ms` and includes all required task, model, runtime, device, execution, evaluation, metrics, provenance, and license fields.

The result should include raw artifact paths or reproduction notes for timing logs when available.

Primary metric:

- `metrics.ttft_ms`

Optional secondary metrics:

- per-run TTFT values in raw artifacts or reproduction notes
- `metrics.decode_tokens_per_second`
- `metrics.peak_memory_mb`
- `metrics.thermal_state`

## Evaluation

### Automatic Evaluation

- Verify required result fields are present.
- Verify `task.task_id` is `suite-b-on-device-performance-001`.
- Verify `task.task_version` is `1.0`.
- Verify `task.suite` is `Suite B: On-device Performance`.
- Verify `metrics.ttft_ms` is numeric.
- Verify model, quantization, device, OS version, runtime, prompt length, output length, warm-up procedure, and measurement procedure are recorded.

### Manual Evaluation

- Review whether the prompt is appropriate for a short-prompt latency test.
- Review whether the measurement procedure clearly defines when timing starts and when the first token is counted.
- Review whether warm-up behavior is documented consistently.
- Review whether reproduction notes are sufficient for another contributor to repeat the run.

### Pass Conditions

- A valid result JSON is provided.
- TTFT is measured and recorded.
- The prompt, prompt length, requested output length, model, runtime, device, quantization, OS version, warm-up procedure, and measurement procedure are documented.
- Timing start and first-token boundaries are documented.
- The submission does not include fabricated or simulated measurements.

### Failure Conditions

- TTFT is missing, non-numeric, simulated, or copied from an unrelated source.
- Required device, model, runtime, quantization, OS, prompt length, output length, warm-up, or measurement details are missing.
- The result is presented as official while the task remains draft.
- The prompt contains private or non-redistributable data.

## Scoring Rubric

This draft protocol uses measurement completeness rather than performance ranking.

- 10: Complete, reproducible TTFT measurement with clear timing boundaries and all required metadata.
- 7-9: Usable TTFT measurement with minor metadata or reproduction gaps.
- 4-6: Partial measurement with significant reproducibility gaps.
- 1-3: Incomplete or ambiguous measurement.
- 0: Missing, fabricated, or unusable measurement.

Performance numbers collected under this draft protocol must not be treated as official leaderboard rankings.

## Reproducibility Requirements

Record:

- exact prompt text
- prompt length and tokenizer or counting method
- requested output length
- model name, version, parameter size when known, and quantization
- runtime name, runtime version, backend, and model format
- device name, chip, memory when known, OS name, and OS version
- power state and relevant system settings when known
- warm-up procedure
- timing start and stop definitions
- measurement procedure and number of runs
- per-run values and median aggregation method
- failed or interrupted run handling
- raw logs or artifact paths when available

## Reviewer Notes

This task measures responsiveness, not overall throughput. Reviewers should not compare results unless model, runtime, quantization, device class, OS version, prompt band, output band, warm-up procedure, and measurement method are comparable.
