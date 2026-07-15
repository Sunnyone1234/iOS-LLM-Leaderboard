# Framework v2 transition

## Status

Framework v2 concepts are active only inside the bounded Suite B Power release
slice. Framework v1 remains supported for historical A–E tasks and results.
Other suites do not become v2 merely because Power uses versioned workloads,
measurement modes, result bundles, and independent validation.

The object model is documented in
[Benchmark Framework v2 Architecture](../methodology/benchmark-framework-v2.md).

## Why Power needed it

Framework v1 used `task` for a scenario, measurement protocol, metric-specific
test, and runtime comparison. Power separates:

- workload — versioned input and output requirements;
- measurement mode — the execution state;
- metric — a value calculated from observations;
- result bundle — exact configuration, attempts, summary, and raw evidence;
- validation report — structural, protocol, metric, behavior, and ranking
  decisions derived from the submitted result.

This lets one compatible run retain TTFT, prefill, decode, memory, thermal,
failure, and token evidence without creating one task per number.

## Compatibility rules

- do not reuse an ID for a different workload;
- keep every historical result labeled with its original schema and release;
- do not rewrite evidence during migration;
- do not mix incompatible result contracts in one exact comparison cell;
- freeze benchmark releases and SHA-256-pinned assets after publication;
- migrate another suite only through a separately approved contract.

## Completed Power slice

Power 1.1 has frozen workload, measurement-mode, fixture, App, result-schema,
validator, validation-report, ranking-policy, release, and evidence identities
for B-UX-001 and B-PIPE-001. The final release adopts six RC1 source results by
exact ID and hash. Current community packages preserve the raw source export
and add a separate final-release contributor manifest.

## What is not implied

- Suite A/C Build Research is not an active v2 benchmark.
- Suite D/E has no active v2 release.
- Historical Framework v1 content remains valid in its original scope.
- A future migration must not create a parallel public contribution workflow.
