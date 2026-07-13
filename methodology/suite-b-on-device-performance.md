# Suite B: On-device Performance Methodology

Suite B evaluates pinned local model artifacts and runtimes on physical Apple
devices. It belongs to the Embedded Intelligence track.

## Current Status

Suite B Protocol v2 is a design draft. The physical-iPhone Benchmark App has
completed a real MLX pilot, but no Suite B workload or result is official yet.

## Workload-Centric Design

Suite B does not define TTFT, prefill, decode, memory, and thermal behavior as
five independent tasks. A versioned workload executes once and collects a
compatible set of metrics from the same attempts.

The suite contains:

- user-experience workloads for recognizable in-app interactions; and
- pipeline profiles for input scaling, sustained generation, and thermal or
  runtime diagnosis.

This separation prevents synthetic pipeline numbers from being presented as a
complete description of user experience.

## Comparison Unit

A comparable observation includes:

```text
workload version
+ measurement-mode version
+ model artifact and quantization
+ runtime adapter and version
+ physical device and OS
+ generation configuration
```

Model names remain the primary public label. Full configuration remains part of
the evidence and determines whether two rows are compatible.

## Metrics

The draft common set includes:

- pipeline TTFT;
- user-visible TTFT when observable;
- prefill throughput;
- decode throughput;
- p50/p95/p99 token interval;
- request completion time for UX workloads;
- sampled process physical footprint;
- iOS thermal state and sustained degradation; and
- failure, cancellation, early-stop, and OOM counts.

Definitions live in
[Suite B Metric Definitions](../benchmarks/suite-b-on-device-performance/metrics.md).

## Ranking

Suite B does not produce a global score. Views are separated by workload,
device, metric definition, and evidence level. The default view is model-first;
configuration and raw data appear in details.

## Suite Boundary

Suite B measures device execution. Suite E evaluates runtime compatibility,
integration effort, feature coverage, licensing, and deployment tradeoffs. A
Suite E scorecard may reference compatible Suite B evidence without duplicating
or reinterpreting it.

See [Suite B Protocol v2](../benchmarks/suite-b-on-device-performance/protocol-v2.md)
and [Framework v2 Architecture](benchmark-framework-v2.md).
