# Project Vision

## Mission

iOS-LLM-Leaderboard is a community-maintained, reproducible benchmark and
integration reference for deploying on-device AI on Apple platforms.

The Phase 1 product helps developers answer two connected questions:

- **Power**: which model, runtime, and device configurations can provide useful
  intelligence inside an application?
- **Ship**: which tested configurations are practical to integrate,
  distribute, and operate?

The project turns credible benchmark evidence into understandable model
comparisons and focused Swift integration guidance.

The long-term vision also includes **Build**: whether an AI system can deliver
a complete iOS application. Build is explicitly a Phase 2 Research Track, not
part of the Phase 1 public product or its success criteria.

## Primary Audience

- iOS developers selecting a local model and runtime for an app feature;
- runtime maintainers and model publishers validating Apple-platform support;
- reviewers and researchers studying on-device LLM behavior.

In Phase 2, the audience may expand to developers evaluating complete iOS
software-delivery systems.

## Core Decisions the Project Supports

1. Which local model runs acceptably on a particular Apple device?
2. Which runtime is practical to integrate and distribute in an iOS app?
3. Which model meets both a minimum quality requirement and a deployment
   budget?
4. What short integration recipe should a developer start from?

## Product Tracks

### Phase 1: Power

Power evaluates intelligence embedded inside an app, including workload quality
and measured on-device behavior.

- Suite B: On-device Performance
- applicable embedded-feature work from Suite D: App Feature Intelligence

The evidence unit includes the exact model artifact, runtime, quantization,
device, OS, inference settings, workload, and measurement mode.

### Phase 1: Ship

Ship translates tested Power evidence into deployment guidance.

- Suite E can contribute runtime compatibility and integration evidence.
- Developer recipes link deployment claims to tested reference profiles.
- Suite B remains the canonical owner of device performance measurements.

The current delivery target is the
[Power Benchmark 1.0 final review package](power-benchmark-1.0-finalization.md).
It freezes only B-UX-001 and B-PIPE-001, adopts the completed physical-device
matrix without rewriting its RC1 source identity, and keeps publication and
the default ranking disabled until explicit final approval. It does not add a
Suite D or Suite E task.

### Phase 2 Research Track: Build

Build is the long-term evaluation of complete iOS software delivery, from a
product requirement through planning, implementation, compilation, testing,
simulator validation, accessibility, privacy review, and App Store readiness.

Suite A and Suite C remain stable compatibility categories, but isolated code
generation and completion tasks do not define the future Build product. No
Build protocols, schemas, runners, or public rankings are part of Phase 1.

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
- a Phase 1 coding-model or coding-agent leaderboard;
- one global score across all suites;
- an inference framework competing with MLX Swift, llama.cpp, or Core ML;
- simulated or vendor-claimed device results presented as measurements;
- a separate full SwiftUI app for every recommended model;
- legal conclusions about privacy or App Store compliance.
