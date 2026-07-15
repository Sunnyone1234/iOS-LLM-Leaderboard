# Scripts

## Public entry point

Use one command for current Power contribution work:

```bash
python3 scripts/power.py submit RESULT.json --github HANDLE --accept-declarations
python3 scripts/power.py validate submissions/suite-b/power-1.1.0/draft/ID
python3 scripts/power.py preview
```

## Current implementation tools

- `validate_suite_b_power_1_1_submission.py` validates the current two-file
  contribution package.
- `validate_suite_b_power_1_1_final_result.py` derives final Power 1.1
  eligibility from adopted RC1 evidence.
- `generate_power_community_ranking.py` builds the live evidence dataset and
  Markdown views.
- `generate_ship_profiles.py` builds Ship evidence profiles.

## Versioned and historical tools

Other scripts preserve release generation, pilot processing, Framework v1,
Power 1.0, RC validation, review records, and audit workflows. Some are pinned
by release manifests and must not be modified. They are implementation and
audit assets, not additional contributor entry points.

Before changing a release-specific script, check whether a manifest under
`benchmarks/**/releases/` pins its SHA-256. Create a new versioned asset instead
of altering a pinned file.
