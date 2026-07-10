# Benchmark Validation

Benchmark validation defines the checks that should be applied to benchmark tasks and result submissions.

The repository includes an initial Framework v1 result validator in
scripts/validate_result.py. This document remains the source of validation
requirements; the script does not yet implement the future Framework v2 trust
and result-bundle model.

## Task Validation

Task validation should check:

- required metadata fields exist
- suite value is valid
- difficulty value is valid
- `task_type` value is valid
- `evaluation_mode` value is valid
- status value is valid
- `task_id` follows the required format
- task version is present
- active tasks include reproducibility requirements
- task has evaluation criteria and pass/failure conditions

## Result Validation

Result validation should check:

- required result fields exist
- score is numeric or null only for drafts/placeholders
- score is between 0 and `max_score`
- `task_id` is not empty
- `task_version` is present
- `model_name` is present
- provider is present
- evaluator is present
- contributor license confirmation is true
- metrics are numeric or null
- metrics.thermal_state is a documented categorical value or null
- demo-placeholder results are clearly marked
- demo-placeholder results are excluded from official leaderboards

## Current Script Coverage

The initial validator checks:

- nested Framework v1 required paths;
- placeholder-only null score and pass values;
- score range against evaluation.max_score;
- ISO execution date;
- supported access, run, and provenance values;
- metric types, including categorical thermal state;
- Suite B metadata and presence of a primary metric for non-placeholder results;
- contributor license confirmation.

## Future Validation

Future validation may check:

- `task_id` exists in `benchmarks/`
- `task_version` matches the task file
- suite name is valid
- official leaderboard excludes demo results
- runtime/device metadata is present for Suite B and Suite E
- benchmark release and workload hashes match
- submitted aggregates can be recalculated from raw evidence
- evidence level is supported by the required independent reproduction

## Leaderboard Rules

Official leaderboard generation should:

- exclude demo-placeholder results
- group results by suite
- record task version
- avoid averaging incompatible suites unless a formal weighting method exists
- clearly distinguish model scores
- clearly distinguish device performance
- clearly distinguish runtime comparisons
- clearly distinguish Xcode workflow results
- clearly distinguish app feature intelligence results

Do not combine Suite A, B, C, D, and E into a single global score unless a formal weighting methodology is defined.
