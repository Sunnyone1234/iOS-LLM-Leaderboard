# PowerAppKit

PowerAppKit is the non-measurement support layer for the Power 2 App. It is MIT
licensed and deliberately separate from the Runner certificate digest.

- `PowerResultsStore` writes the encoded evidence once and later returns the
  exact same bytes.
- `PowerRunCheckpointStore` atomically records attempt lifecycle so a process
  termination preserves the active attempt as failed and later attempts as
  not-run instead of silently losing the session.
- `PowerReleasePreflight` hash-verifies the active remote pointer and App
  release before an Official source configuration may test or submit.
- `PowerSubmissionKit` creates the two-file contribution package without
  rewriting `result.json`.
- `PowerGitHubSubmission` performs Device Flow and opens a result-only pull
  request from a contributor fork.

The GitHub client does not synchronize the fork's default branch. It creates a
fresh submission branch from the exact upstream default-branch commit instead,
so a public-repository OAuth token does not need permission to update workflow
files merely because a fork is behind.

An App release pins the exact App component manifest that consumes this
package. Later source changes require a new App release; they never rewrite an
existing release identity.
