# Power Benchmark 1.1 Final Review Candidate

Generated from six hash-bound physical-device results and deterministic final validation reports.
Raw evidence remains labeled `suite-b-power@1.1.0-rc.1`; no result bytes were rewritten.

> This is review material, not an official ranking. Public ranking remains disabled until explicit maintainer approval.

## Measured responsiveness

| Review order | Model | Quant | Proxy TTFT | Pipeline TTFT | Prefill | Peak memory | End thermal | Recommendation | Evidence |
| ---: | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| 1 | Qwen3 0.6B | 4-bit | 183.09 ms | 181.72 ms | 385.40 tok/s | 473 MiB | nominal | not verified | [21B5F28F](../../results/suite-b-power-1.1.0-rc.1/device-verification/raw/2026-07-15T15-25-48Z_b-ux-001-short-interaction_mlx-community-qwen3-0.6b-4bit_iphone15-3_21b5f28f.json) |
| 2 | Qwen3 1.7B | 4-bit | 487.73 ms | 484.78 ms | 144.47 tok/s | 1098 MiB | nominal | eligible | [169EBB65](../../results/suite-b-power-1.1.0-rc.1/device-verification/raw/2026-07-15T15-41-21Z_b-ux-001-short-interaction_mlx-community-qwen3-1.7b-4bit_iphone15-3_169ebb65.json) |
| 3 | Qwen3 4B | 3-bit | 1137.58 ms | 1133.06 ms | 61.79 tok/s | 1883 MiB | nominal | eligible | [E357D4E7](../../results/suite-b-power-1.1.0-rc.1/device-verification/raw/2026-07-15T15-48-56Z_b-ux-001-short-interaction_mlx-community-qwen3-4b-3bit_iphone15-3_e357d4e7.json) |

## Measured sustained generation

| Review order | Model | Quant | Decode | Pipeline TTFT | Prefill | Peak memory | End thermal | Recommendation | Evidence |
| ---: | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| 1 | Qwen3 0.6B | 4-bit | 96.84 tok/s | 454.12 ms | 517.69 tok/s | 803 MiB | nominal | eligible | [8C10D75C](../../results/suite-b-power-1.1.0-rc.1/device-verification/raw/2026-07-15T15-30-51Z_b-pipe-001-sustained-generation_mlx-community-qwen3-0.6b-4bit_iphone15-3_8c10d75c.json) |
| 2 | Qwen3 1.7B | 4-bit | 40.97 tok/s | 1239.75 ms | 189.59 tok/s | 1475 MiB | serious | eligible | [4784FF6E](../../results/suite-b-power-1.1.0-rc.1/device-verification/raw/2026-07-15T15-44-46Z_b-pipe-001-sustained-generation_mlx-community-qwen3-1.7b-4bit_iphone15-3_4784ff6e.json) |
| 3 | Qwen3 4B | 3-bit | 9.82 tok/s | 4889.43 ms | 48.06 tok/s | 2373 MiB | serious | eligible | [167679D8](../../results/suite-b-power-1.1.0-rc.1/device-verification/raw/2026-07-15T15-56-24Z_b-pipe-001-sustained-generation_mlx-community-qwen3-4b-3bit_iphone15-3_167679d8.json) |

The measured-performance and recommendation views are separate.
No combined Power score or Ship score is defined.
