# Project Vision

## Mission

iOS-LLM-Leaderboard is a community-maintained, reproducible benchmark and
integration reference for iOS developers.

It evaluates large language models from two complementary perspectives:

- models and tools used to build iOS applications;
- models, runtimes, and device configurations embedded inside iOS
  applications.

The project turns credible benchmark evidence into understandable model
comparisons and focused Swift integration guidance.

## Primary Audience

- iOS developers choosing a coding model or editor integration;
- iOS developers selecting a local model and runtime for an app feature;
- runtime maintainers and model publishers validating Apple-platform support;
- reviewers and researchers studying on-device LLM behavior.

## Core Decisions the Project Supports

1. Which model best supports a particular Swift or Xcode workflow?
2. Which local model runs acceptably on a particular Apple device?
3. Which runtime is practical to integrate and distribute in an iOS app?
4. Which model meets both a minimum quality requirement and a deployment
   budget?
5. What short integration recipe should a developer start from?

## Evaluation Tracks

### Developer Assistance

This track evaluates models and tools used during app development.

- Suite A: Swift Code Generation
- Suite C: Xcode Integration

The evaluation unit may be a model or a model-tool configuration, depending on
the task.

### Embedded Intelligence

This track evaluates intelligence running inside an app.

- Suite B: On-device Performance
- Suite D: App Feature Intelligence
- Suite E: Runtime Evaluation

The evidence unit includes the model artifact, runtime, quantization, device,
OS, and inference settings.

## Public Presentation and Evidence

The main leaderboard should be understandable without requiring readers to
decode an internal configuration identifier.

- model names are the primary display unit;
- device and tested-profile information appear as concise context;
- full configuration identity remains available on detail pages;
- raw runs and evidence remain reviewable.

This separates user-facing simplicity from benchmark rigor.

## Community Role

The project should not depend on one maintainer owning every Apple device.

An official benchmark app should allow iOS developers to run a locked benchmark
release on their own hardware and submit a reviewable result bundle with
minimal manual work.

Community scale must not weaken evidence standards. Results should progress
through explicit trust levels rather than entering the default ranking
immediately.

## Developer Convenience

Developers do not need another opinionated starter app. Their app architecture,
UI, and product requirements vary too widely.

The project should instead provide small, focused integration recipes for
tested model and runtime profiles.

## Non-goals

- a universal LLM intelligence leaderboard;
- one global score across all suites;
- an inference framework competing with MLX Swift, llama.cpp, or Core ML;
- simulated or vendor-claimed device results presented as measurements;
- a separate full SwiftUI app for every recommended model;
- legal conclusions about privacy or App Store compliance.
