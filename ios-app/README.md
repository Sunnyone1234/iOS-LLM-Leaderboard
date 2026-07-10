# Official iOS Benchmark App

This directory is reserved for the official community benchmark app.

The app is data-collection infrastructure for iOS-LLM-Leaderboard. It is not a
starter app for developers to copy into unrelated products.

## Purpose

The app should allow an iOS developer to:

1. install the official runner on a physical device;
2. select a compatible model profile and benchmark release;
3. run a locked, reproducible procedure;
4. review local results and every field proposed for submission;
5. submit a result bundle with minimal manual work.

The project cannot depend on one maintainer owning every iPhone and iPad model.
The app is the intended path for community device coverage.

## MVP Scope

- physical iPhone support first;
- automatic public device and OS metadata;
- versioned model profiles;
- MLX Swift as the first runtime adapter;
- local benchmark execution with no network dependency during measured phases;
- progress, cancellation, and failure reporting;
- summary and raw-run result export;
- contributor review before upload;
- local use without mandatory submission.

## Intended Submission Flow

1. The app exports a versioned result bundle.
2. A submission service or GitHub App validates the upload.
3. A pull request or bot-managed repository submission is created.
4. Repository automation performs structural and semantic checks.
5. The result enters the appropriate evidence level.

The app must not write directly to the default branch.

## Data Boundary

Expected benchmark metadata:

- public device model and chip;
- OS version and build;
- benchmark app and release version;
- model artifact, quantization, and runtime identity;
- inference settings;
- timing, token, memory, thermal, and failure evidence;
- integrity hash.

The app should not collect Apple ID, serial number, UDID, personal prompts,
user documents, or unrelated app data.

## Architecture Direction

The runner should use a runtime adapter boundary so that benchmark semantics do
not depend on MLX Swift.

Later adapters may support:

- llama.cpp;
- Core ML;
- Apple Foundation Models where equivalent measurements are possible;
- future Apple-platform runtimes.

No app implementation is included yet.
