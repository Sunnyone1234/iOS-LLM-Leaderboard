# Power 1.1 RC1 Physical-Device Review

## Status

The frozen three-model, two-workload matrix is complete. All six unmodified
App exports are structurally valid, protocol-conformant, bound to the exact
reference App, and accepted by the independent report consumer for RC review.

This review does **not** authorize publication, ranking, recommendation,
tagging, or official-result adoption. Power 1.0 remains the active public
release until the final Power 1.1 policy, regenerated reports, maintainer
declarations, and explicit publication authorization are complete.

## Frozen execution identity

- Device: `iPhone15,3` (iPhone 14 Pro Max)
- OS: iOS `26.5.2`, build `23F84`
- Reference App: `0.13.0` build `16`
- App source: `f5b863cc0ca4d82d987cd9779f8875939d7bf90c`
- Runner: `ios-reference-benchmark-app@0.13.0`
- Runtime: MLX Swift LM `3.31.4@bd4b7434e6bdb588c7ef55706ff8904cb7fd4c57`
- Backend: MLX/Metal
- Protocol: `suite-b-power@1.1.0-rc.1`
- Result schema: `suite-b-power-result-1.1.0-rc.1`
- Validation report: `suite-b-power-validation-report-1.1.0-rc.1`

Every session began unplugged, in Release configuration, without a debugger,
with Low Power Mode disabled and the system thermal state nominal. Battery was
65% for the 0.6B and 1.7B sessions and 60% for the 4B sessions.

## Evidence matrix

| Artifact / workload | Result | Behavior | Metric eligibility | RC review |
| --- | --- | --- | --- | --- |
| Qwen3 0.6B 4-bit / Short Interaction | [`21B5F28F`](raw/2026-07-15T15-25-48Z_b-ux-001-short-interaction_mlx-community-qwen3-0.6b-4bit_iphone15-3_21b5f28f.json) · [report](validation/2026-07-15T15-25-48Z_b-ux-001-short-interaction_mlx-community-qwen3-0.6b-4bit_iphone15-3_21b5f28f.validation.json) | `not_verified` | 6 of 6 metrics | accepted |
| Qwen3 0.6B 4-bit / Sustained Generation | [`8C10D75C`](raw/2026-07-15T15-30-51Z_b-pipe-001-sustained-generation_mlx-community-qwen3-0.6b-4bit_iphone15-3_8c10d75c.json) · [report](validation/2026-07-15T15-30-51Z_b-pipe-001-sustained-generation_mlx-community-qwen3-0.6b-4bit_iphone15-3_8c10d75c.validation.json) | not applicable | 5 of 5 metrics | accepted |
| Qwen3 1.7B 4-bit / Short Interaction | [`169EBB65`](raw/2026-07-15T15-41-21Z_b-ux-001-short-interaction_mlx-community-qwen3-1.7b-4bit_iphone15-3_169ebb65.json) · [report](validation/2026-07-15T15-41-21Z_b-ux-001-short-interaction_mlx-community-qwen3-1.7b-4bit_iphone15-3_169ebb65.validation.json) | `verified` | 6 of 6 metrics | accepted |
| Qwen3 1.7B 4-bit / Sustained Generation | [`4784FF6E`](raw/2026-07-15T15-44-46Z_b-pipe-001-sustained-generation_mlx-community-qwen3-1.7b-4bit_iphone15-3_4784ff6e.json) · [report](validation/2026-07-15T15-44-46Z_b-pipe-001-sustained-generation_mlx-community-qwen3-1.7b-4bit_iphone15-3_4784ff6e.validation.json) | not applicable | 5 of 5 metrics | accepted |
| Qwen3 4B 3-bit / Short Interaction | [`E357D4E7`](raw/2026-07-15T15-48-56Z_b-ux-001-short-interaction_mlx-community-qwen3-4b-3bit_iphone15-3_e357d4e7.json) · [report](validation/2026-07-15T15-48-56Z_b-ux-001-short-interaction_mlx-community-qwen3-4b-3bit_iphone15-3_e357d4e7.validation.json) | `verified` | 6 of 6 metrics | accepted |
| Qwen3 4B 3-bit / Sustained Generation | [`167679D8`](raw/2026-07-15T15-56-24Z_b-pipe-001-sustained-generation_mlx-community-qwen3-4b-3bit_iphone15-3_167679d8.json) · [report](validation/2026-07-15T15-56-24Z_b-pipe-001-sustained-generation_mlx-community-qwen3-4b-3bit_iphone15-3_167679d8.validation.json) | not applicable | 5 of 5 metrics | accepted |

