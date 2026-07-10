# Submit a Device Result

Use this guide when submitting a local model or runtime result from iPhone, iPad, or Mac.

This is a Framework v1 draft workflow. Results collected before Suite B
workloads, runner, and evidence rules are frozen must remain non-official and
must not enter a performance ranking.

## Steps

1. Choose a fixed model, runtime, prompt, and device.
2. Record model, runtime, OS, and device metadata.
3. Record raw measurements that are actually available.
4. Copy `templates/device-result-template.json`.
5. Fill in all fields you can verify.
6. Fill in the Suite B measurement fields: prompt token band, output token band, warm-up procedure, measurement procedure, measured run count, aggregation method, cold or warm start state, timing boundaries, failed or interrupted run handling, and per-run metrics when available.
7. Add notes for unavailable metrics instead of inventing values.
8. Confirm the JSON parses and follows `methodology/benchmark-result-specification.md`.
9. Open a pull request with the completed JSON and reproduction notes.

The official benchmark app will replace most manual steps in a future release.
App-generated result bundles will be preferred because they can lock the
benchmark release, workload, timing, and environment-capture behavior.

## Measurement Notes

Useful metrics include tokens per second, first token latency, peak memory usage, thermal observations, and battery or energy observations.

Qualitative observations are acceptable during the MVP stage when clearly labeled.

Per-run metrics may include TTFT, prefill tokens/sec, decode tokens/sec, peak memory, thermal state, and notes. Use `null` for metrics that were not collected.
