# Scoring Methodology

This document defines the initial scoring model for iOS-LLM-Leaderboard. Scores are intended to be transparent, reviewable, and reproducible across the five independent benchmark suites.

No official benchmark results exist yet.

## Score Scale

Unless a task defines otherwise, scores should use a 0 to 100 scale.

- `0`: unusable or non-responsive
- `50`: partially correct but materially flawed
- `80`: useful with minor issues
- `100`: excellent and production-ready for the stated task

## Suite A: Swift Code Generation Score

Swift and SwiftUI code generation tasks use this weighted rubric:

| Dimension | Weight |
| --- | ---: |
| Compile success | 30% |
| Functional correctness | 30% |
| Swift idiomatic quality | 20% |
| Modern Apple API usage | 10% |
| Readability and architecture | 10% |

## Suite B: On-device Performance Score

On-device scores should not be aggregated until enough device and runtime data exists. Early submissions should report raw measurements with device metadata.

Metrics include:

- tokens per second
- first token latency
- peak memory usage
- thermal behavior
- battery or energy observations
- runtime and quantization details

## Suite C: Xcode Integration Score

Xcode integration tasks evaluate usefulness inside editor workflows.

Recommended dimensions:

- completion or edit relevance
- compile correctness
- edit minimality
- preservation of surrounding project style
- explanation quality when requested
- workflow usefulness

## Suite D: App Feature Intelligence Score

App feature tasks evaluate whether a model can support realistic product features in an iOS app.

Recommended dimensions:

- Task accuracy
- Structured output quality
- Robustness across edge cases
- Cost and latency awareness
- Safety and refusal behavior where appropriate
- integration suitability for iOS apps

## Suite E: Runtime Evaluation Score

Runtime evaluation should report raw measurements and qualitative integration notes until a suite-specific scoring model is defined.

Recommended dimensions:

- supported model formats
- iOS support maturity
- Apple Silicon support
- quantization support
- memory profile
- first token latency
- tokens per second
- integration complexity
- licensing and redistribution considerations

## Privacy and Compliance Score

Privacy and compliance reviews should describe evidence and uncertainty. They should avoid legal conclusions unless performed by qualified reviewers.

Review dimensions include:

- provider privacy policy
- whether user data is used for training
- safety guardrails
- suitability for App Store-facing applications
- local or offline inference support
- data retention and logging controls

## Reviewer Notes

Reviewers should record assumptions, test environment, model version, date, and any deviations from the task instructions.

Suite scores should remain independent unless a future methodology explicitly defines an aggregate score.
