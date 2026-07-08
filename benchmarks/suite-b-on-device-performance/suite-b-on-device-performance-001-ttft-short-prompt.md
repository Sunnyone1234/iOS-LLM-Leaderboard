# TTFT Short Prompt

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
| status | draft |
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

## Expected Output

Submit a Framework v1 result JSON under `results/raw/` that records TTFT in `metrics.ttft_ms` and includes all required task, model, runtime, device, execution, evaluation, metrics, provenance, and license fields.

The result should include raw artifact paths or reproduction notes for timing logs when available.

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
- The prompt, model, runtime, device, quantization, OS version, warm-up procedure, and measurement procedure are documented.
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
- raw logs or artifact paths when available

## Reviewer Notes

This task measures responsiveness, not overall throughput. Reviewers should not compare results unless prompt, model, runtime, quantization, device class, OS version, and measurement procedure are comparable.
