# iOS-LLM-Leaderboard

iOS-LLM-Leaderboard is a GitHub-first benchmark project for evaluating large language models from an iOS developer perspective.

The project focuses on three practical questions:

1. Which LLM writes the best Swift and SwiftUI code?
2. Which local models run best on iPhone, iPad, and Apple Silicon?
3. Which models are most useful for real iOS app features, privacy, and App Store compliance?

This repository is currently an MVP documentation and structure release. It does not contain a benchmark engine, official rankings, or verified performance numbers yet.

## Why This Project Exists

General LLM leaderboards are useful, but they rarely evaluate the workflows that matter to iOS developers: SwiftUI state management, Apple framework usage, StoreKit, XCTest, Xcode integration, on-device inference, privacy behavior, and App Store-facing product constraints.

This project aims to make those evaluations reproducible, transparent, and useful for developers choosing models for real iOS apps.

## What Is Evaluated

The leaderboard is designed around five independent benchmark suites:

- Swift / SwiftUI code generation
- On-device performance
- Xcode integration experience
- Real iOS app feature tasks
- Runtime comparison, privacy, and App Store compliance

## Benchmark Suites

iOS-LLM-Leaderboard is organized into five independent suites. Each suite may produce its own score, report, or leaderboard. The project does not currently define a single aggregate score across all suites.

| Suite | Name | Focus |
| --- | --- | --- |
| Suite A | Swift Code Generation | Swift, SwiftUI, Apple API, and XCTest code generation quality |
| Suite B | On-device Performance | Local model measurements on iPhone, iPad, and Apple Silicon |
| Suite C | Xcode Integration | Completion, inline fixes, refactoring, and editor workflow fit |
| Suite D | App Feature Intelligence | Product-facing intelligence tasks such as extraction, summarization, translation, safety, and App Store responses |
| Suite E | Runtime Evaluation | Runtime comparison across MLX Swift, llama.cpp, CoreML, LiteRT-LM, Apple Foundation Models, and future Apple runtime APIs |

Suite boundaries are intentional. Swift code generation tasks, app feature intelligence tasks, Xcode workflow tasks, runtime measurements, and on-device performance results should remain separate unless a future methodology explicitly defines an aggregate view.

## Placeholder Leaderboard

The table below is demo data only. It is included to show the intended format and must not be interpreted as a ranking.

| Rank | Model | Provider | Swift Codegen | App Feature | On-device | Privacy | Notes |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| - | DemoModel-A | Demo Provider | 0.00 | 0.00 | N/A | N/A | Placeholder only |
| - | DemoModel-B | Demo Provider | 0.00 | 0.00 | N/A | N/A | Placeholder only |

See [results/LEADERBOARD.md](results/LEADERBOARD.md) for the generated leaderboard placeholder.

## Current MVP Scope

This initial version provides:

- Repository structure for benchmark definitions and results
- Scoring methodology documentation
- Markdown benchmark task templates and starter tasks
- JSON result templates
- Contributor submission guides
- Placeholder example integration directories
- Simple JSON validation and leaderboard generation scripts

This MVP intentionally does not implement real benchmark logic, model execution, device measurement, or automated judging.

## Repository Structure

```text
methodology/           Suite-specific methodology and scoring definitions
benchmarks/            Suite-organized benchmark task definitions
results/               Leaderboard output, raw result folder, and sample JSON
models/                Tested model metadata guidance
devices/               Device metadata guidance
examples/              Starter integration placeholders
templates/             JSON submission templates
contributor-kit/       Contributor submission guides
ios-app/               Future benchmark app planning notes
scripts/               Small utility scripts
```

Benchmark suites live under:

```text
benchmarks/
├── suite-a-swift-codegen/
├── suite-b-on-device-performance/
├── suite-c-xcode-integration/
├── suite-d-app-feature-intelligence/
└── suite-e-runtime-evaluation/
```

## Licensing

This repository uses a dual-license model:

- Code is licensed under the [MIT License](LICENSE).
- Benchmark tasks, prompts, methodology, datasets, leaderboard data, reports, and results are licensed under [Creative Commons Attribution 4.0 International](LICENSE-DATA).

See [LICENSES.md](LICENSES.md) for details.

## How To Contribute

Contributions are welcome for benchmark tasks, result submissions, device runs, methodology improvements, and example integrations. Start with [CONTRIBUTING.md](CONTRIBUTING.md) and the [contributor kit](contributor-kit/README.md).

All submitted benchmark results should include enough metadata for independent review and reproduction.

## Roadmap

See [ROADMAP.md](ROADMAP.md).

## Citation

If you use this project in research, reporting, or tooling, cite it using [CITATION.cff](CITATION.cff).
