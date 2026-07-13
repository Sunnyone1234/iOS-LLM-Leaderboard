# Power Benchmark 1.0 Migration Rules

## Non-promotion rule

Historical Pilot and Foundation results are immutable evidence. They must not
be relabeled, edited in place, or promoted to Power 1.0 results.

| Historical identity | Power 1.0 candidate mapping | Migration decision |
| --- | --- | --- |
| `b-ux-001-short-interaction@0.2.0-pilot` | `b-ux-001-short-interaction@1.0.0-rc.1` | rerun required |
| `b-pipe-001-sustained-generation@0.2.0-pilot` | `b-pipe-001-sustained-generation@1.0.0-rc.1` | rerun required |
| `suite-b-result-bundle-0.3` | F3 result contract | historical validation only |
| `suite-b-result-bundle-0.4` | F3 result contract | development evidence only; rerun required |

The workload IDs remain stable because the scenarios remain the same. Their
versions change because official-candidate outcome taxonomy, raw evidence,
per-metric eligibility, aggregation, and release identity are materially
different.

Existing validators continue to validate historical bytes against their
original schema. A historical result may be displayed in a clearly labeled
Pilot or Foundation evidence view, but it may not enter a Power 1.0 comparison
group. Recalculation from old evidence does not change this rule.

There is no automatic converter. A contributor must run the F4-compatible
reference App against the frozen F3 release identity and submit a new bundle.
