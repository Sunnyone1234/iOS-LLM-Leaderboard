# Schemas

Machine-readable schemas are introduced incrementally during the Framework v2
transition.

- `suite-b-workload-0.1.schema.json` defines draft Suite B workload manifests.
- `suite-b-pilot-bundle-0.3.schema.json` documents the current non-official
  iPhone pilot export before explicit v2 identities and power evidence.
- `suite-b-pilot-bundle-0.4.schema.json` documents the previous non-official
  export with workload mapping, measurement boundaries, generation settings,
  dependency identity, and power evidence.
- `suite-b-pilot-bundle-0.5.schema.json` adds revision-specific model cache,
  download, load, restart, and measurement-eligibility evidence.
- `suite-b-ux-bundle-0.1.schema.json` defines the non-official B-UX-001 pilot
  export with Pipeline TTFT, User-visible TTFT, request completion, visible
  output, and raw token-event evidence.
- `suite-b-input-sweep-bundle-0.1.schema.json` defines the non-official
  B-PIPE-002 four-point input-length sweep and its per-attempt evidence.
- `suite-b-context-assistance-bundle-0.1.schema.json` defines the non-official
  B-UX-002 token-exact context variants, retained timing evidence, visible
  answers, and deterministic per-attempt answer-contract evidence.

The pilot schema is transitional. An official Suite B v2 result schema will be
frozen only after timing boundaries, generation configuration, environment
evidence, and workload identities are emitted and validated by the app.
