# Decode Throughput

> **Superseded draft:** Decode throughput is now a versioned metric collected
> within Suite B workloads. See [Protocol v2](protocol-v2.md) and
> [Metric Definitions](metrics.md).

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
| status | deprecated |
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

Canonical input constraints:

- Target prompt length: 128-512 tokens.
- Target generated output length: 256-768 tokens.
- The prompt should request continuous prose or structured text that is unlikely to stop early.
- The same prompt and generation limits must be used for all measured runs in a submission.

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

Default warm-up procedure:

- Load the model once before measured runs if the runtime has a distinct model-load step.
- Run one unrecorded warm-up generation using the same prompt and output settings.
- Document whether the measured runs use a cold or warm model state.

Default measurement procedure:

- Run at least 3 measured runs where practical.
- Report per-run decode throughput when available.
- Report median decode tokens/sec as the primary value.
- Record whether failed, interrupted, or early-stopped runs were excluded and why.

Timing boundaries:

- Decode timing should exclude prompt prefill time where the runtime exposes separate prefill and decode timing.
- Decode timing starts when the first generated token has been produced or when the runtime enters decode mode.
- Decode timing stops when the target output length, stop condition, or runtime generation limit is reached.
- If prefill and decode cannot be separated, document the limitation and calculation method.

## Expected Output

Submit a Framework v1 result JSON under `results/raw/` that records sustained decode throughput in `metrics.decode_tokens_per_second`.

The result should also record TTFT, generated output token count, and raw artifact paths when available.

Primary metric:

- `metrics.decode_tokens_per_second`

Optional secondary metrics:

- `metrics.ttft_ms`
- actual generated output token count
- per-run decode throughput values in raw artifacts or reproduction notes
- token interval distribution when available

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
- Required model, runtime, device, quantization, OS, prompt length, output length, warm-up, timing boundary, and measurement metadata are present.

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
- per-run values and median aggregation method
- failed, interrupted, or early-stopped run handling
- raw logs or artifact paths when available

## Reviewer Notes

Decode throughput should be compared only between runs with compatible model, runtime, quantization, device, OS version, prompt band, output band, tokenizer behavior, warm-up procedure, and measurement method.
