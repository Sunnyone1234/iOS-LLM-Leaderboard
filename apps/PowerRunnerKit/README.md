# PowerRunnerKit

PowerRunnerKit is the Power 2 measurement implementation. It is a Swift package
so measurement-critical modules can be built and tested without SwiftUI or
GitHub OAuth.

The package deliberately separates:

- `PowerEvidence` — immutable Power 2 evidence value types and deterministic
  JSON serialization;
- `PowerRunnerCore` — monotonic attempt lifecycle and failure preservation;
- `PowerTextProgram` — the text-generation Program contract adapter;
- `PowerAppleTarget` — iPhone environment capture and ranking admission;
- `PowerMLXRuntime` — exact MLX/Tokenizer dependency identity, immutable model
  revision loading, and token-stream adaptation.

The active release keeps its certified `component-manifest.json` bytes
unchanged. Ongoing source work is hashed into the separate
`candidate-component-manifest.json`, so editing Runner code cannot silently
rewrite the active release identity. Any changed digest requires a new
certificate after generic builds, package tests, and reviewed physical-device
Certification evidence pass.

Run:

```bash
swift test --package-path apps/PowerRunnerKit
python3 scripts/generate_power_mlx_dependency_identity.py --check
python3 scripts/generate_power_runner_component_manifest.py --check
```
