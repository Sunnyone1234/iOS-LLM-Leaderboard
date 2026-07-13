# Benchmark Suites

iOS-LLM-Leaderboard is organized around five independent benchmark suites.

Suite A and Suite C belong to the Developer Assistance track. Suite B, Suite D,
and Suite E belong to the Embedded Intelligence track. Track membership does
not create a shared score.

## Suite A: Swift Code Generation

Suite A evaluates whether an LLM can generate production-quality Swift and SwiftUI code.

Example categories:

- SwiftUI
- Navigation
- Animation
- List
- Charts
- Widgets
- Networking
- SwiftData
- CoreData
- CloudKit
- StoreKit2
- Concurrency
- MVVM
- Testing
- Accessibility
- Performance

Typical scoring:

- Compile success: 30%
- Functional correctness: 30%
- Swift idiomatic quality: 20%
- Modern Apple API usage: 10%
- Readability and architecture: 10%

## Suite B: On-device Performance

Suite B evaluates local model performance on Apple devices.

Suite B is the first implementation priority. A physical-iPhone pilot runner
exists, but it remains non-official while the workload-centric v2 protocol is
designed and validated.

Example metrics:

- TTFT
- prefill tokens/sec
- decode tokens/sec
- peak memory
- thermal behavior
- energy usage
- token latency distribution
- p50 / p95 / p99 token interval

Suite B v2 uses user-experience workloads and pipeline profiles. The listed
metrics are collected together from compatible attempts rather than becoming
independent future tasks. See
[Suite B Protocol v2](../benchmarks/suite-b-on-device-performance/protocol-v2.md).

## Suite C: Xcode Integration

Suite C evaluates developer workflows inside Xcode-style environments.

Example categories:

- code completion
- inline fix
- refactoring
- compiler error repair
- documentation generation
- code explanation
- build-error recovery

## Suite D: App Feature Intelligence

Suite D evaluates model capabilities used inside real iOS apps.

Example categories:

- information extraction
- summarization
- translation
- structured output
- planning
- classification
- roleplay
- safety

## Suite E: Runtime Evaluation

Suite E evaluates local inference runtimes and model-runtime pairs. It compares runtimes, not only models.

Example runtime targets:

- MLX Swift
- CoreML
- llama.cpp
- LiteRT-LM
- Apple Foundation Models
- future Apple runtime APIs

Suite E must clearly state whether a task evaluates a runtime, a model, or a model-runtime pair.

## Suite Boundaries

Do not mix Swift code generation tasks, app feature intelligence tasks, Xcode workflow tasks, runtime measurements, and on-device performance results.

Suite-level scores and reports should remain separate unless a future methodology defines a formal aggregate score.
