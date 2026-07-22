# Schemas

Schemas are versioned evidence contracts. A schema pinned by a release
manifest is immutable.

## Current Power 1.1 contracts

- `suite-b-power-result-1.1.0-rc.1.schema.json` — frozen App source export
  adopted by the final release.
- `suite-b-power-validation-report-1.1.0.schema.json` — final independent
  validation decisions.
- `suite-b-power-submission-1.1.0.schema.json` — current two-file contributor
  manifest bound to an untouched source export.
- `suite-b-power-compatible-runners-1.1.2.schema.json` — current exact
  runner/runtime compatibility-policy contract used by trusted intake.

The source result retains its RC1 schema identity because Power 1.1 adopted
the frozen execution contract instead of relabeling raw evidence. The current
submission manifest separately records final release `1.1.0`.

## Historical and compatibility contracts

The directory also retains:

- Framework v1 and unified result envelopes;
- Pilot and Foundation bundle versions;
- workload and plan registries;
- Power 1.0 result, validation, submission, and review schemas;
- Power 1.1 draft and RC validation-report schemas;
- historical community intake and review schemas.

These remain necessary to validate evidence under its original identity. They
are not additional current submission routes.

Before editing a schema, check all manifests under
`benchmarks/**/releases/`. If a manifest pins its SHA-256, create a new
versioned schema rather than changing the existing file.

Current App 0.17.0 contributors should use the configured App's direct GitHub
submission. The retained `scripts/power.py` command remains available for the
runner identities covered by its pinned Power 1.1.1 policy. Contributors
should not construct schema documents manually.
