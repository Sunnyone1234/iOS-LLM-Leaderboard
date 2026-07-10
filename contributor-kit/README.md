# Contributor Kit

This kit explains how community members can contribute to iOS-LLM-Leaderboard.

Framework v1 retains a manual workflow. For Suite B, App 0.4 can generate a
reviewed offline Draft submission containing the exact unified result bytes and
integrity digest. It does not make a submission official or verified and does
not upload to GitHub.

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

- [Submit a model result](submit-model-result.md)
- [Submit a device result](submit-device-result.md)
- [Model result template](../templates/model-result-template.json)
- [Device result template](../templates/device-result-template.json)

Validate an App-generated Suite B package with:

```bash
python3 scripts/validate_suite_b_submission.py path/to/submission.json
```
