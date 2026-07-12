# Suite B Internal Pilot v0.1 Leaderboard

Non-official Pilot evidence only. Rows compare full App-recorded configurations, and rankings are separated by workload, device/OS, plan, measurement boundary, and generation configuration.

B-UX-001's historical `medianUserVisibleTTFTMilliseconds` field is labeled First-renderable proxy TTFT; it is measured inside the adapter and is not screen-visible latency. The bundle also has no automated response-quality decision. B-PIPE-001's five measured runs are not a general thermal-stability claim.

## B-UX-001 Short Interaction

### Comparison group `05c4c08fa209`

Device: iPhone 14 Pro Max (iPhone15,3) (`iPhone15,3`), iOS 26.5 (23F77). Measurement: `b-mode-warm-resident-ux-v1` / `mlx-ux-visible-boundaries-1`.

Ranking metric: Median First-renderable proxy TTFT (ms).

| Rank | Full configuration | Primary | Other measured facts | Completion / failure evidence | Warnings | Result |
| ---: | --- | ---: | --- | --- | --- | --- |
| 1 | mlx-community/Qwen3-0.6B-4bit@73e3e38d9813; 4-bit; MLX Swift LM@3.31.4; iPhone15,3 / 26.5 (23F77); MLX Safetensors; MLX/Metal; App 0.6.0 build 8 (Not recorded); b-ux-001-validation@0.2.0-pilot / b-mode-warm-resident-ux-v1 | 182.35 | Pipeline TTFT 181.38 ms; prefill 385.99 tok/s; decode 107.52 tok/s; peak footprint 804.14 MiB; final thermal nominal | Complete: 5 completed, 0 failed, 0 not run (plus 1 retained warm-up) | runner_source_identity_missing | `ba496540-a56a-4ea2-9e63-a4f8dc0828ef` |
| 2 | mlx-community/Qwen3-1.7B-4bit@3b1b1768f8f8; 4-bit; MLX Swift LM@3.31.4; iPhone15,3 / 26.5 (23F77); MLX Safetensors; MLX/Metal; App 0.6.0 build 8 (Not recorded); b-ux-001-validation@0.2.0-pilot / b-mode-warm-resident-ux-v1 | 496.45 | Pipeline TTFT 489.08 ms; prefill 143.18 tok/s; decode 42.46 tok/s; peak footprint 1107.08 MiB; final thermal nominal | Complete: 5 completed, 0 failed, 0 not run (plus 1 retained warm-up) | runner_source_identity_missing | `897b896a-4fb2-4374-98ec-acca57e3cdc7` |
| 3 | mlx-community/Qwen3-4B-3bit@c4e8054c71fa; 3-bit; MLX Swift LM@3.31.4; iPhone15,3 / 26.5 (23F77); MLX Safetensors; MLX/Metal; App 0.6.0 build 8 (Not recorded); b-ux-001-validation@0.2.0-pilot / b-mode-warm-resident-ux-v1 | 1142.77 | Pipeline TTFT 1131.02 ms; prefill 61.90 tok/s; decode 20.92 tok/s; peak footprint 1878.92 MiB; final thermal nominal | Complete: 5 completed, 0 failed, 0 not run (plus 1 retained warm-up) | runner_source_identity_missing | `b5a84431-f2fc-4095-b743-dde5e741da5a` |

## B-PIPE-001 Sustained Generation

### Comparison group `94ea71d9ee18`

Device: iPhone 14 Pro Max (iPhone15,3) (`iPhone15,3`), iOS 26.5 (23F77). Measurement: `b-mode-sustained-no-rest-v1` / `mlx-pilot-pipeline-boundaries-1`.

Ranking metric: Median decode (tokens/s).

| Rank | Full configuration | Primary | Other measured facts | Completion / failure evidence | Warnings | Result |
| ---: | --- | ---: | --- | --- | --- | --- |
| 1 | mlx-community/Qwen3-0.6B-4bit@73e3e38d9813; 4-bit; MLX Swift LM@3.31.4; iPhone15,3 / 26.5 (23F77); MLX Safetensors; MLX/Metal; App 0.6.0 build 8 (Not recorded); b-pipe-001-validation@0.2.0-pilot / b-mode-sustained-no-rest-v1 | 98.16 | Pipeline TTFT 463.52 ms; prefill 507.16 tok/s; decode 98.16 tok/s; peak footprint 737.13 MiB; final thermal nominal | Complete: 5 completed, 0 failed, 0 not run (plus 1 retained warm-up) | runner_source_identity_missing | `c5431488-0556-4d67-bf77-10e3214b3dc1` |
| 2 | mlx-community/Qwen3-1.7B-4bit@3b1b1768f8f8; 4-bit; MLX Swift LM@3.31.4; iPhone15,3 / 26.5 (23F77); MLX Safetensors; MLX/Metal; App 0.6.0 build 8 (Not recorded); b-pipe-001-validation@0.2.0-pilot / b-mode-sustained-no-rest-v1 | 39.89 | Pipeline TTFT 1243.34 ms; prefill 189.04 tok/s; decode 39.89 tok/s; peak footprint 1389.31 MiB; final thermal serious | Complete: 5 completed, 0 failed, 0 not run (plus 1 retained warm-up) | runner_source_identity_missing | `17c24892-c14e-4e5e-82f7-667eafc2f5d1` |
| 3 | mlx-community/Qwen3-4B-3bit@c4e8054c71fa; 3-bit; MLX Swift LM@3.31.4; iPhone15,3 / 26.5 (23F77); MLX Safetensors; MLX/Metal; App 0.6.0 build 8 (Not recorded); b-pipe-001-validation@0.2.0-pilot / b-mode-sustained-no-rest-v1 | 10.83 | Pipeline TTFT 4680.22 ms; prefill 50.21 tok/s; decode 10.83 tok/s; peak footprint 2288.47 MiB; final thermal serious | Complete: 5 completed, 0 failed, 0 not run (plus 1 retained warm-up) | runner_source_identity_missing | `124ac922-3340-407c-8336-4695e59a3e47` |
