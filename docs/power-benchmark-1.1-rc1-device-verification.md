# Power Benchmark 1.1 RC1 Device Verification

## Required matrix

Run exactly six sessions on the existing reference iPhone (`iPhone15,3`):

| Artifact | Quantization | Short Interaction | Sustained Generation |
| --- | --- | --- | --- |
| `mlx-community/Qwen3-0.6B-4bit@73e3e38d981303bc594367cd910ea6eb48349da8` | 4-bit | required | required |
| `mlx-community/Qwen3-1.7B-4bit@3b1b1768f8f8cf8351c712464f906e86c2b8269e` | 4-bit | required | required |
| `mlx-community/Qwen3-4B-3bit@c4e8054c71facfa84f781cdb7c1ffab3f09f89bf` | 3-bit | required | required |

This is verification of the frozen contract, not an expansion of benchmark
coverage. Do not substitute another model, revision, runtime, App build, or
workload.

## Build the exact frozen App

The App must report all four exact execution identities:

- `runnerVersion`: `0.13.0`
- `appVersion`: `0.13.0`
- `appBuild`: `16`
- `appSourceCommit`: `f5b863cc0ca4d82d987cd9779f8875939d7bf90c`

Build App 0.13.0 from that exact source commit. The later manifest and release-
preparation commits intentionally do not replace the App source identity.
Use a Release build on the physical iPhone with **Debug executable** disabled.

## Session procedure

For each of the six sessions:

1. select one model and one workload only;
2. while connected, prepare the exact pinned artifact until it is cached,
   verified, and loaded;
3. if a download occurred, fully close the App and relaunch it;
4. unplug the phone, keep Low Power Mode off, confirm at least 50% battery and
   nominal thermal state, and do not attach the debugger;
5. run the benchmark once: one warm-up plus five measured attempts;
6. export the JSON without editing it; and
7. fully close and relaunch the App before changing models.

Ordinary placement, ambient temperature, and case state may be recorded as
review observations. Deliberate cooling or heating is not eligible for the
ordinary reference matrix. These observations do not alter the frozen result
schema.

## File intake

Place the six unmodified App exports in:

`results/suite-b-power-1.1.0-rc.1/device-verification/raw/`

For every raw result, generate the internal report:

```sh
python3 scripts/validate_suite_b_power_1_1_rc1_result.py \
  path/to/result.json \
  --output results/suite-b-power-1.1.0-rc.1/device-verification/validation/<same-stem>.validation.json
```

Then verify the exact result/report binding:

```sh
python3 scripts/consume_suite_b_power_1_1_rc1_report.py \
  path/to/result.json \
  path/to/report.validation.json
```

Retain every failed, cancelled, OOM, and not-run attempt in its original result.
Do not rerun merely to hide an unfavorable result. A session may be rerun only
for a documented execution failure; both the failed and replacement evidence
remain in the review record, while only the approved final session enters the
six-result release matrix.
