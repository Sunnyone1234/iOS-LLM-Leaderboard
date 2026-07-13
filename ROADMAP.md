# Roadmap

## Product Priorities

The long-term vision is **Build + Power + Ship**, but the tracks are not equal
delivery priorities.

- **Product Phase 1: Power + Ship.** Establish a trustworthy, reproducible,
  developer-oriented standard for on-device AI deployment on Apple platforms.
- **Product Phase 2: Build Research Track.** Explore how to evaluate complete
  iOS software delivery after the Phase 1 standard is credible.

All execution milestones below through the Power leaderboard and developer
integration guide belong to Product Phase 1. Phase 1 success is determined
entirely by Power + Ship evidence; it does not depend on Suite A, Suite C, a
coding score, or a coding-agent leaderboard.

The long-term roadmap follows one dependency chain:

> benchmark definition → official benchmark app → community evidence →
> validated leaderboard → developer integration recipes

Later phases must not be presented as complete before their dependencies are
validated.

The completed, untagged Pilot v0.1 used maintainer-collected, unmodified
physical-device exports through the internal Pilot ingestion command. It is
retained as historical foundation evidence and will not be published as a
tagged release.

## Product Phase 1: Power + Ship

### Current standardization target: Power Benchmark 1.0 Foundation

The active target is the pre-release
[Power Benchmark 1.0 Foundation](docs/power-benchmark-1.0-foundation.md), using
only these stable candidates:

- `b-ux-001-short-interaction`;
- `b-pipe-001-sustained-generation`.

B-PIPE-002 and B-UX-002 remain Experimental. No additional workload, Suite D
task, Suite E task, global score, or Build deliverable is part of the 1.0
Foundation contract. Ship output remains an evidence profile for the same
tested Suite B configuration.

The active work order and 1.0 release gate are defined in
[Power Benchmark 1.0 Foundation](docs/power-benchmark-1.0-foundation.md). The
completed Pilot scope remains documented in
[Power + Ship Pilot v0.1](docs/power-ship-pilot-v0.1.md).

### Milestone 0: Vision and Architecture

- Define Power and Ship as the Phase 1 public product.
- Preserve Build as a Phase 2 Research Track.
- Define the Benchmark Specification, Community Evidence, and Developer
  Integration Guide layers.
- Keep the five Framework v1 suite namespaces independent for compatibility and
  evidence ownership; do not treat them as equal product tracks.
- Confirm that the public leaderboard is model-centered while full
  configuration identity remains available as evidence.
- Define the role of the official community benchmark app.

### Milestone 1: Framework v2 Design

- Separate workload, task, measurement mode, metric, and result.
- Define a common result envelope with suite-specific payloads.
- Define benchmark releases and migration rules.
- Define model artifact, runtime build, device profile, and inference
  configuration identities.
- Define result bundles and raw evidence requirements.
- Publish a Framework v1 to v2 migration map before changing stable IDs.

Framework v1 remains active until these rules are accepted and implemented.

Progress: the draft object model, Suite B workload categories, metric set,
pilot schemas, and migration direction are now documented. They remain draft.

### Milestone 2: Suite B Complete Specification

- Freeze B-UX-001 and B-PIPE-001 as the only Pilot workload candidates.
- Keep B-PIPE-002 and B-UX-002 Experimental until their documented promotion
  requirements are satisfied.
- Define TTFT, prefill, decode, memory, thermal, and failure metrics.
- Freeze token counting, cache, warm-up, run-count, aggregation, and environment
  rules.
- Define a pilot validation plan using one device, model, and runtime.

### Milestone 3: Official iOS Benchmark App MVP

- Target physical iPhone devices first.
- Use a runtime-neutral adapter architecture.
- Implement MLX Swift as the first reference adapter.
- Run benchmark releases without network access during measured phases.
- Export a result bundle containing summary, raw runs, environment, and
  workload identity.
- Allow contributors to review all submitted fields.

