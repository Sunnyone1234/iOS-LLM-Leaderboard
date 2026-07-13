# Community Submissions

Suite B uses immutable App-generated Draft submissions and separate maintainer
review records.

## Contributor flow

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

## Maintainer promotion

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

