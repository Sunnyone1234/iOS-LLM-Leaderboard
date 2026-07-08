# Prefill Throughput

## Task Metadata

| Field | Value |
|---|---|
| task_id | suite-b-on-device-performance-003 |
| suite | Suite B: On-device Performance |
| category | Throughput |
| subcategory | Prefill Tokens Per Second |
| difficulty | medium |
| task_type | measurement |
| evaluation_mode | measurement |
| version | 1.0 |
| status | draft |
| author | project-maintainers |
| created | 2026-07-09 |
| last_updated | 2026-07-09 |
| tags | prefill, throughput, long-prompt, local-inference |

## Objective

Measure prompt prefill throughput for a local model processing a long input on an Apple device.

## Background

Many iOS features ask a model to process existing user content, such as notes, transcripts, documents, or conversation history. Prefill throughput helps estimate how quickly a local model can ingest that context before generation begins.

## Input

Use a fixed long input selected by the evaluator and record the exact source, text, prompt length, tokenizer used, and token count. The input must be redistributable or included as a raw artifact when permitted.

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

If the runtime cannot directly report prefill timing, document the method used to estimate or derive it.

## Expected Output

Submit a Framework v1 result JSON under `results/raw/` that records prefill throughput in `metrics.prefill_tokens_per_second`.

The result should also include prompt token count, raw artifact references, and notes explaining how prefill timing was measured.

## Evaluation

### Automatic Evaluation

- Verify required result fields are present.
- Verify `task.task_id` is `suite-b-on-device-performance-003`.
- Verify `task.task_version` is `1.0`.
- Verify `task.suite` is `Suite B: On-device Performance`.
- Verify `metrics.prefill_tokens_per_second` is numeric.
- Verify prompt length, output length, model, quantization, device, OS version, runtime, warm-up procedure, and measurement procedure are recorded.

### Manual Evaluation

- Review whether the long input is fixed, redistributable, and sufficiently documented.
- Review whether prefill timing is separated from decode timing.
- Review whether token counting is documented clearly.
- Review whether the method is supported by the runtime or transparently derived.

### Pass Conditions

- A valid result JSON is provided.
- Prefill tokens per second is measured or transparently derived and recorded.
- The long input, model, runtime, device, quantization, OS version, prompt length, output length, warm-up, and measurement procedure are documented.
- Raw input artifacts or stable references are provided when allowed.

### Failure Conditions

- Prefill throughput is missing, non-numeric, fabricated, or derived from an undocumented method.
- The long input cannot be reviewed or reproduced.
- The result mixes prefill and decode timing without explanation.
- Required metadata is missing.

## Scoring Rubric

This draft protocol scores measurement reproducibility, not runtime speed.

- 10: Complete prefill measurement with fixed input, clear token counting, clear timing boundaries, and all required metadata.
- 7-9: Usable prefill measurement with minor metadata or artifact gaps.
- 4-6: Partial measurement with significant uncertainty about input, token count, or timing.
- 1-3: Incomplete measurement with major reproducibility gaps.
- 0: Missing, fabricated, or unusable measurement.

Performance numbers collected under this draft protocol must not be treated as official leaderboard rankings.

## Reproducibility Requirements

Record:

- exact long input or redistributable artifact reference
- prompt length and tokenizer or counting method
- requested output length and actual output token count if generation occurs
- model name, version, parameter size when known, and quantization
- runtime name, runtime version, backend, and model format
- device name, chip, memory when known, OS name, and OS version
- power state and relevant system settings when known
- warm-up procedure
- prefill timing start and stop definitions
- measurement procedure and number of runs
- raw logs or artifact paths when available

## Reviewer Notes

This protocol depends heavily on a reproducible long input and clear runtime timing. Do not compare prefill results when prompt content, token count, tokenizer, runtime, model, quantization, or device differs materially.
