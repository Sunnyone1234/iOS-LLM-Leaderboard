# Benchmark Framework v1

> Framework v1 remains the accepted result format during migration. The
> workload-centric [Framework v2 Architecture](benchmark-framework-v2.md) is
> now the design target for Suite B.

Benchmark Framework v1 defines the canonical structure for iOS-LLM-Leaderboard benchmark tasks, results, validation rules, and documentation conventions.

This framework is documentation-first. A non-official physical-iPhone Suite B
pilot runner now exists, but it does not make Framework v1 an automated or
official benchmark standard.

## Goals

The framework prioritizes:

- reproducibility
- consistency
- maintainability
- community contribution
- future extensibility

Benchmark quality is more important than benchmark quantity. Do not invent benchmark results, rankings, or performance numbers.

## Independent Suite Model

iOS-LLM-Leaderboard uses five independent benchmark suites:

- Suite A: Swift Code Generation
- Suite B: On-device Performance
- Suite C: Xcode Integration
- Suite D: App Feature Intelligence
- Suite E: Runtime Evaluation

Each suite may produce separate scores, reports, and leaderboards. Do not combine Suite A, B, C, D, and E into a single global score unless a formal weighting methodology is defined.

## Canonical Framework Documents

- [Benchmark Suites](benchmark-suites.md)
- [Benchmark Task Specification](benchmark-specification.md)
- [Benchmark Result Specification](benchmark-result-specification.md)
- [Benchmark Validation](benchmark-validation.md)
- [Scoring Methodology](scoring.md)

## Repository Conventions

Benchmark task files live under the suite-specific directories in `benchmarks/`.

Result files should be stored as JSON under `results/raw/`.

Official leaderboard generation should only use validated result files and should exclude demo-placeholder results.

## Compatibility Expectations

Changes to benchmark tasks and result files should preserve framework compatibility:

- stable task IDs
- explicit task versions
- required task metadata
- required result fields
- suite-specific reproducibility metadata
- clear placeholder/demo labeling

When a prompt, expected output, scoring rubric, or pass/fail criteria changes materially, update the task version instead of changing the task ID.
