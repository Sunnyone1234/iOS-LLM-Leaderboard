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

The pilot schema is transitional. An official Suite B v2 result schema will be
frozen only after timing boundaries, generation configuration, environment
evidence, and workload identities are emitted and validated by the app.
