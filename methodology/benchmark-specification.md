# Benchmark Task Specification

> This document defines Framework v1 tasks. Framework v2 separates Suite B
> workloads, measurement modes, metrics, model profiles, and result bundles;
> see [Framework v2 Architecture](benchmark-framework-v2.md).

Benchmark tasks are Markdown files with four logical layers:

1. Metadata
2. Specification
3. Evaluation
4. Reproducibility

Every benchmark task must belong to exactly one suite.

## Required Markdown Structure

```markdown
# Task Title

## Task Metadata

| Field | Value |
|---|---|
| task_id | suite-a-swift-codegen-001 |
| suite | Suite A: Swift Code Generation |
| category | SwiftUI |
| subcategory | List Deletion |
| difficulty | easy |
| task_type | generation |
| evaluation_mode | hybrid |
| version | 1.0 |
| status | draft |
| author | project-maintainers |
| created | YYYY-MM-DD |
| last_updated | YYYY-MM-DD |
| tags | swiftui, list, deletion |

## Objective

Describe what capability this benchmark task evaluates.

## Background

Explain why this task matters for real iOS developers.

## Input

Provide the exact model prompt, IDE context, or measurement setup.

## Expected Output

Describe the expected output format and behavior.

## Evaluation

### Automatic Evaluation

List checks that can be performed automatically.

### Manual Evaluation

List review criteria that require human judgment.

### Pass Conditions

List minimum conditions required to pass the task.

### Failure Conditions

List conditions that should cause failure or heavy penalty.

## Scoring Rubric

Define the scoring scale for this task.

## Reproducibility Requirements

List required environment, tooling, device, runtime, dependency, or model metadata.

## Reviewer Notes

Add notes for maintainers and reviewers.
```

## Required Metadata Fields

Each task must include:

- `task_id`
- `suite`
- `category`
- `subcategory`
- `difficulty`
- `task_type`
- `evaluation_mode`
- `version`
- `status`
- `author`
- `created`
- `last_updated`
- `tags`

## task_id Format

Use this format:

```text
suite-[suite-letter]-[suite-name]-[number]
```

Examples:

```text
suite-a-swift-codegen-001
suite-b-on-device-performance-001
suite-c-xcode-integration-001
suite-d-app-feature-intelligence-001
suite-e-runtime-evaluation-001
```

Rules:

- `task_id` must be stable.
- `task_id` must not be reused.
- `task_id` must not change when the task title changes.
- If prompt, expected output, or scoring changes materially, update task version instead of changing `task_id`.

## Allowed suite Values

```text
Suite A: Swift Code Generation
Suite B: On-device Performance
Suite C: Xcode Integration
Suite D: App Feature Intelligence
Suite E: Runtime Evaluation
```

## Allowed difficulty Values

```text
easy
medium
hard
```

Definitions:

- `easy`: common app-level task with limited edge cases
- `medium`: requires multiple APIs, state handling, or structured reasoning
- `hard`: requires architecture, multi-file reasoning, performance awareness, or careful safety behavior

## Allowed task_type Values

```text
generation
completion
refactoring
review
extraction
classification
translation
conversation
measurement
```

Definitions:

- `generation`: create new output from a prompt
- `completion`: complete partial code or text
- `refactoring`: improve or transform existing code
- `review`: identify problems and suggest fixes
- `extraction`: convert unstructured input into structured output
- `classification`: assign labels or categories
- `translation`: translate between languages
- `conversation`: roleplay or multi-turn behavior
- `measurement`: collect runtime or device performance metrics

## Allowed evaluation_mode Values

```text
automatic
manual
hybrid
measurement
```

Definitions:

- `automatic`: evaluated mostly by tests, scripts, parsing, or deterministic checks
- `manual`: requires human review
- `hybrid`: combines automatic and human evaluation
- `measurement`: based on device, runtime, latency, memory, energy, or thermal metrics

## Allowed status Values

```text
draft
active
deprecated
```

Only active tasks should be used for official leaderboard results.

## Version Rules

Use simple semantic versioning:

```text
1.0
1.1
2.0
```

Rules:

- minor update: wording clarification that does not change scoring meaning
- major update: prompt, expected output, scoring rubric, or pass/fail criteria changes materially
- all results must record the task version used

## Suite-Specific Task Requirements

### Suite A: Swift Code Generation

Required:

- exact prompt
- target platform
- target Swift version if relevant
- target iOS version if relevant
- expected APIs
- compile requirements
- optional unit test requirements

Typical evaluation:

- compile success
- functional correctness
- Swift idiomatic quality
- modern Apple API usage
- readability and architecture

### Suite B: On-device Performance

The following requirements apply only to legacy Framework v1 measurement-task
drafts. New Suite B design must use versioned workloads and the common metric
set instead of creating one task per metric.

Required:

- model
- quantization
- device
- OS version
- runtime
- prompt length
- output length
- warm-up procedure
- measurement procedure

Typical metrics:

- TTFT
- prefill tokens/sec
- decode tokens/sec
- peak memory
- thermal state
- energy notes
- p50 / p95 / p99 token interval if available

Suite B may not contain a normal model prompt. It may contain a measurement protocol instead.

### Suite C: Xcode Integration

Required:

- Xcode version or IDE environment
- initial code context
- requested IDE action
- expected developer workflow result
- compile or review criteria

Typical evaluation:

- completion usefulness
- compiler error repair
- refactoring correctness
- preservation of existing behavior
- developer time saved

### Suite D: App Feature Intelligence

Required:

- user-facing app scenario
- input data
- expected output format
- structured output requirements if applicable
- safety constraints if applicable

Typical evaluation:

- task accuracy
- structured output validity
- robustness
- latency and cost awareness
- safety behavior

### Suite E: Runtime Evaluation

Required:

- runtime name
- runtime version
- model format
- backend
- device
- operating system
- measurement protocol

Typical evaluation:

- runtime compatibility
- setup complexity
- memory behavior
- throughput
- stability
- suitability for iOS developer integration
