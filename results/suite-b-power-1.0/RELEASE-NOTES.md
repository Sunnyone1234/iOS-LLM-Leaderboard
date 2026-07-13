# Power Benchmark 1.0 Final Package Notes

## Status

This is a final review candidate. Publishing, tagging, and official ranking remain disabled until explicit final approval.

## No-rerun adoption

Power 1.0 adopts the exact six F5 result files produced by App 0.8.0 build 10.
The App, workload prompts, timing boundaries, metric formulas, eligibility rules, result schema, and validator are unchanged from RC1.
Raw result identities and bytes remain `1.0.0-rc.1`; the final publication layer binds them by result ID and SHA-256 instead of rewriting them.

## Candidate ranking coverage

- 6 retained physical-device results;
- 5 primary-metric-eligible result rows;
- 3 exact model artifacts;
- one iPhone15,3, one iOS build, and one MLX Swift LM runtime; and
- one retained Short Interaction response-ineligible row.

## Required final decisions

- confirm the contributor declarations for the six maintainer-run results;
- approve the final publication manifest;
- authorize official-result and ranking flags; and
- authorize the GitHub Release and version tag.

Ship deployment profiles and integration recipes follow after the Power 1.0 publication.
