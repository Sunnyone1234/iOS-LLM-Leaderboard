# Framework v2 Transition

## Status

Framework v2 is a design target, not an active benchmark standard.

Framework v1 remains the current repository format until a migration document,
machine-readable schemas, reference examples, and validators are accepted.

## Why a New Version Is Needed

Framework v1 uses task for several different concepts:

- a user scenario;
- a measurement protocol;
- a metric-specific test;
- a runtime comparison template.

It also uses one result structure across suites with very different evidence.

Framework v2 should separate:

- workload: the versioned input and output requirements;
- measurement mode: warm, cold, memory, thermal, or another execution state;
- metric: a value calculated from observations;
- task: an executable combination of workload and measurement mode;
- result bundle: summary plus raw evidence from one submission.

## Proposed Result Architecture

### Common envelope

- schema version;
- benchmark release;
- suite and task identity;
- submission identity;
- contributor and date;
- provenance;
- evidence level;
- artifact references;
- license confirmation.

### Configuration identity

- model artifact;
- tokenizer and chat template;
- quantization;
- runtime build and backend;
- device profile and OS build;
- inference configuration;
- runner build.

### Suite-specific payload

Each suite defines its own payload and validation rules.

Suite B may store token events, timing, memory, thermal, cache, and failures.
Suite A may store generated files, compile results, tests, and rubric scores.

## Compatibility Rules

- do not reuse a task ID for a different workload;
- provide an explicit v1 to v2 mapping;
- keep existing draft results labeled with their original schema;
- do not merge v1 and v2 results in one ranking;
- version workloads independently from documentation wording;
- keep benchmark releases immutable after publication.

## Transition Order

1. approve project vision and product architecture;
2. approve Framework v2 concepts;
3. define Suite B payload and result bundle;
4. implement schemas and validators;
5. implement the reference app export;
6. publish the first Suite B benchmark release;
7. migrate other suites separately.
