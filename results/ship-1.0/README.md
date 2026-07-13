# Ship Deployment Profiles 1.0 RC1

This release candidate is generated from the published, immutable Power 1.0 evidence matrix. It adds deployment guidance and a tested-runtime integration recipe without changing Power results, protocols, schemas, workloads, rankings, or the benchmark App.

Ship is profile-based and has no aggregate score. `Unknown` is preserved wherever the current evidence cannot support a claim.

Regenerate and verify from the repository root:

```bash
python3 scripts/generate_ship_profiles.py
shasum -a 256 -c results/ship-1.0/SHA256SUMS
```
