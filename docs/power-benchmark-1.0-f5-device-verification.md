# Power Benchmark 1.0 F5 Device Verification

## Status

F5 complete for `suite-b-power@1.0.0-rc.1`.

This review verifies the frozen F2 protocol, F3 schema and validator, and F4
reference App against genuine physical-device evidence. It changes no
protocol, schema, validator, release manifest, workload, model profile,
runtime, benchmark App, or ranking decision. Power Benchmark 1.0 is not yet
published; F6 governance and publication work remains required.

## Declared matrix

The fixed F5 matrix is one reference runtime and device across three pinned
model artifacts and the two frozen workloads:

| Model artifact | Revision | Short Interaction | Sustained Generation |
| --- | --- | --- | --- |
| `mlx-community/Qwen3-0.6B-4bit` | `73e3e38d981303bc594367cd910ea6eb48349da8` | Completed; response gate failed; metrics ineligible | Completed; metrics eligible |
| `mlx-community/Qwen3-1.7B-4bit` | `3b1b1768f8f8cf8351c712464f906e86c2b8269e` | Completed; metrics eligible | Completed; metrics eligible |
| `mlx-community/Qwen3-4B-3bit` | `c4e8054c71facfa84f781cdb7c1ffab3f09f89bf` | Completed; metrics eligible | Completed; metrics eligible |

All six cells contain genuine App exports. Matrix completeness means every
declared cell was executed and its terminal evidence retained; it does not
mean every model passed every per-metric eligibility gate.

## Frozen execution identity

All six exports agree on:

- result schema `suite-b-power-result-1.0.0-rc.1`;
- benchmark release and protocol `suite-b-power@1.0.0-rc.1`;
- App `0.8.0` build `10`, runner `ios-reference-benchmark-app@0.8.0`;
- App source commit `2f105ff463bc9b281b19655ba711b1ca7dee8759`;
- MLX Swift LM `3.31.4`, resolved revision
  `bd4b7434e6bdb588c7ef55706ff8904cb7fd4c57`;
- `mlx-swift` `0.31.6@0bb916c67f4b9e5c682cbe02a42c701c93ab5021`;
- a physical `iPhone15,3`, iOS `26.5` build `23F77`; and
- Release configuration, no debugger, Low Power Mode disabled, unplugged,
  cached pinned artifacts, and no model download during a session.

Each export has a distinct `resultID` and `sessionID`. Every session began at
nominal thermal state. All 36 attempts have the frozen sequence of one warmup
plus five measured attempts and a `completed` terminal outcome. Sustained
Generation emitted exactly 512 tokens per attempt and stopped at the output
limit. Short Interaction stopped at EOS.

## Independent validator review

Every raw export was processed without modification by
`suite-b-power-validator@1.0.0-rc.1`. The validator verified the pinned release
assets and recalculated every candidate metric from retained timing, token,
memory, renderability, response, and thermal evidence.

| Check | Outcome |
| --- | --- |
| Raw exports received | 6 |
| Structural validity | 6 valid, 0 invalid |
| Protocol conformance | 6 valid, 0 invalid |
| Validator status | 6 `validWithWarnings` |
| Matrix cells with eligible metrics | 5 |
| Matrix cells with retained ineligible metrics | 1 |
| Official or ranking-eligible results | 0 |

No recalculated attempt metric, summary aggregate, terminal count, or pinned
identity disagreed with an exported value. Deterministic validation reports
are retained beside the raw evidence.

## Evidence metrics

These values document validator-recalculated F5 evidence. They are not an
official leaderboard and are not cross-workload scores.

### Short Interaction

| Model | First-renderable proxy TTFT (ms) | Pipeline TTFT (ms) | Completion (ms) | Prefill (tok/s) | Decode (tok/s) | Footprint (MiB) | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3 0.6B 4-bit | N/A | N/A | N/A | N/A | N/A | N/A | Response conformance failed in 6/6 attempts |
| Qwen3 1.7B 4-bit | 494.40 | 492.03 | 1262.60 | 142.32 | 43.53 | 1791.47 | Eligible |
| Qwen3 4B 3-bit | 1132.81 | 1127.86 | 2810.89 | 62.07 | 21.05 | 2370.44 | Eligible |

First-renderable proxy TTFT is an adapter measurement, not a screen-render
boundary.

### Sustained Generation

| Model | Pipeline TTFT (ms) | Prefill (tok/s) | Decode (tok/s) | Footprint (MiB) | First-to-last decode change | End thermal state | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Qwen3 0.6B 4-bit | 463.98 | 506.69 | 97.90 | 798.53 | +3.08% | fair | Eligible |
| Qwen3 1.7B 4-bit | 1416.04 | 165.98 | 29.71 | 1755.50 | -45.75% | serious | Eligible |
| Qwen3 4B 3-bit | 4858.10 | 48.37 | 10.23 | 2276.88 | -13.77% | serious | Eligible |

The serious end states are retained outcomes of the frozen no-rest workload,
not privacy fields or discarded outliers. Five measured attempts do not
establish general thermal behavior beyond this workload and device.

## Retained Short Interaction failure

Qwen3 0.6B deterministically produced the same response in all six attempts:

> Your note is safe on this iPhone and will sync automatically once you
> reconnect to the network. Let me know if you need further assistance!

The response is concise, states local safety, and mentions synchronization and
connectivity. The frozen `short-interaction-response-v1` lexical policy also
requires one of `return`, `restore`, `available`, `back`, or `again`. None is
present. The App therefore correctly marked all six attempts
`response_conformance_failed`, and the external validator independently made
every candidate metric ineligible because there were zero eligible measured
attempts.

This is a reproducible model-output gate failure. Rerunning until a passing
wording appeared or manually changing the evidence would violate the frozen
contract. The result remains structurally valid and protocol-conformant with
null summary metrics.

## Integrity and privacy review

- The six imported raw files are byte-for-byte identical to the submitted App
  exports.
- SHA-256 digests cover every raw export and deterministic validation report.
- Result IDs, session IDs, filenames, model revisions, and source commit are
  mutually consistent and unique where required.
- Schema validation rejects unrecognized fields; a separate string scan found
  no user name, email address, Apple account, UDID, serial number, vendor
  identifier, device-assigned name, host name, home directory, or local path.
- Generated text is limited to the fixed benchmark prompt response.
- The retained public device model, OS build, battery state, thermal state,
  runtime, and model identities are required technical reproduction metadata.

## Reproducibility decision

F5 passes for its declared single-device, single-runtime matrix:

- all six cells are present and non-placeholder;
- the exact App and benchmark identities are recorded;
- raw evidence is sufficient for the frozen validator to reproduce all metric
  and ineligibility decisions; and
- integrity and privacy checks pass.

The evidence does not prove cross-device, cross-OS, cross-runtime, minimum
device, App Store, battery-life, or broad thermal claims. It remains a release
candidate with `officialResultEligible: false`. The frozen validator continues
to report evidence level `unreviewed` and ranking ineligible; assigning trust,
acceptance, or publication status belongs to F6 governance.

## F6 handoff

F6 may use this package to finalize submission, review, reproduction,
correction, withdrawal, deprecation, release-history, and publication rules.
It must not convert the retained 0.6B Short Interaction failure into a passing
measurement, broaden the evidence claims, or publish/tag 1.0 without explicit
maintainer approval.
