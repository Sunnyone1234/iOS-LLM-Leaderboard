# Sample Device Run

> **Historical Framework v1 sample:** this is not an executable Suite B v2
> workload. Use the versioned manifests in `workloads/` for new runner work.

## Scenario

A contributor records an on-device local model run.

## Prompt

Run the selected local model with a fixed prompt and record raw performance observations.

## Expected Behavior

- Records device metadata.
- Records model and runtime metadata.
- Reports tokens per second and first token latency when available.
- Clearly labels qualitative thermal or battery observations.

## Scoring Rubric

This is a reporting template, not a scored benchmark task.

## Notes for Reviewers

Do not merge submissions that omit device, runtime, or model metadata needed for reproduction.
