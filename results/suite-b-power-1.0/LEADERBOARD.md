# Power Benchmark 1.0 Final Review Candidate

This leaderboard is generated only from the six immutable F5 physical-device results.
The source JSON remains `suite-b-power@1.0.0-rc.1`; Power 1.0 adopts it by hash because the App and protocol semantics are unchanged.

> Final publication and ranking are not active until the maintainer approves the complete package.

## Responsiveness

| Rank | Model | Quant | Proxy TTFT | Pipeline TTFT | Prefill | Peak memory | Device | Evidence |
| ---: | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| 1 | Qwen3 1.7B | 4-bit | 494.40 ms | 492.03 ms | 142.32 tok/s | 1791 MiB | iPhone15,3 | [99A70D26](../../results/suite-b-power-1.0.0-rc.1/f5-device-verification/raw/2026-07-13T12-20-48Z_b-ux-001-short-interaction_mlx-community-qwen3-1.7b-4bit_iphone15-3_99a70d26.json) |
| 2 | Qwen3 4B | 3-bit | 1132.81 ms | 1127.86 ms | 62.07 tok/s | 2370 MiB | iPhone15,3 | [ECB64A54](../../results/suite-b-power-1.0.0-rc.1/f5-device-verification/raw/2026-07-13T12-32-28Z_b-ux-001-short-interaction_mlx-community-qwen3-4b-3bit_iphone15-3_ecb64a54.json) |

## Sustained generation

| Rank | Model | Quant | Decode | Pipeline TTFT | Prefill | Peak memory | Device | Evidence |
| ---: | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| 1 | Qwen3 0.6B | 4-bit | 97.90 tok/s | 463.98 ms | 506.69 tok/s | 799 MiB | iPhone15,3 | [1B0A18F0](../../results/suite-b-power-1.0.0-rc.1/f5-device-verification/raw/2026-07-13T12-11-49Z_b-pipe-001-sustained-generation_mlx-community-qwen3-0.6b-4bit_iphone15-3_1b0a18f0.json) |
| 2 | Qwen3 1.7B | 4-bit | 29.71 tok/s | 1416.04 ms | 165.98 tok/s | 1756 MiB | iPhone15,3 | [F64AB629](../../results/suite-b-power-1.0.0-rc.1/f5-device-verification/raw/2026-07-13T12-16-23Z_b-pipe-001-sustained-generation_mlx-community-qwen3-1.7b-4bit_iphone15-3_f64ab629.json) |
| 3 | Qwen3 4B | 3-bit | 10.23 tok/s | 4858.10 ms | 48.37 tok/s | 2277 MiB | iPhone15,3 | [C4F133ED](../../results/suite-b-power-1.0.0-rc.1/f5-device-verification/raw/2026-07-13T12-27-41Z_b-pipe-001-sustained-generation_mlx-community-qwen3-4b-3bit_iphone15-3_c4f133ed.json) |

## Retained but not ranked

| Model | Workload | Reason | Raw evidence |
| --- | --- | --- | --- |
| Qwen3 0.6B | b-ux-001-short-interaction | insufficient_metric_eligible_attempts | [2C2F23B4](../../results/suite-b-power-1.0.0-rc.1/f5-device-verification/raw/2026-07-13T12-10-55Z_b-ux-001-short-interaction_mlx-community-qwen3-0.6b-4bit_iphone15-3_2c2f23b4.json) |

No Power or Ship aggregate score is defined.
