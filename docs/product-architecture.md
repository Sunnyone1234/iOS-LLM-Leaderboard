# Product Architecture 2

## Product Strategy

The long-term product vision is organized around three developer questions:

1. **Build**: can an AI system deliver a complete iOS application?
2. **Power**: can a model provide useful intelligence inside an iOS
   application on the target Apple device?
3. **Ship**: can the tested model, runtime, and device configuration be
   integrated, distributed, and operated responsibly?

These areas are not equal implementation priorities.

The Phase 1 public product is **Power + Ship**. Its purpose is to establish a
trustworthy, reproducible, developer-oriented evaluation standard for
deploying on-device AI on Apple platforms.

The current Power release is
[Power Benchmark 1.1](power-benchmark-1.1-finalization.md). It adopts the
frozen Power 1.1 RC1 execution contract and six immutable physical-device
results under a final ranking policy without rewriting their source identity.
The completed Power + Ship Pilot v0.1 remains non-official historical evidence
and will not be tagged or published as a release. B-UX-001 and B-PIPE-001 are
the only active Power 1.1 workloads; the protocol, schema, validator, App,
physical-device evidence, and governance contracts are complete. All six
adopted results are Maintainer Reference evidence and measured-performance
eligible; five are also recommendation eligible.

**Build is a Phase 2 Research Track.** It remains part of the long-term vision,
but it is not part of the Phase 1 product, benchmark release, public
leaderboard, or success criteria.

This architecture is a strategic positioning decision. It does not activate a
new benchmark framework, change a protocol or stable suite ID, or make any
draft result eligible for official ranking.

## Phase 1 Product: Power + Ship

### Power

Power asks:

> Can this model provide useful intelligence inside an iOS application with
> acceptable behavior on the target Apple device?

Power combines two forms of evidence without collapsing them into one score:

- workload-specific feature quality, where a minimum quality gate is needed;
- measured on-device behavior, including latency, throughput, memory, thermal,
  and failure evidence.

The primary evidence unit is a tested embedded configuration:

```text
model artifact
+ quantization
+ runtime and backend
+ device and OS
+ inference settings
+ versioned workload and measurement mode
```

Model names may remain prominent in public views, but model-only claims are not
sufficient for on-device comparison.

### Ship

Ship asks:

> Can this tested configuration be integrated, distributed, and maintained in
> a real iOS application?

Ship turns Power evidence into practical deployment guidance. It covers facts
and tested capabilities such as:

- supported devices and measured resource limits;
- runtime and model-format compatibility;
- model download or bundling requirements;
- offline execution, streaming, cancellation, and context management;
- integration recipes and known limitations;
- model and runtime license metadata and attribution requirements.

Ship must reuse canonical Power measurements rather than redefining latency,
memory, or thermal metrics. It should present verified capabilities, measured
constraints, warnings, and unknowns rather than a false-precision deployment
score. License and privacy information is evidence for developer review, not a
legal conclusion.

### Phase 1 Success Criteria

Phase 1 succeeds only when Power + Ship provide credible deployment evidence.
Success requires:

- versioned on-device workloads with unambiguous measurement boundaries;
- execution on physical Apple devices through a reviewable reference runner;
- raw attempts and configuration identity sufficient for independent review;
- validation that recalculates supported metrics and preserves failures, OOMs,
  cancellations, and unsupported attempts;
- explicit evidence levels and independent reproduction rules;
- public comparison views that only aggregate compatible configurations;
- deployment profiles and Swift integration recipes linked to tested evidence;
- useful guidance for choosing a model, runtime, and device configuration for
  a concrete on-device use case.

No Build task, coding score, agent comparison, or Xcode workflow is required
for Phase 1 success.

## Phase 1 Evidence Architecture

The project is organized as a closed evidence loop:

1. a benchmark release freezes tasks, workloads, metrics, and schemas;
2. the official benchmark app executes that release on a physical device;
3. the app exports a result bundle;
4. repository automation validates the bundle;
5. community reproduction increases evidence confidence;
6. leaderboard views aggregate compatible results;
7. Power views compare only compatible embedded configurations;
8. Ship profiles provide deployment facts and short integration recipes backed
   by those tested configurations.

## Layer 1: Benchmark Specification

