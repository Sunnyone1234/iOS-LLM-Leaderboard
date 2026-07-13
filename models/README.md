# Models

This directory documents how tested and recommended-for-testing models are
organized.

The machine-readable [Power test catalog](power-test-catalog.json) lists
artifact revisions that are selectable in the candidate Reference App but do
not yet have accepted physical-iPhone evidence. Catalog rows are discovery
and contribution targets, never leaderboard rows or performance claims.

Future machine-readable model records should use a stable model artifact ID.
The public leaderboard may display a concise model name, while result evidence
references the exact artifact and tested profile.

Model metadata should include:

- model name
- provider or publisher
- model version
- parameter count when known
- context length when known
- license
- hosted or local availability
- supported runtimes
- quantization details for local runs

Do not add unverified performance claims to model metadata.

An artifact may move out of `untested` only after a genuine App export is
submitted and accepted. Runtime registry support is not evidence that a model
loads, fits in memory, completes either workload, or performs well on an
iPhone.
