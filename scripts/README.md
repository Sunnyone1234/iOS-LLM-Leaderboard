# Scripts

## Public entry point

The retained public command is:

```bash
python3 scripts/power.py submit RESULT.json --github HANDLE --accept-declarations
python3 scripts/power.py validate submissions/suite-b/power-1.1.0/draft/ID
python3 scripts/power.py preview
```

This command is SHA-256-pinned by the Power 1.1.1 release and therefore keeps
that release's App 0.13.0/App 0.16.0 compatibility boundary. App 0.18.0 direct
submission is handled by the configured App and the trusted Power 1.1.4 CI
adapters; do not modify `power.py` or advertise a second contributor CLI to
work around the frozen boundary.

## Current implementation tools

- `validate_suite_b_power_1_1_submission.py` validates the current two-file
  contribution package.
- `validate_suite_b_power_1_1_compatible_result.py` applies the versioned exact
  runner/runtime allowlist before reusing the frozen Power 1.1 validator.
- `validate_suite_b_power_1_1_final_result.py` derives final Power 1.1
  eligibility from adopted RC1 evidence and remains pinned and immutable.
- `generate_power_community_ranking.py` builds the live evidence dataset and
  Markdown views.
- `generate_ship_profiles.py` builds Ship evidence profiles.

Power 1.1.2 through 1.1.4 add isolated, version-suffixed adapters for trusted
validation, triage, and ranking. They load the frozen implementations without
changing their module globals or pinned bytes. They are release and CI assets,
not a parallel public contributor flow.

## Versioned and historical tools

Other scripts preserve release generation, pilot processing, Framework v1,
Power 1.0, RC validation, review records, and audit workflows. Some are pinned
by release manifests and must not be modified. They are implementation and
audit assets, not additional contributor entry points.

Before changing a release-specific script, check whether a manifest under
`benchmarks/**/releases/` pins its SHA-256. Create a new versioned asset instead
of altering a pinned file.
