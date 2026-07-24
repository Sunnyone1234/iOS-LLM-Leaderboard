# AGENTS.md

Repository-wide conventions for AI coding agents working on
iOS-LLM-Leaderboard.

## Product scope

The long-term architecture is **Build, Power, Ship**.

- Phase 1 has two separate product tracks: **Power** and **Ship**.
- A Benchmark App run produces Power evidence only.
- Ship may cite accepted Power measurements, but it is a separate downstream
  deployment-guidance product and is not contained in Power.
- Phase 2 Research Track: **Build**.
- Do not implement Build protocols, runners, schemas, or rankings unless a
  later task explicitly approves them.

The project is a benchmark and documentation project, not another inference
framework. Implement infrastructure only when it directly supports benchmark
creation, execution, validation, visualization, or community contribution.

Current public status and navigation are defined by:

- `README.md`
- `docs/README.md`
- `docs/project-vision.md`
- `docs/product-architecture.md`
- `docs/project-structure.md`
- `docs/repository-architecture.md` for the implemented target architecture,
  current architecture and activation state
- `docs/power.md`

The Power 2 migration is a clean break. Do not add active Power 1.1 readers,
schema adapters, policy adapters, dual-version dispatch, or old-result
promotion. Preserve Power 1.1 pinned assets and raw evidence only as a
read-only historical plane.

## Non-negotiable evidence rules

- Never invent benchmark results, measurements, ranks, or device evidence.
- Never simulate device performance and present it as real.
- Never present placeholder or demo data as official evidence.
- Never silently rewrite raw result bytes or a released source identity.
- Preserve failed, cancelled, OOM, and not-run attempts.
- Keep enough exact model, runtime, device, OS, configuration, workload, and
  runner metadata to interpret and reproduce a result.

If real data is unavailable, label examples clearly as placeholder or demo and
exclude them from official leaderboard logic.

## Current Power rules

Power 2 is the active clean-break release. Public intake uses the exact stack
and supported Official App release pinned by `products/power/current.json`.
Developer and Certification builds remain non-publishable. Power 1.0 and 1.1
are historical audit assets and must not be referenced by an active App,
pointer, validator, workflow, package, or ranking.

For current Power work:

- use versioned workloads and measurement modes;
- collect TTFT, prefill, decode, memory, and thermal as metrics from compatible
  attempts rather than creating one task per metric;
- label user-experience workloads and pipeline profiles explicitly;
- never relabel Pipeline TTFT as user-visible TTFT;
- preserve stable workload IDs;
- keep metric eligibility separate from structural validity, protocol
  conformance, behavior verification, and recommendation eligibility;
- keep exact comparison identity even when the UI groups patch releases; and
- do not add a global Power score.

The only community command is `scripts/power`. Power 2 uses the two-file
`submissions/power/text-generation-performance/2.0.0/draft/<id>/` package.
Historical Power and Framework v1 tools remain audit assets, not compatibility
or alternate public flows.

## Suite organization

Keep A–E visible and keep content in the correct namespace:

- Suite A: Swift Code Generation — Build Research.
- Suite B: On-device Performance — active Power foundation.
- Suite C: Xcode Integration — Build Research.
- Suite D: App Feature Intelligence — possible future Power quality evidence.
- Suite E: Runtime Evaluation — possible future Ship evidence.

Do not mix their task ownership. The five namespaces are not equal Phase 1
priorities and must not be combined into one aggregate score.

When editing Framework v1 tasks, follow
`methodology/benchmark-specification.md`, preserve `task_id`, and increment the
task version when prompts, expected output, rubric, or pass/fail criteria change
materially. When editing compatible result templates, follow
`methodology/benchmark-result-specification.md`.

## Pinned and historical assets

Before changing a protocol, schema, validator, generator, checksum, review, or
release file, inspect the release manifests under `benchmarks/**/releases/`.

- A SHA-256-pinned asset is immutable.
- A changed contract receives a new version and path.
- Historical files may be de-indexed from public documentation but must not be
  deleted merely to simplify navigation.
- Generated results must remain reproducible from their retained source data.

## Documentation and growth

Follow `docs/project-structure.md`.

- Keep one current public guide per subject.
- Keep one public command per product; Power uses `scripts/power`.
- Update the current guide instead of adding `new`, `latest`, `final`, or `v2`
  copies.
- Keep drafts labeled and out of homepage methodology links.
- Do not add a top-level directory without documenting owner, lifecycle,
  license, and why an existing directory is insufficient.
- Do not create duplicate CI or deploy workflows.
- Prefer focused recipes over duplicated starter apps.
- Prefer clear methodology and stable evidence over benchmark quantity.

Documentation may summarize a frozen contract, but it must link to the
normative asset and must not contradict it.

## Repository license boundary

MIT:

- code;
- `examples/`;
- scripts;
- current and future source code, including the iOS App.

CC BY 4.0:

- `benchmarks/`;
- `methodology/`;
- benchmark datasets and submissions;
- benchmark results;
- leaderboard data and documentation.

Keep this separation consistent.

## Coding guidelines

Prefer:

- the simplest maintainable solution;
- readable, incremental changes;
- deterministic generators;
- standard-library tooling when practical;
- small integration recipes;
- tests that protect public links, evidence integrity, and release identity.

Avoid:

- unnecessary abstraction or dependencies;
- premature optimization;
- parallel public workflows;
- large repository moves without explicit approval;
- infrastructure for speculative benchmark categories.

Keep documentation synchronized with behavior. Preserve backward compatibility
when practical, especially for immutable evidence and released schemas.

## Verification

Run checks proportional to the change. For repository-wide changes, run:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/power preview --output /tmp/power-preview
git diff --check
```

For iOS App changes, also resolve packages and build the relevant physical or
generic iOS Release target. Never claim a device benchmark result from a
simulator or compiler-only test.
