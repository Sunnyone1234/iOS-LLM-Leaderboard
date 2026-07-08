# Runtime Comparison Template

## Scenario

A contributor compares an identical model across Apple-platform inference runtimes.

## Prompt

Run the same prompt with the same model, quantization, and device across selected runtimes and report raw observations.

## Expected Behavior

- Uses comparable model files where possible.
- Records runtime versions.
- Records build and device details.
- Avoids inventing missing metrics.

## Scoring Rubric

This is a reporting template, not an official ranking.

## Notes for Reviewers

Supported runtime categories include MLX Swift, llama.cpp, CoreML, LiteRT-LM, Apple Foundation Models, and future Apple runtime APIs.
