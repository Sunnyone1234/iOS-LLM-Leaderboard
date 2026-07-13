# AGENTS.md

# iOS-LLM-Leaderboard

This document defines repository-wide development conventions for AI coding agents working on this project.

---

# Project Vision

iOS-LLM-Leaderboard is an open benchmark project for evaluating Large Language Models from an iOS developer's perspective.

The project prioritizes:

- credibility
- reproducibility
- transparency
- community contributions
- long-term maintainability
- understandable model-centered leaderboard views
- low-friction official benchmark app submissions
- focused Swift integration recipes

Benchmark quality is always more important than benchmark quantity.

The product architecture is defined in:

- docs/project-vision.md
- docs/product-architecture.md
- docs/community-contribution-model.md
- docs/framework-v2-transition.md
- methodology/benchmark-framework-v2.md
- benchmarks/suite-b-on-device-performance/protocol-v2.md

---

# Guiding Principles

When making changes:

- Never invent benchmark results.
- Never fabricate measurements.
- Never simulate device performance.
- Never create fake leaderboards.
- Never present placeholder data as real benchmark data.

If real benchmark data is unavailable, clearly label all examples as placeholder or demo data.

---

# Documentation First

During the MVP stage:

- Prefer documentation over implementation.
- Prefer templates over automation.
- Prefer clear methodology over benchmark coverage.
- Avoid implementing complex benchmark infrastructure unless explicitly requested.

---

# Repository Organization

The repository follows these conventions:

MIT License

- examples/
- scripts/
- future source code
- future iOS benchmark app

CC BY 4.0

- benchmarks/
- methodology/
- benchmark datasets
- benchmark results
- leaderboard data

Keep this separation consistent.

---

# Suite Organization

All benchmark tasks and methodology must be organized under the correct suite:

- Suite A: Swift Code Generation
- Suite B: On-device Performance
- Suite C: Xcode Integration
- Suite D: App Feature Intelligence
- Suite E: Runtime Evaluation

Do not mix Swift code generation tasks, app feature intelligence tasks, Xcode workflow tasks, runtime measurements, and on-device performance results.

---

# Benchmark Framework Compatibility

Agents must preserve Benchmark Framework v1 compatibility.

When editing benchmark tasks:

- Follow `methodology/benchmark-specification.md`.
- Preserve stable `task_id` values.
- Update task versions instead of changing task IDs when prompts, expected outputs, scoring rubrics, or pass/fail criteria change materially.
- Keep suite-specific task requirements intact.

When editing benchmark results or templates:

- Follow `methodology/benchmark-result-specification.md`.
- Preserve required result fields.
- Preserve task and result schema compatibility.
- Keep demo-placeholder results clearly marked.
- Never include demo-placeholder results in official leaderboard logic or documentation.

Agents must not invent benchmark results, rankings, or performance numbers.

Framework v2 is currently a design target. Do not present Framework v2 fields,
tasks, trust levels, or releases as active until their schemas, migration
rules, and validators are implemented.

For new Suite B design:

- use versioned workloads and measurement modes;
- collect TTFT, prefill, decode, memory, and thermal as metrics from compatible
  attempts rather than creating one task per metric;
- label user-experience workloads and pipeline profiles explicitly;
- never relabel Pipeline TTFT as user-visible TTFT;
- preserve every failed, cancelled, OOM, and not-run attempt; and
- keep pilot results ineligible for official ranking.

---

# Benchmark Philosophy

Every benchmark should be:

- reproducible
- clearly documented
- independently reviewable
- practical for real iOS developers

Benchmark tasks should evaluate realistic development workflows instead of artificial coding puzzles whenever possible.

---

# Community Contributions

When adding benchmark tasks:

Include:

- task description
- benchmark prompt
- expected behavior
- scoring rubric
- reviewer notes

When adding benchmark results:

Always record sufficient metadata so results can be reproduced.

User-facing leaderboard rows may emphasize model names, but the evidence layer
must preserve the exact model artifact, quantization, runtime, device, OS, and
inference settings required to interpret the result.

---

# Coding Guidelines

Prefer:

- simple architecture
- readable documentation
- incremental improvements
- modular organization

Avoid:

- unnecessary abstractions
- premature optimization
- unnecessary dependencies
- large repository refactors unless explicitly requested

---

# AI Agent Guidelines

When multiple implementation choices exist:

- Choose the simplest maintainable solution.
- Preserve backward compatibility whenever practical.
- Keep documentation synchronized with repository changes.
- Keep examples easy to copy into real iOS projects.
- Design features with community contribution in mind.
- Prefer small integration recipes over duplicated full starter apps unless a
  task explicitly requires a complete reference application.

When uncertain, optimize for clarity, reproducibility, and maintainability rather than feature completeness.

---

# Scope

This repository is primarily a benchmark and documentation project.

Its purpose is not to become another LLM framework or inference engine.

Only implement infrastructure that directly supports benchmark creation, execution, validation, visualization, or community contribution.
