# Suite B: On-device Performance

Suite B is the active measurement foundation for Power. It measures an exact
model artifact and runtime on a physical Apple device using versioned workloads
and measurement modes.

## Current release

`suite-b-power@1.1.0` is published. It adopts the frozen Power 1.1 RC1
execution contract, finalizes the ranking policy, and binds six immutable
physical-device results without rewriting their RC1 source identity.

The only active workloads are:

- `b-ux-001-short-interaction@1.1.0-rc.1`;
- `b-pipe-001-sustained-generation@1.1.0-rc.1`.

Every compatible attempt can retain TTFT, prefill, decode, memory, thermal,
token, behavior, and terminal-outcome evidence. These are metrics and
observations, not separate benchmark tasks.

`b-pipe-002-input-length-sweep` and `b-ux-002-context-assistance` remain
Experimental. Historical Pilot, Framework v1, Power 1.0, draft, and RC assets
remain under their original identities for audit and reproduction.

## Start here

- [Short public method](../../docs/power.md)
- [Power 1.1 final release manifest](releases/suite-b-power-1.1.0.json)
- [Frozen RC1 protocol](power-1.1-rc1-protocol.md)
- [Final ranking policy](power-1.1-ranking-policy.json)
- [Metrics](metrics.md)
- [Workload manifests](workloads/)
- [Release history](releases/RELEASE-HISTORY.md)
- [Power 1.1 results](../../results/suite-b-power-1.1/LEADERBOARD.md)

The unversioned `power-1.1-protocol.md` is a retained draft and is not the
public or normative current-method link.

Validate workload manifests with:

```bash
python3 scripts/validate_suite_b_workload.py \
  benchmarks/suite-b-on-device-performance/workloads/*.json
```

The five `suite-b-on-device-performance-00x-*.md` files are Framework v1
metric-task drafts retained for migration history. Do not use them for a new
official submission.
