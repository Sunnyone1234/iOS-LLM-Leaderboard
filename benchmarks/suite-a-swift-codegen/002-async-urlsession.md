# Async URLSession

## Scenario

An iOS app needs to fetch JSON from an API using modern Swift concurrency.

## Prompt

Write Swift code that fetches and decodes JSON from a URL using `URLSession` and `async/await`.

## Expected Behavior

- Uses `URLSession.shared.data(from:)` or equivalent async API.
- Decodes with `JSONDecoder`.
- Handles invalid status codes and decoding errors.
- Uses clear model types.

## Scoring Rubric

Use the Suite A Swift Code Generation Score in `methodology/scoring.md`.

## Notes for Reviewers

Verify error handling and avoid awarding full credit for force unwraps or ignored failures.
