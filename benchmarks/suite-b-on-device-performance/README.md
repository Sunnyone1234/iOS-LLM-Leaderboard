# Suite B: On-device Performance

Suite B is the active measurement foundation for Power. It measures an exact
model artifact and runtime on a physical Apple device using versioned workloads
and measurement modes.

## Current release

`suite-b-power@1.1.4` is the current compatibility-policy release. Its 1.1.0
source release adopts the frozen Power 1.1 RC1 execution contract, finalizes
the ranking policy, and binds six immutable physical-device results without
rewriting their RC1 source identity. Patch 1.1.1 changes no measurement or
result schema. Patches 1.1.1 through 1.1.4 add and extend an exact
approved-runner policy for community intake. Patch 1.1.4 approves App 0.18.0
build 21 at the exact protected-merge source commit after its submission-path
fixes passed App, intake, identity, and ranking checks.

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
- [Power 1.1 current compatibility release](releases/suite-b-power-1.1.4.json)
- [Power 1.1 source release manifest](releases/suite-b-power-1.1.0.json)
- [Compatible-runner policy](power-1.1-compatible-runners-1.1.4.json)
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
