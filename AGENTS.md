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

Benchmark quality is always more important than benchmark quantity.

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

When uncertain, optimize for clarity, reproducibility, and maintainability rather than feature completeness.

---

# Scope

This repository is primarily a benchmark and documentation project.

Its purpose is not to become another LLM framework or inference engine.

Only implement infrastructure that directly supports benchmark creation, execution, validation, visualization, or community contribution.
