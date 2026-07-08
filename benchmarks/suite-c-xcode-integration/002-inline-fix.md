# Inline Fix

## Scenario

An iOS developer asks an assistant to fix a localized Swift compiler or runtime issue.

## Prompt

Given a Swift snippet with a type error, propose the smallest correct inline fix.

## Expected Behavior

- Identifies the cause of the issue.
- Changes only the necessary code.
- Preserves the surrounding architecture.
- Explains the fix briefly when requested.

## Scoring Rubric

Evaluate correctness, minimality, explanation quality, and preservation of intent.

## Notes for Reviewers

Use fixed snippets to compare models fairly.
