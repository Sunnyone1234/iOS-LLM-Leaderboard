# MLX Swift Integration Recipe

[`PinnedMLXModel.swift`](PinnedMLXModel.swift) is the focused integration recipe
for the three Ship 1.0 RC1 reference profiles. It mirrors the revision-pinned
loader, tokenizer adapter, and token-stream boundary used by the tested
benchmark App without requiring an app to adopt the benchmark runner.

## Exact package versions

Add these Swift packages in Xcode and select the listed products:

| Package | Exact version | Products |
| --- | --- | --- |
| `https://github.com/ml-explore/mlx-swift-lm` | `3.31.4` | `MLXLLM`, `MLXLMCommon` |
| `https://github.com/huggingface/swift-huggingface` | `0.9.0` | `HuggingFace` |
| `https://github.com/huggingface/swift-transformers` | `1.3.0` | `Tokenizers` |

These are the direct package versions used by the Power 1.0 reference App. Its
resolved lockfile also records `mlx-swift` `0.31.6` at revision
`0bb916c67f4b9e5c682cbe02a42c701c93ab5021`.

## Load and stream

```swift
let model = try await PinnedMLXModel.load(.qwen3_0_6B)

let completion = try await model.stream(prompt: "Explain this feature briefly") {
    index, tokenID in
    // Decode or batch token IDs for your UI at a cadence appropriate for the app.
    print(index, tokenID)
}

print(completion.generationTokenCount)
```

The default load path can download the exact pinned revision when absent. Once
the artifact is cached, pass `localFilesOnly: true` when the app should fail
instead of attempting a network request:

```swift
let model = try await PinnedMLXModel.load(
    .qwen3_0_6B,
    localFilesOnly: true
)
```

## Evidence boundary

Power 1.0 verifies the exact artifacts, cached revision-pinned model loading,
completed physical-device inference, and runtime token events on the tested
iPhone 14 Pro Max configuration. The first-run download path is present in the
reviewed implementation but was deliberately excluded from measured attempts.

The current evidence does **not** verify fully offline operation, cancellation,
model bundling, minimum supported hardware, privacy compliance, or App Store
readiness. See the [Ship method](../../docs/ship-deployment-profiles.md) and
[machine-readable profiles](../../results/ship-1.0/deployment-profiles.json)
before using a measured constraint as a product requirement.

The model license URLs in each Ship profile are publisher metadata for developer
review, not legal advice. This recipe is code covered by the repository's MIT
license.
