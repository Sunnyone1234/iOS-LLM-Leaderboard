# Suite B Power 1.0 RC.1 F5 Device Verification Evidence

## Status

This directory contains the completed F5 physical-device verification matrix
for `suite-b-power@1.0.0-rc.1`. It is release-candidate evidence, not an
official benchmark release, and it does not authorize leaderboard ranking.

The matrix contains six unmodified exports from App `0.8.0` build `10` at
source commit `2f105ff463bc9b281b19655ba711b1ca7dee8759`:

- three pinned Qwen3 artifacts;
- both frozen Power 1.0 RC.1 workloads;
- MLX Swift LM `3.31.4`; and
- one physical `iPhone15,3` running iOS `26.5` (`23F77`).

No result is simulated, synthesized, hand-edited, or promoted from the
historical Pilot.

## Contents

- `raw/`: the six original App JSON exports, retained byte-for-byte;
- `validation/`: deterministic reports emitted by the frozen
  `suite-b-power-validator@1.0.0-rc.1`; and
- `SHA256SUMS`: integrity digests for every raw export and validation report.

The complete review and interpretation limits are recorded in
[`docs/power-benchmark-1.0-f5-device-verification.md`](../../../docs/power-benchmark-1.0-f5-device-verification.md).

## Validation outcome

All six exports are structurally valid and protocol-conformant. Five matrix
cells have eligible metrics. The Qwen3 0.6B Short Interaction result completed
all attempts but failed the frozen response-conformance gate on every attempt,
so its metrics remain null and ineligible. This is retained capability
evidence, not a missing or rejected run.

Every validation report remains `validWithWarnings`, `unreviewed`, and
ranking-ineligible because the release candidate itself does not grant an
evidence level or authorize official ranking. F5 review does not rewrite those
frozen validator decisions.

## Verify

From this directory:

```bash
shasum -a 256 -c SHA256SUMS
```

From the repository root, regenerate an individual report with:

```bash
python3 scripts/validate_suite_b_power_result.py \
  results/suite-b-power-1.0.0-rc.1/f5-device-verification/raw/<result>.json
```
