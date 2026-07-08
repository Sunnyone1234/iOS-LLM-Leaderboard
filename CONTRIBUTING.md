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

Every benchmark task should include:

- Task title
- Scenario
- Prompt
- Expected behavior
- Scoring rubric
- Notes for reviewers

Place every task in the correct suite directory:

- `benchmarks/suite-a-swift-codegen/`
- `benchmarks/suite-b-on-device-performance/`
- `benchmarks/suite-c-xcode-integration/`
- `benchmarks/suite-d-app-feature-intelligence/`
- `benchmarks/suite-e-runtime-evaluation/`

Do not mix Swift code generation tasks, app feature intelligence tasks, Xcode workflow tasks, runtime measurements, and on-device performance results.

Do not add tasks that depend on private data, undisclosed model access, or unverifiable scoring.

## Result Contributions

Every result should include:

- model name
- provider
- task ID
- score
- evaluator
- date
- notes

Additional metadata is encouraged when it improves reproducibility.

## Data Integrity

Do not invent benchmark results, rankings, device measurements, or performance numbers. Placeholder examples must be clearly labeled as placeholder or demo data.

## Pull Request Checklist

- Documentation is updated.
- New or moved benchmark content is in the correct suite.
- Placeholder data is clearly labeled.
- JSON files validate with `python3 scripts/validate_result.py <file>`.
- Generated leaderboard changes are intentional.
- License boundaries remain consistent.
