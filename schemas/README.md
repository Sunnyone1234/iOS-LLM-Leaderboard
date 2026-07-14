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
- `suite-b-power-result-1.0.0-rc.1.schema.json` is the frozen F3
  release-candidate result contract for exactly B-UX-001 and B-PIPE-001. It
  retains the raw timing, token, memory, thermal, outcome, and response evidence
  required by the Power 1.0 protocol. App 0.8.0 implements this contract, but
  the contract alone does not authorize official results.
- `suite-b-power-result-1.1.0-draft.1.schema.json` versions that same submitted
  field shape for the Power 1.1 draft. It adds no contributor field, marks the
  existing App `responseConformance` observation as advisory, and requires the
  future semantic validator to keep technically derivable metrics independent
  of that observation.
- `suite-b-power-validation-report-1.0.0-rc.1.schema.json` keeps structural
  validity, protocol conformance, per-metric eligibility, evidence review, and
  ranking eligibility as separate validator decisions.
- `suite-b-power-validation-report-1.1.0-draft.1.schema.json` is the minimal
  internal Power 1.1 report generated from one submitted result. It binds the
  result SHA-256, records validator and ranking-policy versions, separates
  metric and recommendation eligibility, and represents applicable behavior
  assessment as `verified`, `not_verified`, or `contradicted`. Contributors do
  not create or upload this report.
- `suite-b-community-submission-0.1.schema.json` wraps exact result bytes,
  integrity evidence, contributor declarations, and a Draft trust request for
  offline repository submission.
- `suite-b-intake-report-0.1.schema.json` records CI structural findings without
  changing trust or leaderboard state.
- `suite-b-community-review-0.1.schema.json` records an explicit maintainer
  promotion from Draft to Community Submitted only.
- `suite-b-power-submission-1.0.0-rc.1.schema.json` defines the strict
  two-file Power RC1 package manifest, contributor declarations, conflict
  disclosure, immutable result digest, and exact public identity references.
- `suite-b-power-review-1.0.0-rc.1.schema.json` defines append-only,
  hash-bound evidence transitions while forcing release and ranking
  authorization to remain false during RC1.

The earlier workload-specific and Community Submission 0.1 schemas remain
supported for historical evidence but are not Power RC1 submission contracts.
The F3 schemas and validator are pinned by the non-official
`suite-b-power@1.0.0-rc.1` release manifest. App 0.8.0 and the completed F5
device matrix provide the matching execution evidence; official publication
still requires explicit maintainer approval after the F6 review.
