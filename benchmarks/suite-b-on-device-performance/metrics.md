# Suite B Metric Definitions

## Status

Draft metric set `suite-b-metrics-0.1`. Metric definitions are versioned and
must not be compared across incompatible timing boundaries.

## Timing Metrics

### Pipeline TTFT (`pipeline_ttft_ms@1`)

Time from submitting already prepared model input to the runtime generation
path until the adapter receives the first raw generated token.

It excludes model download and model loading. Whether tokenization and chat
templating are excluded is declared by the measurement-mode boundary. The
current MLX pilot prepares the input before starting the clock, so it excludes
those stages.

### User-perceived TTFT (`user_visible_ttft_ms@1`)

Time from accepting the canonical text request at the app layer until the first
user-visible generated content is available to render. It includes chat
templating, tokenization, runtime submission, prefill, hidden leading special
or reasoning tokens, and app-layer delivery. UI animation and display refresh
latency are outside v1 of this metric.

If an adapter cannot identify visible content, this metric is `null`; raw TTFT
must not be relabeled as user-visible TTFT.

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
during an attempt, divided by 1,048,576. The sampling interval is recorded.

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

### Sustained degradation (`first_to_last_percent_change@1`)

For a named metric `m` over the first and last successful measured attempts:

```text
(m_last / m_first - 1) × 100
```

The result retains the two run indices. Negative decode or prefill change means
slower sustained performance; positive TTFT change means worse latency.

## Reliability Metrics

Record planned, completed, failed, cancelled, OOM, early-EOS, and not-run
attempt counts. Failures are evidence and are never removed from the bundle.

