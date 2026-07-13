# iOS-LLM-Leaderboard

iOS-LLM-Leaderboard is a community-maintained, reproducible benchmark and
integration reference for deploying on-device AI on Apple platforms.

The Phase 1 public product is organized around two questions:

- **Power**: can a model provide useful intelligence inside an iOS app with
  acceptable behavior on the target Apple device?
- **Ship**: can the tested model, runtime, and device configuration be
  integrated and distributed in a real app?

The long-term vision also includes **Build**, but Build is a Phase 2 Research
Track rather than a Phase 1 product. Its future subject is complete iOS software
delivery, not isolated Swift snippets or code completion.

The Phase 1 product helps developers answer:

1. Which local models run best on iPhone, iPad, and Apple Silicon?
2. Which configurations meet the quality and performance needs of real app
   features?
3. Which models and runtimes fit practical integration, distribution,
   privacy-review, and deployment constraints?

This repository is currently a documentation-first framework. It does not yet
publish official rankings or verified performance results.

## Interactive Leaderboard

[**Open the interactive Power leaderboard →**](https://yizesun.github.io/iOS-LLM-Leaderboard/)

The website reads the same checked-in `normalized-results.json` used by the
auditable Markdown reports. It provides workload tabs, configuration filters,
sortable metric columns, deployment facts, and direct links to raw evidence.
Until GitHub Pages is enabled, preview it locally from the repository root:

```bash
python3 -m http.server 4173
```

Then open `http://localhost:4173/`. The site remains explicitly Pilot evidence;
it does not introduce a global score or change any benchmark rule.

## Product Strategy

The long-term architecture is Build, Power, and Ship, with an explicit delivery
priority.

| Track | Status | Question | Current suite relationship |
| --- | --- | --- | --- |
| Power | Phase 1 product | Which embedded configurations provide useful, acceptable on-device intelligence? | Suite B and applicable Suite D quality work |
| Ship | Phase 1 product | Which tested configurations are practical to integrate and deploy? | Suite E evidence reusing Suite B measurements |
| Build | Phase 2 Research Track | Can an AI system deliver a complete iOS application? | Suite A and Suite C retained for compatibility, not Phase 1 priority |

Phase 1 success is based entirely on trustworthy Power + Ship evidence. No
coding task, coding-agent comparison, or Xcode workflow is required for Phase 1
success.

### Product Layers

| Layer | Purpose |
| --- | --- |
| Benchmark Specification | Versioned tasks, workloads, metrics, schemas, and comparison rules |
| Community Evidence | Real-device runs submitted by iOS developers and classified by evidence level |
| Developer Integration Guide | Model pages, compatibility notes, and small copy-ready Swift integration recipes |

See [Project Vision](docs/project-vision.md) and
[Product Architecture](docs/product-architecture.md).

## Current Release Target: Power + Ship Pilot v0.1

The current release target is a narrow, non-official Pilot that validates the
Power evidence path and an evidence-linked Ship profile with 2–3 exact model
artifacts, one reference runtime, and 1–2 physical iPhone models.

Pilot v0.1 includes exactly two Suite B workload IDs:

- `b-ux-001-short-interaction`;
- `b-pipe-001-sustained-generation`.

`b-pipe-002-input-length-sweep` and `b-ux-002-context-assistance` remain
Experimental and are excluded from Pilot eligibility and comparison. No Suite
D or Suite E benchmark task is added to the Pilot; its Ship output reuses the
same tested Suite B configuration and does not create a deployment score.

The Pilot does not activate official rankings, rename suite or workload IDs,
replace historical schemas, or move existing benchmark directories. The App
remains non-official Pilot infrastructure and is versioned when reliability
fixes change its behavior. See the complete scope, publication checklist, and
readiness gates in
[Power + Ship Pilot v0.1](docs/power-ship-pilot-v0.1.md).

Unmodified App exports can be placed under
`results/suite-b-pilot-v0.1/raw/` and processed with:

```bash
python3 scripts/generate_suite_b_pilot.py
```

The generated [Pilot leaderboard](results/suite-b-pilot-v0.1/LEADERBOARD.md)
and [Ship evidence view](results/suite-b-pilot-v0.1/SHIP-EVIDENCE.md) contain the
complete six-result physical-iPhone Pilot matrix: three exact model artifacts,
one iPhone 14 Pro Max, and both frozen workloads. All six App 0.6.0 build 8
exports are genuine, retained unmodified, and accepted by the Pilot pipeline.
See the [Pilot v0.1 release notes](results/suite-b-pilot-v0.1/RELEASE-NOTES.md)
and [SHA-256 manifest](results/suite-b-pilot-v0.1/SHA256SUMS) for the frozen
release-candidate scope, integrity checks, and known limitations.

## Benchmark Suites

| Suite | Name | Focus |
| --- | --- | --- |
| Suite A | Swift Code Generation | Existing Build research material; not a Phase 1 priority |
| Suite B | On-device Performance | Measured local inference on Apple devices |
| Suite C | Xcode Integration | Existing Build research material; not a Phase 1 priority |
| Suite D | App Feature Intelligence | Quality evidence for intelligence used inside product features |
| Suite E | Runtime Evaluation | Ship compatibility, integration, licensing, and deployment evidence |

Each suite may produce its own reports and leaderboard views. The project does
not define a single aggregate score across all suites.

Suite B remains the first implementation priority and the measurement
foundation for Phase 1 Power. Ship guidance must reuse this evidence rather
than redefine its metrics.

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

See [Framework v2 Transition](docs/framework-v2-transition.md),
[Framework v2 Architecture](methodology/benchmark-framework-v2.md), and the
draft [Suite B Protocol v2](benchmarks/suite-b-on-device-performance/protocol-v2.md).

## Current Repository Contents

- methodology and suite-level design documents;
- initial tasks for Suites A through E;
- a workload-centric Suite B v2 design with four draft workload manifests;
- Framework v1 result templates and demo placeholders;
- contributor guidance;
- Framework v1 and Suite B pilot validation tooling;
- a real physical-iPhone MLX Benchmark App pilot with local JSON export.

No official benchmark release, ranking, or verified performance dataset is
included yet. The App and its exports remain explicitly non-official pilot
infrastructure.

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
