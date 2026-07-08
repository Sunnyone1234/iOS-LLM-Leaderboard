# Suite E: Runtime Evaluation Methodology

Suite E tracks how local and Apple-platform inference runtimes differ for iOS developers.

This suite is independent from Suite B. Suite E focuses on runtime characteristics, integration tradeoffs, and comparable runtime reporting.

No benchmark numbers are defined in this MVP.

## Runtimes In Scope

- MLX Swift
- llama.cpp
- CoreML
- LiteRT-LM
- Apple Foundation Models
- Future Apple runtime APIs

## Comparison Criteria

- supported model formats
- iOS support maturity
- Apple Silicon support
- quantization support
- memory profile
- first token latency
- tokens per second
- integration complexity
- licensing and redistribution considerations

## Reporting

Runtime reports should include device metadata, model metadata, runtime version, build settings, and measurement method.

## Suite Boundary

Device-specific local performance submissions belong in Suite B. Cross-runtime comparison and runtime integration evaluation belong in Suite E.
