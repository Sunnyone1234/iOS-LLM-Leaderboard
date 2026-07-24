<p align="center">
  <img src="docs/assets/readme/header-v2.svg" width="100%" alt="Compare small language models on real iPhones using reproducible on-device evidence">
</p>

<p align="center">
  <a href="https://yizesun.github.io/iOS-LLM-Leaderboard/"><img src="docs/assets/readme/open-leaderboard-v2.svg" width="360" alt="Compare models on iPhone"></a>
</p>

<p align="center">
  <a href="contributor-kit/power.md">Run the benchmark</a>
  &nbsp;&nbsp;·&nbsp;&nbsp;
  <a href="docs/power.md">Read the methodology</a>
</p>

<p align="center">
  <img alt="Power 2 activation candidate" src="https://img.shields.io/badge/Power_2-activation_candidate-bf8700?style=flat-square">
  <a href="https://github.com/YizeSun/iOS-LLM-Leaderboard/releases/tag/ship-1.0.0"><img alt="Ship 1.0" src="https://img.shields.io/badge/Ship-1.0-a94747?style=flat-square"></a>
  <a href="https://github.com/YizeSun/iOS-LLM-Leaderboard/actions/workflows/power-community-ranking.yml"><img alt="Power community ranking checks" src="https://github.com/YizeSun/iOS-LLM-Leaderboard/actions/workflows/power-community-ranking.yml/badge.svg?branch=main"></a>
  <a href="https://yizesun.github.io/iOS-LLM-Leaderboard/"><img alt="Leaderboard live" src="https://img.shields.io/badge/leaderboard-live-238636?style=flat-square"></a>
  <a href="LICENSE"><img alt="MIT and CC BY 4.0 licenses" src="https://img.shields.io/badge/license-MIT%20%2B%20CC%20BY%204.0-57606a?style=flat-square"></a>
</p>

## What you can learn

- **Power:** compare response speed, generation speed, memory use, and thermal
  behavior for exact model configurations on physical Apple devices.
- **Ship:** check what is known about integrating and distributing a tested
  configuration in an iOS app.
- **Build Research:** follow the longer-term research into whether an AI system
  can deliver a complete, reviewable iOS application. This is not a current ranking.

The leaderboard never ranks a model name in isolation. Evidence always keeps
the model artifact and revision, quantization, runtime, device, OS, settings,
workload, and App version together.

Running the Benchmark App produces one **Power result**. It does not create or
verify a Ship profile. Ship is a separate downstream product: it may cite
accepted Power measurements, then adds independently reviewed integration,
packaging, licensing, limitations, and unknowns.

<p align="center">
  <img src="docs/assets/readme/power-ship-flow-v2.svg" width="100%" alt="A Benchmark App test produces Power evidence; a separate Ship process may cite accepted Power facts in deployment guidance">
</p>

## Current releases

| Product | Status | What is public |
| --- | --- | --- |
| Power 2 | Activation candidate | Text performance × physical iPhone cell; automated checks pass and exact Official build 4 physical validation is pending |
| Ship 1.0 | Published separately | Deployment profiles and a focused MLX Swift recipe derived separately from accepted Power 1.0 evidence |
| Build | Research | Long-term complete-software-delivery research; no protocols or ranking yet |

Power 2 is a clean replacement rather than a compatibility release. Its
Program, physical-iPhone Target, exact models, Runner certificate, App
identity, intake policy, and ranking policy form one hash-pinned stack.
Public intake stays closed until the immutable Official App release and
`products/power/current.json` are issued together. Power 1.1 evidence and
release manifests remain a read-only historical archive and are never input
to the Power 2 App, validator, workflow, or ranking.

Ship 1.0 is not part of Power 1.1 and is not produced by a benchmark run. Its
separate publication uses accepted Power 1.0 measurements as cited source
evidence and combines them with reviewed integration facts, limitations, and
unknowns. See the
[profiles](results/ship-1.0/PROFILES.md) and
[integration recipe](examples/mlx-swift/README.md).

## Suite map

The A–E namespaces remain visible so stable IDs and historical work stay easy
to locate. They are not five equal product priorities.

