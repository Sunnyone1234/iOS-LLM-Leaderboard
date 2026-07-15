# Suite B Power 1.1 RC1 Evidence

This directory contains the newly executed Power 1.1 RC1 physical-device
review matrix. It contains no fabricated or promoted data. Power 1.0 and Power
1.1 draft results are not copied here.

Release-candidate review package:

```text
device-verification/
  raw/          six unmodified App 0.13.0 exports
  validation/   six validator-generated, SHA-bound reports
  CHECKSUMS.sha256
  INTAKE-2026-07-15.md
  REVIEW.md
RELEASE-NOTES.md
```

All six result/report pairs pass the frozen independent consumer. They remain
non-official and ranking-ineligible until the final `1.1.0` policy, regenerated
reports, and explicit maintainer adoption are complete. See
[`power-benchmark-1.1-rc1-device-verification.md`](../../docs/power-benchmark-1.1-rc1-device-verification.md)
and
[`power-benchmark-1.1-finalization.md`](../../docs/power-benchmark-1.1-finalization.md).

Rejected or superseded intake is recorded without being promoted into the raw
release matrix. The first such review is
[`device-verification/INTAKE-2026-07-15.md`](device-verification/INTAKE-2026-07-15.md).
