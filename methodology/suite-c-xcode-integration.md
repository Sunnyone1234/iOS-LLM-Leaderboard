# Suite C: Xcode Integration Methodology

Suite C evaluates how useful a model is inside Xcode-oriented development workflows.

This suite is independent from Suite A. Suite C focuses on workflow fit, edit locality, completion quality, and integration experience rather than standalone code generation.

## Evaluation Focus

- code completion relevance
- inline fix correctness
- edit minimality
- refactoring quality
- preservation of existing project style
- usefulness inside Xcode or Xcode-like editor workflows

## Review Expectations

Reviewers should record:

- editor or assistant integration
- model and provider
- Xcode version when applicable
- project context supplied to the model
- whether generated changes compile
- whether the edit changed behavior unintentionally

## Suite Boundary

Tasks that ask for complete standalone Swift or SwiftUI code belong in Suite A. Tasks that evaluate completion, inline repair, refactoring, or assistant behavior inside an editor workflow belong in Suite C.