Progress: the MLX physical-iPhone pilot now loads a pinned Qwen3 artifact,
runs one warm-up and five measured attempts, captures raw token timing, sampled
process footprint and thermal boundaries, and exports local JSON. It remains a
non-official instrumentation baseline.

Stage 1 is complete for Qwen3 0.6B on one iPhone across both Pilot workloads.
The App 0.6.0 build 8 matrix is also complete: all three fixed Qwen3 profiles
were run on the same iPhone across both workloads, producing 6 normalized and
eligible results with 0 rejection. The Pilot remains non-official evidence and
does not activate Suite B 1.0.

### Milestone 4: Validation and Repository Submission

- Add machine-readable JSON Schemas.
- Validate task, benchmark release, workload hash, and result structure.
- Recalculate supported metrics from raw event evidence.
- Add GitHub workflows and contribution templates.
- Support low-friction result submission from the benchmark app.
- Generate a pull request or bot-managed repository submission rather than
  writing directly to the default branch.

### Milestone 5: Community Evidence

- Classify results as Draft, Community Submitted, Reproduced, Verified, or
  Maintainer Reference.
- Require independent reproduction for the default community ranking.
- Publish device-coverage gaps so contributors can see which iPhone models
  still need results.
- Preserve failed, OOM, interrupted, and unsupported runs as evidence.

### Milestone 6: Power Leaderboard

- Generate separate views by device, workload, metric, benchmark release, and
  evidence level.
- Display model names prominently.
- Show a concise tested-profile label in the main view.
- Put full runtime, quantization, OS, and raw evidence on detail pages.
- Do not publish a global cross-suite score.

### Milestone 7: Ship Profiles and Developer Integration Guide

- Add short Swift recipes for supported runtimes and model profiles.
- Cover installation, loading, generation, streaming, cancellation, context
  management, model distribution, and licensing.
- Publish recommended small-model views only when enough reproduced or verified
  results exist.
- Link each model recommendation to a tested reference profile.
- Avoid maintaining a separate full app for every recommended model.
- Publish runtime compatibility and deployment facts without duplicating Suite
  B performance metrics.
- Represent supported capabilities, constraints, warnings, and unknowns rather
  than producing a false-precision Ship score.

### Milestone 8: Phase 1 Quality and Deployment Coverage

Recommended order:

1. Suite D minimum quality gate for recommended local models.
2. Suite E runtime integration scorecards that reuse Suite B measurements.

Suite A and Suite C are not part of this milestone or any other Product Phase 1
success criterion.

## Product Phase 2: Build Research Track

Build is deferred because coding agents, tool interfaces, and development
workflows are changing extremely quickly. General code generation and agent
benchmarks are already well explored, while on-device AI deployment lacks a
mature Apple-platform standard. Expanding into coding-agent evaluation now
would split project focus before Power + Ship have established credible
evidence and community value.

Build will not continue as a collection of Swift snippets, API examples, or
code-completion prompts. Its long-term research question is whether an AI
software-delivery system can take an iOS product through:

```text
Product Requirement
        ↓
Engineering Planning
        ↓
Implementation
        ↓
Compilation
        ↓
Testing
        ↓
Simulator Validation
        ↓
Accessibility Review
        ↓
Privacy Review
        ↓
App Store Readiness
```

This is a vision record only. Product Phase 1 will not create Build benchmark
protocols, schemas, runners, or implementation infrastructure. Build should
receive an implementation plan only after Power + Ship have a credible public
release and a stable end-to-end iOS delivery problem can be defined.

## Current Immediate Work

- Keep current Pilot results explicitly non-official and untagged.
- Align the App-emitted historical result schema, semantic validator, and
  regression coverage.
- Freeze immutable Power 1.0 release identity and Pilot migration rules.
- Resolve the protocol and evidence gaps listed in the Foundation work order.
- Keep both Experimental workloads outside the 1.0 release contract.
- Do not publish Power 1.0 until every Foundation release gate passes.
