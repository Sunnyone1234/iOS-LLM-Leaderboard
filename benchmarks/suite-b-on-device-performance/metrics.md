# Suite B Metric Definitions

## Status

The metric formulas below are frozen for `suite-b-power@1.0.0-rc.1`. The
historical `suite-b-metrics-0.1` identity remains attached to Pilot evidence.
Metric definitions are versioned and must not be compared across incompatible
timing boundaries.

## Timing Metrics

### Pipeline TTFT (`pipeline_ttft_ms@1`)

Time from submitting already prepared model input to the runtime generation
path until the adapter receives the first raw generated token.

It excludes model download and model loading. Whether tokenization and chat
templating are excluded is declared by the measurement-mode boundary. The
current MLX pilot prepares the input before starting the clock, so it excludes
those stages.

### First-renderable proxy TTFT (`first_renderable_proxy_ttft_ms@1`)

Time from accepting the canonical text request at the app layer until
cumulative decoding first produces generated content available to the render
path. It includes chat
templating, tokenization, runtime submission, prefill, hidden leading special
or reasoning tokens, and adapter decoding. SwiftUI rendering, display refresh,
and human perception are outside v1 of this metric.

If an adapter cannot prove the frozen bounded trace, this metric is `null`;
Pipeline TTFT must not be relabeled as this proxy.

### End-to-end latency (`request_completion_ms@1`)

Time from accepting the canonical text request until the final generated token
or documented stop condition is returned to the app layer.

## Throughput Metrics

### Prefill throughput (`prefill_tokens_per_second@1`)

Actual model-input token count divided by explicit runtime-reported prompt
evaluation duration. The token count includes chat-template and special tokens
actually processed by the model. If a runtime does not expose a reliable
prefill duration, the metric is `null`.

### Decode throughput (`decode_tokens_per_second@1`)

For at least two generated token events:

```text
(generated token count - 1)
----------------------------------------------
last token timestamp - first token timestamp
```

The first generated token belongs to TTFT and is excluded from the decode
numerator. Raw stop-token inclusion policy must be recorded.

### Token interval percentiles (`token_interval_ms@1`)

Differences between consecutive raw token timestamps, reported as p50, p95,
and p99 using the interpolation method declared by the runner version.

## Memory Metrics

### Process physical footprint (`process_physical_footprint_mib@1`)

Maximum sampled `TASK_VM_INFO.phys_footprint` for the benchmark app process
during an attempt, divided by 1,048,576. The sampling interval and every
in-window sample are retained for Power 1.0.

This value is not labeled model-only memory or system-wide peak memory. A
result should additionally record, when available:

- baseline before model load;
- footprint after model load;
- peak during the attempt; and
- incremental peak relative to the selected baseline.

## Thermal Metrics

### Thermal state (`ios_thermal_state@1`)

The categorical `ProcessInfo.thermalState`: `nominal`, `fair`, `serious`,
`critical`, or `unknown`. It is not a temperature measurement.

Record session start, attempt start, attempt end, session end, and timestamped
state changes when available.

### Decode sustained degradation (`decode_first_to_last_percent_change@1`)

For decode throughput over measured attempt indices one and five:

```text
(decode_last / decode_first - 1) × 100
```

Both attempts must be decode-eligible and all six planned attempt records must
exist. Negative means slower sustained decode. The historical Pilot metric ID
`first_to_last_percent_change@1` remains attached to its original evidence and
must not be relabeled as this Power 1.0 metric.

## Reliability Metrics

Record planned, completed, failed, cancelled, OOM, early-EOS, and not-run
attempt counts. Failures are evidence and are never removed from the bundle.
