# Ship Deployment Profiles 1.0 RC1

These profiles translate published Power 1.0 evidence into deployment guidance. They define no Ship score and make no App Store, privacy, offline, minimum-device, or legal conclusion.

| Model | Exact tested profile | Artifact | Observed memory | Verified | Implementation-supported | Unknown | Evidence |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3 0.6B (4-bit) | mlx-community/Qwen3-0.6B-4bit@73e3e38d9813; MLX Swift LM 3.31.4; iPhone 14 Pro Max (iPhone15,3); iOS 26.5 (23F77) | 0.68 GB | 799 MiB | 5 | 2 | 6 | `ship-qwen3-0-6b-4bit-mlx-swift-lm-3.31.4-iphone15-3` |
| Qwen3 1.7B (4-bit) | mlx-community/Qwen3-1.7B-4bit@3b1b1768f8f8; MLX Swift LM 3.31.4; iPhone 14 Pro Max (iPhone15,3); iOS 26.5 (23F77) | 0.98 GB | 1791 MiB | 5 | 2 | 6 | `ship-qwen3-1-7b-4bit-mlx-swift-lm-3.31.4-iphone15-3` |
| Qwen3 4B (3-bit) | mlx-community/Qwen3-4B-3bit@c4e8054c71fa; MLX Swift LM 3.31.4; iPhone 14 Pro Max (iPhone15,3); iOS 26.5 (23F77) | 1.77 GB | 2370 MiB | 5 | 2 | 6 | `ship-qwen3-4b-3bit-mlx-swift-lm-3.31.4-iphone15-3` |

`Observed memory` is the largest eligible Power workload median peak for the profile. It is not a minimum RAM requirement.

See [the method](../../docs/ship-deployment-profiles.md), [machine-readable profiles](deployment-profiles.json), and [the MLX Swift recipe](../../examples/mlx-swift/README.md).
