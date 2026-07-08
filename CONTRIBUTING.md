# Contributing

Thank you for helping improve iOS-LLM-Leaderboard.

This project values reproducibility, transparent methodology, and practical usefulness for iOS developers. Benchmark quality is more important than benchmark quantity.

## Licensing

By submitting a pull request, you agree that your contribution will be licensed under the same licensing model as this repository (MIT for code and CC BY 4.0 for benchmark data and documentation).

## Ways To Contribute

- Submit benchmark results with reproducible metadata.
- Submit device benchmark results for iPhone, iPad, or Mac.
- Propose new benchmark tasks.
- Improve methodology documents.
- Add example integrations for iOS developers.
- Improve validation and leaderboard tooling.

## Benchmark Task Contributions

New benchmark tasks must follow [Benchmark Task Specification](methodology/benchmark-specification.md).

Every benchmark task should include:

- required task metadata
- objective and background
- exact input, prompt, IDE context, or measurement setup
- expected output
- automatic and manual evaluation criteria
- pass and failure conditions
- scoring rubric
- reproducibility requirements
- reviewer notes

Place every task in the correct suite directory:

- `benchmarks/suite-a-swift-codegen/`
- `benchmarks/suite-b-on-device-performance/`
- `benchmarks/suite-c-xcode-integration/`
- `benchmarks/suite-d-app-feature-intelligence/`
- `benchmarks/suite-e-runtime-evaluation/`

Do not mix Swift code generation tasks, app feature intelligence tasks, Xcode workflow tasks, runtime measurements, and on-device performance results.

Do not add tasks that depend on private data, undisclosed model access, or unverifiable scoring.

## Result Contributions

New benchmark results must follow [Benchmark Result Specification](methodology/benchmark-result-specification.md).

Every result must include:

- required result fields
- task ID and task version
- model and provider metadata
- execution date and evaluator
- score, max score, and pass/fail state
- contributor license confirmation
- suite-specific runtime, device, metric, or output metadata where applicable

Submitted results must include enough reproducibility metadata for independent review. If a field is not applicable, use `null` instead of omitting required fields.

For Suite B result submissions, include prompt token band, output token band, warm-up procedure, measurement procedure, measured run count, aggregation method, cold or warm start state, timing boundaries, failed or interrupted run handling, and per-run metrics when available.

Demo or placeholder data must be clearly marked and must not be used for official leaderboard results.

## Data Integrity

Do not invent benchmark results, rankings, device measurements, or performance numbers. Placeholder examples must be clearly labeled as placeholder or demo data.

## Pull Request Checklist

- Documentation is updated.
- New or moved benchmark content is in the correct suite.
- New benchmark tasks follow `methodology/benchmark-specification.md`.
- New benchmark results follow `methodology/benchmark-result-specification.md`.
- Submitted results include reproducibility metadata.
- Placeholder data is clearly labeled.
- JSON files parse successfully and follow `methodology/benchmark-result-specification.md`.
- Generated leaderboard changes are intentional.
- License boundaries remain consistent.
