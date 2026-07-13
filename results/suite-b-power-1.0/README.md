# Power Benchmark 1.0

This directory is generated from immutable F5 RC1 evidence through the hash-bound no-rerun adoption manifest.

These files form the published Power Benchmark 1.0 package and activate the workload-specific official ranking.

Regenerate and verify from the repository root:

```bash
python3 scripts/generate_suite_b_power_release.py
shasum -a 256 -c results/suite-b-power-1.0/SHA256SUMS
```
