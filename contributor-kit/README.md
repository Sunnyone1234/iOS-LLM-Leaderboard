# Contributor Kit

This kit explains how community members can contribute to iOS-LLM-Leaderboard.

Power 1.0 public intake is open for unmodified physical-iPhone exports from two
exact App sources:

- use the [Power 1.0 contributor quickstart](power-1.0-quickstart.md) and App
  0.8.0 build 10 to reproduce an existing Qwen comparison cell;
- use [Test a Recommended Power Model](test-recommended-model.md) and App 0.9.0
  build 11 to create evidence for one of four pinned, untested candidates.

Both paths cover the exact App checkout, physical-device run, immutable
package, validation, and contributor-owned pull request. The candidates are
not ranking rows until genuine evidence is accepted.

Framework v1 retains a separate historical manual workflow. App 0.4 can
generate a reviewed offline Draft submission containing the exact unified
result bytes and integrity digest. It does not make a submission official or
verified and does not upload to GitHub.

You can contribute:

- benchmark results
- device benchmark results
- new benchmark tasks
- example integrations
- methodology improvements

Before submitting results, make sure placeholder data is removed and all metadata needed for reproduction is included.

See [Community Contribution Model](../docs/community-contribution-model.md) for
the planned low-friction app submission and evidence-level process.

Benchmark tasks must follow [Benchmark Task Specification](../methodology/benchmark-specification.md).

Benchmark results must follow [Benchmark Result Specification](../methodology/benchmark-result-specification.md).

Useful files:

- [Contribute a Power 1.0 result](power-1.0-quickstart.md)
- [Test a recommended Power model](test-recommended-model.md)
- [Recommended model catalog](../models/power-test-catalog.json)
- [Live Power coverage gaps](../results/suite-b-power-community/COVERAGE.md)
- [Submit a model result](submit-model-result.md)
- [Submit a device result](submit-device-result.md)
- [Model result template](../templates/model-result-template.json)
- [Device result template](../templates/device-result-template.json)

Validate an App-generated Suite B package with:

```bash
python3 scripts/validate_suite_b_submission.py path/to/submission.json
```
