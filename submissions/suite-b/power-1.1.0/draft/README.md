# Power 1.1 Community Submissions

Each child directory is an immutable two-file package created by
`python3 scripts/power.py submit`:

```text
<submissionID>/
├── submission.json
└── result.json
```

`result.json` is the untouched App 0.13.0 export. `submission.json` records the
public GitHub contributor, declarations, environmental disclosure, and the
SHA-256 binding. CI validates both files. A valid merged package can enter the
live community view, but it does not alter the immutable Power 1.1 release or
grant Verified status.
