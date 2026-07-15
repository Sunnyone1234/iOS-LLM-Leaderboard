# Power Benchmark 1.1

This directory is generated from immutable Power 1.1 RC1 evidence and hash-bound final validation reports.

This is a final review candidate and does not activate public ranking.

Regenerate and verify from the repository root:

```bash
python3 scripts/generate_suite_b_power_1_1_release.py
shasum -a 256 -c results/suite-b-power-1.1/SHA256SUMS
```
