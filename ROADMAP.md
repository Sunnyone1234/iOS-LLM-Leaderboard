# Roadmap

The project grows in evidence depth, not in the number of benchmark ideas.

## Now: Power 1.1 community coverage

- keep the two frozen workloads stable;
- make the physical-device contribution path reliable and short;
- add independent devices, models, and contributors;
- preserve exact configuration identity and raw failure evidence;
- improve model coverage without weakening artifact compatibility checks;
- keep the live ranking understandable and reproducible.

Power 1.1 success is broader credible coverage under the existing contract,
not another protocol revision.

## Next: complete Ship evidence

- link deployment profiles to current Power evidence;
- expand focused Swift integration recipes;
- record format, download, offline, streaming, cancellation, license, and
  distribution facts with explicit sources;
- keep unsupported or unverified claims as `Unknown`;
- avoid a global Ship score.

Ship reuses Power measurements. It does not redefine latency, memory, or
thermal metrics.

## Later: Power quality and Ship integration evidence

Suite D may provide a future Power quality gate and Suite E may provide future
Ship integration evidence. Neither is active until a concrete developer need,
minimal contract, validation path, and maintenance owner are approved.

## Phase 2 research: Build

Suite A and Suite C remain visible as Build Research. Build may eventually
evaluate complete iOS software delivery:

```text
product requirement → plan → implementation → compilation → tests
→ simulator validation → accessibility → privacy → App Store readiness
```

Do not implement Build protocols, runners, or rankings during Phase 1. Do not
reduce Build to isolated Swift snippets, API examples, or code completion.

## Ongoing maintenance

- one current public guide and one public Power command;
- one GitHub Pages deploy workflow;
- immutable pinned release assets;
- generated views checked against source evidence;
- A–E suite navigation retained with accurate product roles;
- historical records kept for auditability but de-indexed from onboarding;
- no new top-level directory or benchmark category without a documented owner
  and lifecycle.

See [project structure and growth policy](docs/project-structure.md).
