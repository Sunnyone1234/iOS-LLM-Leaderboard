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

This repository publishes Power Benchmark 1.0 and its workload-specific
official ranking. Historical Pilot and RC evidence remains available with its
original non-official identity.

## Interactive Leaderboard

[**Open the interactive Power + Ship leaderboard →**](https://yizesun.github.io/iOS-LLM-Leaderboard/)

The website combines the immutable Power 1.0 Maintainer Reference evidence
with valid merged community packages. It provides Power workload rankings,
per-cell contributor and variation evidence, plus a sortable Ship deployment
profile view linked to exact tested configurations and Swift integration code.
Its separate **Models to test** view lists pinned, untested artifacts that the
community can run next. Those catalog entries have no rank or performance
claim and never appear in a leaderboard until genuine evidence is accepted.
To preview the site locally from the repository root:

```bash
python3 -m http.server 4173
```

Then open `http://localhost:4173/`. The live dataset begins with the five
eligible Power 1.0 rows and retains the sixth response-ineligible result
outside the ranking. Merged community runs are grouped only with exact
matching configurations. The Ship tab shows three evidence profiles with
explicit verified, implementation-only, and unknown claims. It does not
introduce a global score or change any benchmark rule.

## Product Strategy

The long-term architecture is Build, Power, and Ship, with an explicit delivery
priority.

| Track | Status | Question | Current benchmark-namespace relationship |
| --- | --- | --- | --- |
| Power | Phase 1 product | Which embedded configurations provide useful, acceptable on-device intelligence? | Suite B measurements now; Suite D may add a later quality gate |
| Ship | Phase 1 product | Which tested configurations are practical to integrate and deploy? | Published Ship 1.0 profiles reuse Power 1.0 evidence; Suite E may add later integration evidence |
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

## Current Release: Power Benchmark 1.0

F2–F6 froze and reviewed the Power protocol, result schema, semantic
validator, reference App, physical-device verification matrix, submission
package, and evidence governance. The published release adopts the exact six
F5 RC1 result files without rerunning them because the App and every benchmark
semantic contract remain unchanged. Their original bytes and RC1 identities
remain visible and are bound into Power 1.0 by result ID and SHA-256.

See the [Power 1.0 finalization decision](docs/power-benchmark-1.0-finalization.md),
[generated leaderboard](results/suite-b-power-1.0/LEADERBOARD.md),
[release notes](results/suite-b-power-1.0/RELEASE-NOTES.md), and
[checksums](results/suite-b-power-1.0/SHA256SUMS). The six adopted results are
Maintainer Reference evidence; the five primary-metric-eligible rows are active
in the official workload-specific ranking. See the
[`1.0.0` GitHub Release](https://github.com/YizeSun/iOS-LLM-Leaderboard/releases/tag/1.0.0).

## Current Ship Release: Deployment Profiles 1.0

Ship 1.0 converts the three exact tested Power configurations into versioned,
machine-readable deployment profiles. It reuses all six Maintainer Reference
results, changes no benchmark result or App code, and defines no deployment
score. Claims not established by current evidence remain `Unknown`.

See the [Ship evidence method](docs/ship-deployment-profiles.md),
[deployment profile table](results/ship-1.0/PROFILES.md),
[machine-readable data](results/ship-1.0/deployment-profiles.json), and
[MLX Swift integration recipe](examples/mlx-swift/README.md). The formal
release is tagged [`ship-1.0.0`](https://github.com/YizeSun/iOS-LLM-Leaderboard/releases/tag/ship-1.0.0).

The completed Power + Ship Pilot v0.1 matrix is retained as historical
foundation evidence. It will not be published as a tagged release and its
`0.2.0-pilot` results will not be relabeled as Power 1.0 evidence.

The historical Pilot v0.1 includes exactly two Suite B workload IDs:

- `b-ux-001-short-interaction`;
- `b-pipe-001-sustained-generation`.

`b-pipe-002-input-length-sweep` and `b-ux-002-context-assistance` remain
Experimental and are outside the 1.0 Foundation release contract. No Suite D
or Suite E benchmark task is added; Ship continues to reuse the same tested
Suite B configuration and does not create a deployment score.

The historical Pilot did not activate official rankings, rename suite or
workload IDs, replace historical schemas, or move existing benchmark
directories. See its completed evidence scope in
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
See the [untagged Pilot evidence notes](results/suite-b-pilot-v0.1/RELEASE-NOTES.md)
and [SHA-256 manifest](results/suite-b-pilot-v0.1/SHA256SUMS) for the frozen
historical scope, integrity checks, and known limitations.

## Legacy Suite Namespaces

Suite A–E are retained as Framework v1 benchmark and evidence namespaces. They
are not the public product tracks, do not have equal Phase 1 priority, and do
not replace the Build, Power, and Ship architecture.

| Namespace | Framework v1 focus | Current product status |
| --- | --- | --- |
| Suite A | Swift Code Generation | Compatibility and historical Build research material; excluded from Phase 1 |
| Suite B | On-device Performance | Active measurement foundation for Phase 1 Power |
| Suite C | Xcode Integration | Compatibility and historical Build research material; excluded from Phase 1 |
| Suite D | App Feature Intelligence | Potential later Power quality evidence; no Pilot v0.1 task |
| Suite E | Runtime Evaluation | Potential later Ship integration evidence; no Pilot v0.1 task or score |

The namespaces remain separate so stable IDs, schemas, historical tasks, and
metric ownership stay interpretable during migration. Framework v1 suite
reports must not be mistaken for five parallel product roadmaps, and the
project does not define a single aggregate score across them.

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
Submitted, Reproduced, and Verified. Separately, a valid package merged into
`main` can enter the clearly labeled live community view: one GitHub account
counts once per exact comparison cell, two accounts display as reproduced,
and three or more enable contributor-weighted aggregation. The same account
can contribute to any number of different cells.

See [Community Contribution Model](docs/community-contribution-model.md) and
[Power Community Reproduction and Live Ranking](docs/power-community-ranking.md).

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
- a real physical-iPhone MLX Benchmark App and six-result Power 1.0 dataset
  with immutable raw evidence.

Power 1.0 is the first official benchmark release. Historical Pilot evidence
remains non-official and separate from the official ranking.

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

Community contributions are central to the project. Power 1.0 public result
intake is open for immutable App 0.8.0 build 10 exports using the exact RC1
source contract adopted by the official release. Contributions may also
propose methodology, integrations, and tooling.

Official Power result submission uses the frozen App/result contract and the
hash-bound review process documented below. Passing intake does not
automatically grant a ranking-eligible evidence level.

Start with the [Power 1.0 contributor quickstart](contributor-kit/power-1.0-quickstart.md),
[Power 1.0 public-intake guide](docs/power-benchmark-1.0-public-intake.md),
[CONTRIBUTING.md](CONTRIBUTING.md), and the
[Contributor Kit](contributor-kit/README.md).

## Roadmap

See [ROADMAP.md](ROADMAP.md).

## Citation

If you use this project in research, reporting, or tooling, cite it using
[CITATION.cff](CITATION.cff).
