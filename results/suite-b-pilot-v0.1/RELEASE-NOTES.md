# Power + Ship Pilot v0.1 Release Notes

## Status

This package is the release candidate for the non-official Power + Ship Pilot
v0.1. It is not Suite B 1.0, does not activate an official leaderboard, and
does not establish general device-support or deployment-readiness claims.

No tag or GitHub Release has been created. Publication remains subject to
maintainer approval.

## Scope

The release candidate contains six genuine, unmodified Benchmark App 0.6.0
build 8 exports:

```text
3 exact model artifacts
× 1 physical iPhone
× 2 frozen Pilot workloads
= 6 Pilot results
```

The reference device is an iPhone 14 Pro Max (`iPhone15,3`) running iOS 26.5
build 23F77. All runs use MLX Swift LM 3.31.4, MLX Swift 0.31.6, the MLX/Metal
backend, Release configuration, no attached debugger, Low Power Mode off, and
the documented battery and thermal admission rules.

The exact model artifacts are:

- `mlx-community/Qwen3-0.6B-4bit@73e3e38d981303bc594367cd910ea6eb48349da8`;
- `mlx-community/Qwen3-1.7B-4bit@3b1b1768f8f8cf8351c712464f906e86c2b8269e`;
- `mlx-community/Qwen3-4B-3bit@c4e8054c71facfa84f781cdb7c1ffab3f09f89bf`.

The only included workload identities are:

- `b-ux-001-short-interaction@0.2.0-pilot`;
- `b-pipe-001-sustained-generation@0.2.0-pilot`.

## Pipeline outcome

The frozen Pilot generator reports:

- 6 input files;
- 6 normalized results;
- 6 eligible Pilot results;
- 0 ineligible results; and
- 0 rejected files.

Every result retains one warm-up and five completed measured attempts. No
failed or not-run attempt is hidden. The medium and larger B-PIPE-001 runs end
in the system-reported `serious` thermal state; those observations remain in
the evidence and were not rerun or filtered.

## Headline evidence

| Configuration | First-renderable proxy TTFT | B-UX peak footprint | B-PIPE decode | B-PIPE peak footprint | B-PIPE final thermal |
| --- | ---: | ---: | ---: | ---: | --- |
| Qwen3 0.6B, 4-bit | 182.35 ms | 804.14 MiB | 98.16 tok/s | 737.13 MiB | nominal |
| Qwen3 1.7B, 4-bit | 496.45 ms | 1107.08 MiB | 39.89 tok/s | 1389.31 MiB | serious |
| Qwen3 4B, 3-bit | 1142.77 ms | 1878.92 MiB | 10.83 tok/s | 2288.47 MiB | serious |

These rows are workload-specific configuration evidence, not a combined score.
See `LEADERBOARD.md` for the complete identities and additional measured facts.

## Ship evidence

`SHIP-EVIDENCE.md` reuses the same eligible Power results. It records pinned
model sources, repository sizes, license metadata without a legal conclusion,
local preparation and inference evidence, streaming token events, measured peak
process footprint, and the physical device actually tested. It does not create
a Ship score or infer App Store approval.

## Integrity and privacy review

- Each file under `raw/` is byte-identical to the supplied App export.
- `SHA256SUMS` covers all six raw files and the four generated release outputs.
- The raw bundles contain no contributor name, email address, account name,
  device serial number, Vendor ID, local filesystem path, credential, API key,
  or access token.
- Public device data is limited to the model-level Apple machine identifier,
  OS version/build, battery and thermal conditions, and benchmark runtime facts.
- Result UUIDs, timestamps, token IDs/timing, and fixed-workload model output
  are intentionally retained as reproducibility evidence.

## Validation

- `python3 -m unittest discover -s tests`: 81 tests passed.
- `python3 scripts/generate_suite_b_pilot.py`: 6 normalized, 6 eligible,
  0 rejected.
- BenchmarkApp Xcode test suite: 29 tests passed.
- JSON parsing, release-count assertions, checksum verification, and
  `git diff --check` passed.

## Known limitations

- First-renderable proxy TTFT is measured at the adapter/renderable-content
  boundary. It is not screen-render latency and is not yet independently
  reconstructable from the retained token-event evidence.
- B-UX-001 does not contain an automated response-quality decision.
- Five measured attempts are not a general thermal-stability claim.
- Inference-time network state is not recorded, so offline execution remains
  `Unknown` in Ship evidence.
- The tested device is `iPhone15,3`; a minimum supported device is not
  established.
- App Store and distribution readiness are not evaluated.
- `appSourceCommit` was not injected into the physical builds. The results
  therefore retain the non-blocking `runner_source_identity_missing` warning.
- The Pilot covers one reference runtime and is non-official evidence only.

## Reproduction

From the repository root:

```bash
python3 scripts/generate_suite_b_pilot.py
shasum -a 256 -c results/suite-b-pilot-v0.1/SHA256SUMS
```

The first command regenerates the normalized dataset, leaderboard, pipeline
report, and Ship evidence from the six raw App exports. The second verifies the
release evidence and generated outputs.
