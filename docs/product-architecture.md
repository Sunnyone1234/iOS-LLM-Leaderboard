# Product Architecture

## Overview

The project is organized as a closed evidence loop:

1. a benchmark release freezes tasks, workloads, metrics, and schemas;
2. the official benchmark app executes that release on a physical device;
3. the app exports a result bundle;
4. repository automation validates the bundle;
5. community reproduction increases evidence confidence;
6. leaderboard views aggregate compatible results;
7. model pages provide short integration recipes backed by tested profiles.

## Layer 1: Benchmark Specification

This layer owns:

- suite boundaries;
- versioned workloads;
- measurement procedures;
- metric definitions;
- task and result schemas;
- benchmark release policy;
- comparison and aggregation rules.

It must be possible to determine exactly which benchmark release produced a
result.

## Layer 2: Community Evidence

This layer owns:

- official runner and app versions;
- device and environment capture;
- raw run evidence;
- repository submissions;
- automated and manual validation;
- evidence levels;
- independent reproduction.

The official app lowers contribution effort and reduces uncontrolled
differences. It does not eliminate the need for evidence review.

## Layer 3: Developer Integration Guide

This layer owns:

- model-centered detail pages;
- tested device and runtime information;
- compact Swift recipes;
- runtime installation;
- model loading and generation examples;
- distribution and license notes.

Integration guidance should reference benchmark identities, but it must remain
useful to developers who do not need to understand the full result schema.

## Leaderboard Presentation Model

The public view and evidence view serve different readers.

### Public view

- model name;
- model size;
- headline quality and performance indicators;
- supported or verified devices;
- recommended use cases;
- concise reference-profile label.

### Evidence view

- model artifact and revision;
- quantization;
- runtime and backend;
- device and OS build;
- inference settings;
- benchmark release;
- per-run values;
- failure evidence;
- contributor and trust status.

## Recommended Small Models

Recommended small-model lists should show model names, not internal
configuration IDs.

Eligibility should still depend on a tested reference profile and minimum
evidence rules. The recommendation should link to:

- the profile used for the headline result;
- compatible devices;
- known limitations;
- short integration recipes.

## Suite Relationships

- Suite B owns standardized device measurements.
- Suite D can provide a minimum quality gate for local model recommendations.
- Suite E reuses Suite B measurements and adds runtime integration evidence.
- Suite A and Suite C remain in the Developer Assistance track.

No suite should redefine another suite's canonical metric boundaries.
