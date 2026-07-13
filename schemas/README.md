# Schemas

Machine-readable schemas are introduced incrementally during the Framework v2
transition.

- `suite-b-plan-registry-0.1.schema.json` defines the common typed execution
  registry for the four current Suite B workloads.
- `suite-b-plan-registry-0.2.schema.json` adds the unplugged power source and
  minimum 50% starting battery admission rules.
- `suite-b-workload-0.1.schema.json` defines draft Suite B workload manifests.
- `suite-b-pilot-bundle-0.3.schema.json` documents the current non-official
  iPhone pilot export before explicit v2 identities and power evidence.
- `suite-b-pilot-bundle-0.4.schema.json` documents the previous non-official
  export with workload mapping, measurement boundaries, generation settings,
  dependency identity, and power evidence.
- `suite-b-pilot-bundle-0.5.schema.json` adds revision-specific model cache,
  download, load, restart, and measurement-eligibility evidence.
- `suite-b-pilot-bundle-0.6.schema.json` freezes the current sustained-generation
  runner under the B-PIPE-001 workload and plan identities while retaining
  validator support for older Pilot bundles.
- `suite-b-ux-bundle-0.1.schema.json` defines the non-official B-UX-001 pilot
  export with Pipeline TTFT, User-visible TTFT, request completion, visible
  output, and raw token-event evidence.
- `suite-b-input-sweep-bundle-0.1.schema.json` defines the non-official
  B-PIPE-002 four-point input-length sweep and its per-attempt evidence.
- `suite-b-context-assistance-bundle-0.1.schema.json` defines the non-official
  B-UX-002 token-exact context variants, retained timing evidence, visible
  answers, and deterministic per-attempt answer-contract evidence.
- `suite-b-result-bundle-0.1.schema.json` is the unified envelope emitted by
  all four current workloads. Single-run workloads contain one `sessions`
  entry; point-series workloads contain one entry per token-exact point.
- `suite-b-result-bundle-0.2.schema.json` records and enforces the versioned
  power admission requirements while keeping 0.1 evidence valid.
- `suite-b-result-bundle-0.3.schema.json` documents the historical App 0.6.0
  Pilot envelope with the additive fixed-profile model, source, license, and
  compatibility metadata. It remains non-official and is not the Power
  Benchmark 1.0 result schema.
- `suite-b-result-bundle-0.4.schema.json` defines the non-official Foundation
  App 0.7.0 envelope. It adds a bounded, versioned cumulative-decoding trace
  that permits independent recalculation of the First-renderable proxy TTFT.
  It remains a development candidate and is not the frozen Power Benchmark
  1.0 result schema.
- `suite-b-community-submission-0.1.schema.json` wraps exact result bytes,
  integrity evidence, contributor declarations, and a Draft trust request for
  offline repository submission.
- `suite-b-intake-report-0.1.schema.json` records CI structural findings without
  changing trust or leaderboard state.
- `suite-b-community-review-0.1.schema.json` records an explicit maintainer
  promotion from Draft to Community Submitted only.

The earlier workload-specific schemas remain supported for existing evidence.
An official Power Benchmark 1.0 result schema will be frozen only after
immutable benchmark-release identity, normative edge cases, independently
recalculable official metrics, migration rules, and App/validator compatibility
are frozen together.
