# Submit a Model Result

Use this guide when submitting a result for a benchmark task.

This is the current Framework v1 manual workflow. Passing format validation
does not by itself make a result official, reproduced, or verified.

## Steps

1. Choose an existing task from `benchmarks/`.
2. Run the model with the task prompt.
3. Review the output using the documented scoring rubric.
4. Copy `templates/model-result-template.json`.
5. Fill in all required fields.
6. Place the completed JSON file in `results/raw/`.
7. Confirm the JSON parses and follows `methodology/benchmark-result-specification.md`.
8. Open a pull request with the raw result and any relevant notes.

## Required Fields

- `schema_version`
- `result_id`
- `task.task_id`
- `task.task_version`
- `task.suite`
- `model.model_name`
- `model.provider`
- `execution.date`
- `execution.evaluator`
- `evaluation.score`
- `evaluation.max_score`
- `evaluation.passed`
- `license_confirmation.contributor_agrees_to_repo_license`

Do not submit placeholder or fabricated results.
