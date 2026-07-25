# Contributor Kit

There is one current benchmark-result path:

## Contribute Power evidence

Use the [current Power quickstart](power.md) to:

1. build the exact official Benchmark App source;
2. run one model and one workload on a physical iPhone;
3. export the untouched result JSON;
4. create and validate a two-file package; and
5. open a pull request from your own GitHub account.

```bash
python3 scripts/power submit /path/to/result.json \
  --github YOUR_GITHUB_HANDLE \
  --accept-declarations
```

Power 2 public intake is open for results produced by the supported Official
source configuration pinned by `products/power/current.json`. The embedded
release identity is a self-declaration by a locally signed build. One eligible
contributor is Accepted; independent matching evidence is required for
Reproduced. Developer and Certification builds remain non-publishable.

## Other contributions

- Read [CONTRIBUTING.md](../CONTRIBUTING.md) for focused integration,
  documentation, validation, and Build Research work.
- Benchmark methodology lives in [docs/power.md](../docs/power.md).
- Stable task and result rules remain in [methodology/](../methodology/).

## Historical paths

The following guides remain available only to reproduce or audit their frozen
contracts. Do not use them for a new submission:

- [Power 1.1 quickstart](power-1.1-quickstart.md)
- [Power 1.0 quickstart](power-1.0-quickstart.md)
- [Historical recommended-model workflow](test-recommended-model.md)
