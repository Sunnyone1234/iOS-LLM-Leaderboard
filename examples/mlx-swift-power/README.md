# Exact Power model recipe

[`ExactPowerModel.swift`](ExactPowerModel.swift) loads the exact Hugging Face
artifact and immutable revision attached to any Power leaderboard row.

```swift
let model = try await ExactPowerModel.load(
    artifactID: "mlx-community/gemma-3-1b-it-qat-4bit",
    revision: "15fed4eafb456c6fcb2a1165f19ac609670ed14b"
)
```

Use the package versions documented by the
[published MLX Swift recipe](../mlx-swift/README.md). A successful load does not
establish offline behavior, packaging, licensing, supported devices, or App
Store readiness. Those claims appear only when the exact model revision has a
published Ship profile.

This separate Power recipe keeps the checksum-frozen Ship 1.0 recipe unchanged.
