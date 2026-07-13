# Community Submissions

Power 1.0 RC1 uses immutable two-file Draft packages and separate,
hash-bound maintainer review records. The executable candidate path is:

```text
submissions/suite-b/power-1.0.0-rc.1/
```

Read the [Power submission guide](../docs/power-benchmark-1.0-submission.md)
and [governance policy](../docs/power-benchmark-1.0-governance.md). Public
intake remains closed until explicit release approval.

## Power RC1 contributor flow

1. Review the unmodified App Power result.
2. Explicitly accept the contributor and CC BY 4.0 declarations.
3. Create the two-file package with
   `scripts/create_suite_b_power_submission.py`.
4. Validate it with `scripts/validate_suite_b_power_submission.py`.
5. Open a pull request and wait for both CI and maintainer review.

Passing validation leaves evidence `unreviewed` and ranking-ineligible. Trust
changes only through a merged record validated by
`scripts/validate_suite_b_power_reviews.py`.

## Historical Pilot path

The paths below retain the earlier `suite-b-community-submission-0.1` Pilot
workflow for compatibility. They are not Power 1.0 packages and cannot be
promoted into Power 1.0 evidence.

### Pilot contributor flow

1. Validate the exported package locally.
2. Rename it to `<submissionID>.json` without changing its contents.
3. Place it in `submissions/suite-b/draft/` on a contribution branch.
4. Open a pull request and wait for the Suite B submissions check.

```bash
python3 scripts/validate_suite_b_submission.py exported-submission.json
python3 scripts/validate_suite_b_intake.py submissions/suite-b/draft \
  --report /tmp/suite-b-intake-report.json
```

Structural validation leaves the submission at Draft and never changes the
default leaderboard.

### Pilot maintainer promotion

After CI passes and review is complete, a maintainer may create a Community
Submitted record:

```bash
python3 scripts/promote_suite_b_submission.py \
  --submission submissions/suite-b/draft/<submissionID>.json \
  --reviewer <maintainer-handle> \
  --output submissions/suite-b/reviews/community-submitted/<submissionID>.json
```

The promotion tool cannot assign Reproduced, Verified, Maintainer Reference,
or default leaderboard eligibility. Those future transitions require separate
evidence and governance rules.
