# Power 1.0 RC.1 Evidence Reviews

This directory stores accepted, immutable evidence-transition records using
`suite-b-power-review-1.0.0-rc.1`.

Review filenames must equal `<reviewID>.json`. Review records bind a Draft
manifest and result by SHA-256. They never modify the source package and cannot
authorize ranking while RC1 remains non-official.

Validate the complete transition history with:

```bash
python3 scripts/validate_suite_b_power_reviews.py \
  --submissions submissions/suite-b/power-1.0.0-rc.1/draft \
  --reviews submissions/suite-b/power-1.0.0-rc.1/reviews
```
