# Contribute a Power result

Power accepts evidence produced by an exact supported Official App release on
a physical iPhone. A source-built Developer App is useful for code and UI
work, but cannot create ranking evidence.

> **Current release:** public Power 2 intake is open. The supported Official
> App release and exact stack are pinned by
> [`products/power/current.json`](../products/power/current.json). Developer
> and Certification builds remain non-publishable.

## App flow

1. Install the current supported **Power Benchmark** Official build.
2. Open **Test**, choose one registered model and workload, then prepare the
   model.
3. Run the benchmark on a physical iPhone. Do not edit the saved result.
4. Open **Results** and select the exact completed run you want to contribute.
5. Review the public metadata, conflict disclosure, environment notes, and
   declarations.
6. Tap **Submit to GitHub**, copy the Device Flow code, authorize the requested
   GitHub account, and return to the App.
7. Open the created pull request and leave its two result files unchanged.

The App creates a new branch from the current upstream commit, writes one
two-file package, and opens a result-only pull request. It never updates the
default branch of your fork.

## Equivalent CLI flow

Export **Share Raw Power JSON** from the App, preserve the bytes, then run:

```bash
python3 scripts/power submit /path/to/result.json \
  --github YOUR_GITHUB_HANDLE \
  --accept-declarations
```

The command creates:

```text
submissions/power/text-generation-performance/2.0.0/draft/<submission-id>/
├── result.json
└── submission.json
```

Validate the exact package locally:

```bash
python3 scripts/power validate \
  submissions/power/text-generation-performance/2.0.0/draft/<submission-id>
```

Commit only that UUID-named directory and open the pull request from the same
GitHub account declared by `contributor.githubLogin`.

## What automation decides

Trusted base-repository CI, never code from the contribution branch, checks:

- the pull request changes only complete two-file Power packages;
- contributor identity and declarations;
- raw-result digest and schema;
- exact Program, Target, workload, model artifact, runtime, App release, and
  Runner certificate identities;
- physical-device and admission requirements;
- duplicate evidence;
- behavior, recommendation, and per-metric eligibility.

The result is labeled:

- `power:auto-accept` — all hard intake gates pass; required checks may merge
  it automatically;
- `power:manual-review` — evidence is structurally admissible but a stated
  review condition remains;
- `power:rejected` — a hard gate or result-only scope rule failed.

Acceptance and ranking are separate. Valid failures, cancellations, OOMs, or
metric-ineligible attempts remain evidence. One contributor creates accepted
evidence, two distinct contributors reproduce an exact comparison cell, and
three enable contributor-weighted aggregation. There is no global Power score.

## Before asking for help

- Confirm the App says **Official**, not Developer or Certification.
- Confirm you selected the intended saved result in **Results**.
- Do not reformat or resave `result.json`.
- Keep code/documentation changes in a separate pull request from evidence.
- Read the uploaded machine-readable triage report for exact reason codes.
