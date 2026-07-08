# Suite A: Swift Code Generation Methodology

Suite A evaluates whether a model can produce correct, maintainable Swift and SwiftUI code for real iOS development workflows.

This suite is independent from Suite C. Suite A focuses on generated code quality rather than editor integration behavior.

## Evaluation Focus

- Swift language correctness
- SwiftUI architecture and state management
- Apple framework usage
- Compile success in a realistic project context
- XCTest coverage when requested
- Maintainability and readability

## Rubric

Use the Suite A Swift Code Generation Score from [scoring.md](scoring.md):

- Compile success: 30%
- Functional correctness: 30%
- Swift idiomatic quality: 20%
- Modern Apple API usage: 10%
- Readability and architecture: 10%

## Review Expectations

Reviewers should record:

- Xcode version
- Swift version
- target platform
- warnings or compile errors
- manual fixes required, if any

Generated code should not receive full credit if it only works after substantial reviewer repair.

## Suite Boundary

Tasks that primarily measure completion, inline fixes, or refactoring inside an editor workflow belong in Suite C.
