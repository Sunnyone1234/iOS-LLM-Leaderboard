# Decode Throughput

## Task Metadata

| Field | Value |
|---|---|
| task_id | suite-b-on-device-performance-002 |
| suite | Suite B: On-device Performance |
| category | Throughput |
| subcategory | Decode Tokens Per Second |
| difficulty | medium |
| task_type | measurement |
| evaluation_mode | measurement |
| version | 1.0 |
| status | draft |
| author | project-maintainers |
| created | 2026-07-09 |
| last_updated | 2026-07-09 |
| tags | decode, throughput, tokens-per-second, local-inference |

## Objective

Measure sustained decode tokens per second for a local model generating a medium-length response on an Apple device.

## Background

Decode throughput determines how quickly users see the body of a generated answer after the first token appears. For iOS apps, sustained generation speed affects perceived quality in chat, summarization, drafting, and assistant workflows.

## Input

Use a deterministic prompt intended to produce a medium-length generated response. Record the exact prompt text, prompt length, requested output length, tokenizer used, and token count.

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

The output length target should be documented in tokens or with the closest runtime-supported equivalent.

## Expected Output

Submit a Framework v1 result JSON under `results/raw/` that records sustained decode throughput in `metrics.decode_tokens_per_second`.

The result should also record TTFT, generated output token count, and raw artifact paths when available.

## Evaluation

### Automatic Evaluation

- Verify required result fields are present.
- Verify `task.task_id` is `suite-b-on-device-performance-002`.
- Verify `task.task_version` is `1.0`.
- Verify `task.suite` is `Suite B: On-device Performance`.
- Verify `metrics.decode_tokens_per_second` is numeric.
- Verify prompt length, output length, model, quantization, device, OS version, runtime, warm-up procedure, and measurement procedure are recorded.

### Manual Evaluation

- Review whether the generated output length is sufficient to represent sustained decoding.
- Review whether token counting is documented clearly.
- Review whether the measurement excludes prompt prefill time when reporting decode throughput.
- Review whether repeated runs, variance, or run selection are explained.

### Pass Conditions

- A valid result JSON is provided.
- Decode tokens per second is measured and recorded.
- The measurement procedure explains how decode throughput was calculated.
- Required model, runtime, device, quantization, OS, prompt length, output length, warm-up, and measurement metadata are present.

### Failure Conditions

- Decode throughput is missing, non-numeric, fabricated, or calculated from an undocumented method.
- The result mixes prefill and decode timing without explaining the calculation.
- Required metadata is missing.
- The generated output is too short or otherwise unsuitable for sustained decode measurement.

## Scoring Rubric

This draft protocol scores measurement quality, not model speed.

- 10: Complete, reproducible decode throughput measurement with clear token counting and timing boundaries.
- 7-9: Usable measurement with minor metadata or artifact gaps.
- 4-6: Partial measurement with unclear timing, token counting, or run procedure.
- 1-3: Incomplete measurement with major reproducibility gaps.
- 0: Missing, fabricated, or unusable measurement.

Performance numbers collected under this draft protocol must not be treated as official leaderboard rankings.

## Reproducibility Requirements

Record:

- exact prompt text
- prompt length and tokenizer or counting method
- requested output length and actual output token count
- decoding parameters that affect generation length or stopping
- model name, version, parameter size when known, and quantization
- runtime name, runtime version, backend, and model format
- device name, chip, memory when known, OS name, and OS version
- power state and relevant system settings when known
- warm-up procedure
- decode timing start and stop definitions
- measurement procedure and number of runs
- raw logs or artifact paths when available

## Reviewer Notes

Decode throughput should be compared only between runs with compatible output length, runtime settings, tokenizer behavior, model, quantization, device, and OS version.