All result IDs and session IDs are unique. The artifacts use the three exact
revisions pinned by the RC manifest. Every session contains one warm-up and
five measured attempts; no measured attempt failed, was cancelled, ran out of
memory, or was omitted.

## Observed values

These values describe the accepted RC evidence. They are not a public ranking
and do not imply that Power 1.1 is released.

### Short Interaction

| Artifact | Proxy TTFT | Pipeline TTFT | Prefill | Decode | Footprint | Completion |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen3 0.6B 4-bit | 183.09 ms | 181.72 ms | 385.40 tok/s | 104.94 tok/s | 473.39 MiB | 446.24 ms |
| Qwen3 1.7B 4-bit | 487.73 ms | 484.78 ms | 144.47 tok/s | 41.33 tok/s | 1098.10 MiB | 1299.46 ms |
| Qwen3 4B 3-bit | 1137.58 ms | 1133.06 ms | 61.79 tok/s | 20.99 tok/s | 1883.39 MiB | 2821.79 ms |

### Sustained Generation

| Artifact | Decode | Pipeline TTFT | Prefill | Footprint | First-to-last change | End thermal |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3 0.6B 4-bit | 96.84 tok/s | 454.12 ms | 517.69 tok/s | 803.08 MiB | +0.08% | nominal |
| Qwen3 1.7B 4-bit | 40.97 tok/s | 1239.75 ms | 189.59 tok/s | 1474.92 MiB | -37.84% | serious |
| Qwen3 4B 3-bit | 9.82 tok/s | 4889.43 ms | 48.06 tok/s | 2372.78 MiB | -45.66% | serious |

The 1.7B and 4B sustained sessions ended at `serious` thermal state. Their
attempts and degradation metrics remain eligible under the frozen protocol and
are retained without rerunning or selecting a more favorable session.

## Behavior and performance separation

The 0.6B Short Interaction response is semantically relevant but does not meet
the frozen automatic behavior-verification rule, so its behavior status is
`not_verified`. Its six performance metrics remain eligible. The 1.7B and 4B
Short Interaction responses are behavior-verified. Behavior is not applicable
to the pipeline workload.

RC1 itself authorizes neither measured-performance ranking nor recommendations.
The final release must regenerate reports under a new `1.1.0` policy; it must
not reinterpret these RC report booleans in place.

## Integrity and privacy review

- [`CHECKSUMS.sha256`](CHECKSUMS.sha256) covers all six raw exports and all six
  validation reports.
- Each report stores the exact result ID and SHA-256 digest, and every
  result/report pair passes the fail-closed consumer.
- Raw files are byte-for-byte copies of the received App exports.
- No account name, local filesystem path, email address, phone number, UDID,
  serial number, persistent device identifier, or unrelated personal content
  was found. Public model output and `iPhone15,3` device metadata are expected.
- Earlier source-mismatched attempts remain documented in
  [`INTAKE-2026-07-15.md`](INTAKE-2026-07-15.md) and are not part of this matrix.

## Known limitations

- Coverage is one physical `iPhone15,3`, one OS build, one MLX Swift runtime,
  and three artifacts from one model family.
- First-renderable proxy TTFT is an adapter-boundary observation, not a display
  frame or screen-paint measurement.
- Five measured attempts do not establish battery life or long-duration
  thermal stability.
- Exact ambient temperature, device-surface temperature, case state, and
  placement are not fields in the frozen result schema and were not recorded
  in the App exports.
- `ProcessInfo.thermalState` is categorical and must not be treated as a
  temperature measurement.
- Behavior verification is deliberately separate from metric eligibility; a
  `not_verified` behavior status is neither a protocol failure nor a verified
  recommendation.
- The benchmark does not establish minimum supported hardware, behavior on
  untested runtimes, model quality outside these workloads, or App Store
  approval.
- License metadata is informational and not legal advice.

## Remaining release gates

Before official Power 1.1 publication, the maintainer must confirm contributor
declarations, conflict disclosure, and thermal-assistance disclosure; approve
the exact evidence and checksums; review the final `1.1.0` policy and regenerated
reports; and explicitly authorize merge, official-result adoption, ranking,
tagging, GitHub Release publication, and leaderboard deployment.
