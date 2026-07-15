# Power benchmark

Power measures an exact on-device configuration, not a model name alone:

```text
model artifact + quantization + runtime + device + OS
+ inference settings + workload + Benchmark App version
```

## Current release

Power 1.1 is the active public release. It adopts the frozen Power 1.1 RC1
execution contract and six immutable physical-iPhone results, then applies the
final 1.1 ranking policy without rewriting the original result bytes or source
identities.

The active workloads are:

| Workload | Developer question | Primary ranking metric |
| --- | --- | --- |
| `b-ux-001-short-interaction` | How quickly can an app receive a first renderable output unit? | First-renderable proxy TTFT, lower is better |
| `b-pipe-001-sustained-generation` | How quickly can the configuration sustain generation? | Decode tokens per second, higher is better |

First-renderable proxy TTFT is measured at the adapter boundary. It is not
screen-render latency. Pipeline TTFT, prefill throughput, decode throughput,
process physical footprint, thermal state, and failures remain visible as
supporting evidence where the workload supports them.

There is no combined Power score. Different app features value latency,
throughput, memory, and sustained behavior differently.

## Evidence and validation

The App records warm-up and measured attempts, raw event evidence, exact model
and runtime identities, device and OS build, generation settings, memory, and
thermal state. Failed, cancelled, OOM, and not-run attempts are preserved.

Validation separates:

- structural validity;
- protocol conformance;
- per-metric eligibility;
- behavior verification;
- measured-performance ranking eligibility; and
- recommendation eligibility.

A structurally valid result can therefore remain visible even when one metric
is ineligible. Submission validation happens before merge; the generated
ranking independently derives eligibility again from retained evidence.

Power 1.1 source exports retain the schema identity
`suite-b-power-result-1.1.0-rc.1` because finalization adopted the frozen RC1
contract instead of relabeling evidence. A separate Power 1.1 submission
manifest binds those bytes to the contributor and final public release.

## Community ranking

- One case-insensitive GitHub account counts once per exact comparison cell.
- The same account can contribute to multiple different cells.
- Two independent contributors display as reproduced.
- Three or more enable contributor-weighted aggregation.
- Deliberate cooling, deliberate heating, or unknown thermal assistance is
  retained as evidence but excluded from the ordinary live ranking.
- App Attest is not required.

The default website may group iOS patch releases for readability and prefer
the newest App baseline. Exact OS builds and older compatible cells remain in
the evidence dataset.

## Normative assets

This page is the short public explanation. Normative details are in:

- [final release manifest](../benchmarks/suite-b-on-device-performance/releases/suite-b-power-1.1.0.json);
- [frozen RC1 protocol](../benchmarks/suite-b-on-device-performance/power-1.1-rc1-protocol.md);
- [final ranking policy](../benchmarks/suite-b-on-device-performance/power-1.1-ranking-policy.json);
- [result schema](../schemas/suite-b-power-result-1.1.0-rc.1.schema.json);
- [validation-report schema](../schemas/suite-b-power-validation-report-1.1.0.schema.json);
- [release notes](../results/suite-b-power-1.1/RELEASE-NOTES.md); and
- [checksums](../results/suite-b-power-1.1/SHA256SUMS).

To contribute, use the [Power 1.1 quickstart](../contributor-kit/power-1.1-quickstart.md).
