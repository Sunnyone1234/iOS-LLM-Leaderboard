# iOS-LLM-Leaderboard

iOS-LLM-Leaderboard is a community-maintained, reproducible benchmark and
integration reference for large language models from an iOS developer
perspective.

It evaluates both:

- models used to build iOS applications; and
- models, runtimes, and device configurations embedded inside iOS applications.

The project is designed to help developers answer three practical questions:

1. Which models are most useful for Swift, SwiftUI, and Xcode workflows?
2. Which local models run best on iPhone, iPad, and Apple Silicon?
3. Which models are suitable for real iOS app features, privacy requirements,
   and deployment constraints?

This repository is currently a documentation-first framework. It does not yet
publish official rankings or verified performance results.

## Product Structure

The project has two evaluation tracks and three product layers.

### Evaluation Tracks

| Track | Question | Suites |
| --- | --- | --- |
| Developer Assistance | Which models and tools best help developers build iOS apps? | Suite A and Suite C |
| Embedded Intelligence | Which models and runtimes best support intelligence inside iOS apps? | Suite B, Suite D, and Suite E |

The tracks remain separate. A cloud coding model and a small on-device model do
not belong in one global ranking.

### Product Layers

| Layer | Purpose |
| --- | --- |
| Benchmark Specification | Versioned tasks, workloads, metrics, schemas, and comparison rules |
| Community Evidence | Real-device runs submitted by iOS developers and classified by evidence level |
| Developer Integration Guide | Model pages, compatibility notes, and small copy-ready Swift integration recipes |

See [Project Vision](docs/project-vision.md) and
[Product Architecture](docs/product-architecture.md).

## Benchmark Suites

| Suite | Name | Focus |
| --- | --- | --- |
| Suite A | Swift Code Generation | Swift, SwiftUI, Apple API, and XCTest code quality |
| Suite B | On-device Performance | Measured local inference on Apple devices |
| Suite C | Xcode Integration | Completion, fixes, refactoring, and editor workflow fit |
| Suite D | App Feature Intelligence | Intelligence used inside real iOS product features |
| Suite E | Runtime Evaluation | Runtime compatibility, integration, licensing, and deployment tradeoffs |

Each suite may produce its own reports and leaderboard views. The project does
not define a single aggregate score across all suites.

Suite B is the first implementation priority.

## Community Benchmark App

The intended contribution path is an official benchmark app that developers can
run on their own devices.

The app should:

- identify the device and OS;
- download or select a versioned compatible model profile;
- run a locked benchmark release;
- collect raw timing, token, memory, thermal, and failure evidence;
- show the contributor exactly what will be submitted; and
- create a repository submission with minimal manual work.

Repository results will progress through evidence levels such as Community
Submitted, Reproduced, and Verified. A single submission should not
automatically enter the default ranking.

See [Community Contribution Model](docs/community-contribution-model.md).

## Leaderboard Experience

The public leaderboard should remain easy to understand:

- model names are the primary display unit;
- device-specific views explain where a result applies;
- the reference runtime and quantization appear as concise supporting labels;
- full configuration and raw evidence remain available on the detail page.

The evidence layer still records the exact model artifact, quantization,
runtime, backend, device, OS, cache policy, and benchmark release. This
configuration detail supports credibility without making the main table
unnecessarily difficult to read.

## Developer Convenience

The project will not assume that developers want to adopt a complete starter
app. iOS apps differ too much in architecture and product requirements.

Instead, model and runtime pages should provide focused integration recipes:

- package installation;
- model loading;
- one-shot generation;
- streaming;
- cancellation;
- context reset;
- local model download or bundling;
- memory and thermal handling;
- licensing and attribution.

Recommended small-model views should show model names prominently and link each
model to a tested reference profile and short Swift examples.

## Benchmark Framework

The current Benchmark Framework v1 documents task and result conventions:

- [Benchmark Framework](methodology/benchmark-framework.md)
- [Benchmark Suites](methodology/benchmark-suites.md)
- [Benchmark Task Specification](methodology/benchmark-specification.md)
- [Benchmark Result Specification](methodology/benchmark-result-specification.md)
- [Benchmark Validation](methodology/benchmark-validation.md)

Framework v1 remains the current repository format while Framework v2 is
designed. The transition must distinguish workloads, measurement modes,
metrics, tasks, and result evidence without presenting draft designs as active
standards.

See [Framework v2 Transition](docs/framework-v2-transition.md).

## Current Repository Contents

- methodology and suite-level design documents;
- initial tasks for Suites A through E;
- detailed draft Suite B measurement protocols;
- Framework v1 result templates and demo placeholders;
- contributor guidance;
- initial validation and leaderboard scripts;
- placeholder directories for future runtime examples and the benchmark app.

No benchmark engine, official rankings, or verified performance dataset is
included yet.

## Result Integrity

- Never invent or simulate device measurements.
- Never present placeholder data as a real ranking.
- Preserve raw observations and configuration identity.
- Keep benchmark releases and task versions explicit.
- Separate evidence quality from performance.
- Do not rank incompatible devices, workloads, or measurement boundaries
  together.

## Licensing

This repository uses a dual-license model:

- code is licensed under the [MIT License](LICENSE);
- benchmark tasks, methodology, datasets, reports, and results are licensed
  under [CC BY 4.0](LICENSE-DATA).

See [LICENSES.md](LICENSES.md).

## Contributing

Community contributions are central to the project. During the current
documentation-first stage, contributions may propose tasks, methodology,
schemas, integrations, and tooling.

Official device-result submission will open only after the Suite B workloads,
runner, schema validation, and evidence rules are frozen.

Start with [CONTRIBUTING.md](CONTRIBUTING.md) and the
[Contributor Kit](contributor-kit/README.md).

## Roadmap

See [ROADMAP.md](ROADMAP.md).

## Citation

If you use this project in research, reporting, or tooling, cite it using
[CITATION.cff](CITATION.cff).