This layer owns:

- suite boundaries;
- versioned workloads;
- measurement procedures;
- metric definitions;
- task and result schemas;
- benchmark release policy;
- comparison and aggregation rules.

It must be possible to determine exactly which benchmark release produced a
result.

## Layer 2: Community Evidence

This layer owns:

- official runner and app versions;
- device and environment capture;
- raw run evidence;
- repository submissions;
- automated and manual validation;
- evidence levels;
- independent reproduction.

The official app lowers contribution effort and reduces uncontrolled
differences. It does not eliminate the need for evidence review.

## Layer 3: Developer Integration Guide

This layer owns:

- model-centered detail pages;
- tested device and runtime information;
- compact Swift recipes;
- runtime installation;
- model loading and generation examples;
- distribution and license notes.

Integration guidance should reference benchmark identities, but it must remain
useful to developers who do not need to understand the full result schema.

## Power Presentation Model

The public view and evidence view serve different readers.

### Public view

- model name;
- model size;
- headline quality and performance indicators;
- supported or verified devices;
- recommended use cases;
- concise reference-profile label.

### Evidence view

- model artifact and revision;
- quantization;
- runtime and backend;
- device and OS build;
- inference settings;
- benchmark release;
- per-run values;
- failure evidence;
- contributor and trust status.

## Recommended Small Models

Recommended small-model lists should show model names, not internal
configuration IDs.

Eligibility should still depend on a tested reference profile and minimum
evidence rules. The recommendation should link to:

- the profile used for the headline result;
- compatible devices;
- known limitations;
- short integration recipes.

## Build Research Track: Phase 2

Build asks the long-term question:

> Can an AI system deliver a complete, reviewable iOS application from product
> intent to release readiness?

Build must not be designed as another collection of isolated Swift snippets,
Apple API examples, or code-completion prompts. Its future scope is complete
software delivery:

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

The future evaluation object would therefore be a software-delivery system,
including the model, agent, tools, configuration, and controlled Xcode
environment, rather than a model in isolation.

This section records direction only. Phase 1 must not create Build protocols,
runners, schemas, or new implementation work.

### Why Build Is Deferred

Coding agents and their tool interfaces are changing faster than a credible
long-lived benchmark can currently be frozen. General code generation and
agent benchmarks are also already well explored, while Apple-platform
on-device deployment still lacks a mature, reproducible, developer-oriented
standard.

Deferring Build:

- concentrates limited project capacity on the clearest unmet developer need;
- avoids coupling Phase 1 credibility to unstable agent products and prompts;
- allows later Build work to evaluate complete delivery rather than repeating
  saturated snippet benchmarks;
- gives the project time to learn from real Xcode automation, simulator,
  accessibility, privacy, and release-readiness workflows.

Build may move from research framing to an implementation plan only after the
Power + Ship standard has a credible release and the project can define a
stable, end-to-end iOS delivery problem. It is not scheduled merely because a
particular coding model or agent becomes popular.

## Suite Relationships

Build, Power, and Ship are a product mapping over the legacy suite layout. This
mapping does not rename a suite, move a directory, or change a stable ID.

| Legacy suite | Product-track mapping | Pilot v0.1 relationship |
| --- | --- | --- |
| Suite A: Swift Code Generation | Build, Phase 2 Research Track | Preserved for compatibility; excluded from Pilot v0.1 |
| Suite B: On-device Performance | Power, Phase 1 | Owns Pilot measurements; only B-UX-001 and B-PIPE-001 are included |
| Suite C: Xcode Integration | Build, Phase 2 Research Track | Preserved for compatibility; excluded from Pilot v0.1 |
| Suite D: App Feature Intelligence | Potential Power quality evidence in later Phase 1 work | No Suite D task is included in Pilot v0.1 |
| Suite E: Runtime Evaluation | Ship compatibility and integration evidence in later Phase 1 work | No Suite E task is executed or scored in Pilot v0.1; the Pilot Ship profile reuses the tested Suite B configuration |

No suite should redefine another suite's canonical metric boundaries.

The existing suite directories, IDs, protocols, schemas, and Benchmark App
remain unchanged by this product architecture. A future migration requires its
own reviewed plan and must preserve Benchmark Framework v1 compatibility.
