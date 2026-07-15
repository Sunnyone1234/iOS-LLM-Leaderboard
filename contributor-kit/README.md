# Contributor Kit

There is one current benchmark-result path:

## Contribute Power 1.1 evidence

Use the [Power 1.1 quickstart](power-1.1-quickstart.md) to:

1. build the exact official Benchmark App source;
2. run one model and one workload on a physical iPhone;
3. export the untouched result JSON;
4. create and validate a two-file package; and
5. open a pull request from your own GitHub account.

```bash
python3 scripts/power.py submit /path/to/result.json \
  --github YOUR_GITHUB_HANDLE \
  --accept-declarations
```

See [live coverage gaps](../results/suite-b-power-community/COVERAGE.md) and the
[App-ready model catalog](../models/power-test-catalog.json) when choosing what
to test.

## Other contributions

- Read [CONTRIBUTING.md](../CONTRIBUTING.md) for focused integration,
  documentation, validation, and Build Research work.
- Benchmark methodology lives in [docs/power.md](../docs/power.md).
- Stable task and result rules remain in [methodology/](../methodology/).

## Historical paths

The following guides remain available only to reproduce or audit their frozen
contracts. Do not use them for a new Power 1.1 submission:

- [Power 1.0 quickstart](power-1.0-quickstart.md)
- [Historical recommended-model workflow](test-recommended-model.md)
