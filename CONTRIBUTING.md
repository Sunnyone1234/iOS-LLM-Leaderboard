# Contributing

Thank you for helping make on-device AI evaluation more useful and credible.
Choose the smallest contribution path that fits your change.

## 1. Submit a Power 1.1 result

Follow the [Power 1.1 quickstart](contributor-kit/power-1.1-quickstart.md). The
public flow is:

```bash
python3 scripts/power.py submit /path/to/result.json \
  --github YOUR_GITHUB_HANDLE \
  --accept-declarations
```

This creates exactly:

```text
submissions/suite-b/power-1.1.0/draft/<submission-id>/
├── submission.json
└── result.json
```

Do not edit `result.json`. Review both files, commit only that package, and
open the pull request from the declared GitHub account. CI checks the package,
the frozen Power contract, and the live-ranking preview.

The declarations confirm that you ran the benchmark on a physical device, may
submit the evidence, reviewed public metadata, left the raw result untouched,
removed personal data, accept CC BY 4.0 for the evidence, and understand that
submission does not guarantee a rank or trust-level change.

If you deliberately cooled or heated the device, or do not know whether the
run was assisted, disclose it with `--thermal-assistance`. The package remains
reviewable evidence but does not enter the ordinary live ranking.

## 2. Improve integration or documentation

Good small contributions include:

- a focused Swift integration recipe;
- a correction to current public documentation;
- a reproducibility or validation fix;
- clearer model, runtime, license, or deployment evidence.

Keep examples copyable and narrow. Do not add a full starter application when
a short recipe is enough.

## 3. Propose benchmark or Build Research work

Suite A and Suite C remain visible as Build Research. Build is not active in
Phase 1 and must not be expanded into isolated Swift snippets, API examples,
or code-completion tasks. A future proposal should evaluate complete software
delivery and remain a proposal until separately approved.

New Suite B ideas should not create one task per metric. Power workloads
collect compatible TTFT, prefill, decode, memory, thermal, and failure evidence
under one versioned execution contract.

Before proposing a new benchmark category, explain why an existing suite,
workload, metric, or Ship profile cannot represent it.

## Pull-request rules

- Never invent measurements, placeholder ranks, or device evidence.
- Do not modify pinned release assets or historical raw result bytes.
- Preserve stable task and workload IDs.
- Keep generated files synchronized with their source data.
- Update the current public guide instead of adding a parallel guide.
- Add a new top-level directory only when
  [project-structure.md](docs/project-structure.md) permits it.
- Keep MIT code/examples separate from CC BY 4.0 benchmark data and docs.

Run before opening a pull request:

```bash
python3 -m unittest discover -s tests -v
git diff --check
```

Power result contributors can also run:

```bash
python3 scripts/power.py validate \
  submissions/suite-b/power-1.1.0/draft/<submission-id>
python3 scripts/power.py preview --output /tmp/power-preview
```

Historical Power 1.0, Pilot, and Framework v1 submission instructions remain
in their versioned paths for auditability. They are not the current public
intake route.

## License

By opening a pull request, you agree that your contribution follows the
repository license boundary: MIT for code and examples, CC BY 4.0 for
benchmark specifications, data, results, and documentation.