| Suite | Scope | Product role now |
| --- | --- | --- |
| [Suite A](benchmarks/suite-a-swift-codegen/) | Swift Code Generation | Build Research; retained, not active in Phase 1 ranking |
| [Suite B](benchmarks/suite-b-on-device-performance/) | On-device Performance | Historical foundation; current Power contracts live under `products/power/` |
| [Suite C](benchmarks/suite-c-xcode-integration/) | Xcode Integration | Build Research; retained, not active in Phase 1 ranking |
| [Suite D](benchmarks/suite-d-app-feature-intelligence/) | App Feature Intelligence | Future Power quality evidence; no active release |
| [Suite E](benchmarks/suite-e-runtime-evaluation/) | Runtime Evaluation | Future Ship evidence; no active release |

## Contribute a real-device result

1. Follow the [current Power quickstart](contributor-kit/power.md)
   and run one model on one physical device.
2. Export the untouched JSON result from the Benchmark App.
3. Use **Submit to GitHub** in a configured App build, or create the same
   two-file pull-request package on a Mac:

```bash
python3 scripts/power submit /path/to/result.json \
  --github YOUR_GITHUB_HANDLE \
  --accept-declarations
```

4. For the CLI path, commit the generated directory and open a pull request
   from the same GitHub account named in the manifest.

CI validates the package, current stack, contributor identity,
duplicates, and ranking eligibility, then labels it for automatic acceptance,
manual review, or rejection. Merging adds evidence to the live community view; it does
not rewrite an immutable release or automatically establish reproduction.

During the final activation checkpoint, the same path remains fail-closed for
public evidence. The quickstart clearly identifies the required Official App
release; Developer and Certification builds cannot submit ranking evidence.

Other useful contributions include focused Swift integration recipes,
documentation corrections, validators, and clearly scoped Build Research
proposals. Start with [CONTRIBUTING.md](CONTRIBUTING.md).

## How the live ranking works

- One GitHub account counts once per exact comparison cell.
- The same account may contribute to any number of different cells.
- Two independent contributors mark a cell as reproduced.
- Three or more contributors enable contributor-weighted aggregation.
- Raw failures, OOMs, cancellations, and ineligible attempts remain evidence.
- iOS patch versions may share a display family; exact OS builds remain in the
  evidence identity.

There is no global score. Responsiveness and sustained generation remain
separate workload rankings. Read [Power method](docs/power.md) for the public
explanation and the frozen release assets for normative details.

## Repository map

| Path | Purpose |
| --- | --- |
| `benchmarks/` | Normative suite and release specifications |
| `apps/ios/` + `apps/PowerRunnerKit/` | Power App shell and certified runner components |
| `schemas/` | Machine-readable contracts |
| `submissions/` | Contributor-owned evidence packages |
| `results/` | Immutable raw evidence and generated views |
| `site/` + `index.html` | Public leaderboard |
| `examples/` | Small integration recipes |
| `docs/` | Current guides plus retained decision records |
| `scripts/` | Validators, generators, and historical release tooling |

The project deliberately keeps rigorous evidence even when it is not part of
the public reading path. [Project structure](docs/project-structure.md)
defines what may grow, what must remain immutable, and how new work avoids
creating another parallel public workflow.

## Local checks

```bash
python3 -m unittest discover -s tests -v
python3 scripts/power preview
python3 -m http.server 4173
```

Then open `http://localhost:4173/`.

## Principles

- Never invent, simulate, or silently rewrite benchmark evidence.
- Prefer fewer stable workloads over broad but ambiguous coverage.
- Keep the contributor path short and the evidence path complete.
- Preserve pinned release assets and historical source identities.
- Label unknowns as unknown instead of turning them into scores.

See [documentation index](docs/README.md), [project vision](docs/project-vision.md),
[product architecture](docs/product-architecture.md), and the proposed
[repository architecture blueprint](docs/repository-architecture.md).

## License

- Code and examples: [MIT](LICENSE)
- Benchmark specifications, datasets, results, and documentation:
  [CC BY 4.0](LICENSE-DATA)
