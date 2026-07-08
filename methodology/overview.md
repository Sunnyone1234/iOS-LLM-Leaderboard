# Methodology Overview

iOS-LLM-Leaderboard is organized around five independent benchmark suites. Each suite evaluates a different part of the iOS developer experience and may produce separate scores, reports, and leaderboards.

The suites are:

- Suite A: Swift Code Generation
- Suite B: On-device Performance
- Suite C: Xcode Integration
- Suite D: App Feature Intelligence
- Suite E: Runtime Evaluation

Suites should not be merged into a single score unless a future methodology explicitly defines how to combine them. During the MVP stage, independent suite-level reporting is preferred.

## Suite Boundaries

- Suite A covers Swift, SwiftUI, Apple API, and XCTest code generation tasks.
- Suite B covers measured local model performance on iPhone, iPad, and Mac devices.
- Suite C covers model behavior inside Xcode-oriented workflows such as completion, inline fixes, and refactoring.
- Suite D covers real app feature intelligence such as extraction, summarization, translation, safety behavior, and App Store-facing writing.
- Suite E covers runtime comparison across MLX Swift, llama.cpp, CoreML, LiteRT-LM, Apple Foundation Models, and future Apple runtime APIs.

Do not mix Swift code generation tasks, app feature intelligence tasks, Xcode workflow tasks, runtime measurements, and on-device performance results.

## Shared Scoring

Shared scoring conventions are documented in [scoring.md](scoring.md). Suite-specific methodology files define additional expectations for each suite.
