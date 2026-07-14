# Power 1.0 Environmental Observation Draft

## Status and compatibility

This document defines observation-first intake guidance for new Power 1.0
community evidence. It does not change:

- `suite-b-power@1.0.0` or its signed release assets;
- the adopted `suite-b-power@1.0.0-rc.1` protocol identity;
- workload IDs, prompts, generation settings, metrics, or eligibility math;
- the Power result or submission schemas;
- the reference App; or
- previously published or submitted evidence.

The current result JSON does not contain ambient-temperature, device-surface,
case, placement, or thermal-assistance fields. For now, these observations live
in the pull request and are reviewed as contributor declarations. This draft
does not make temperature or case metadata a prerequisite for ranking.

The existing frozen admission rules remain unchanged. In particular, a
measurement must begin with `ProcessInfo.thermalState == nominal`, along with
the existing battery, power, build, debugger, cache, and device checks.

## Recommended observations

Contributors are encouraged to record the following immediately before a
session and, when practical, again after it:

- ambient room temperature in degrees Celsius and the reading source;
- externally measured device-surface temperature in degrees Celsius;
- the surface-temperature method, measurement location, and timing;
- case state: `installed`, `removed`, or `unknown`;
- placement: `tabletop`, `stand`, `handheld`, `other`, or `unknown`; and
- any environmental detail likely to affect heat transfer.

No ambient-temperature range is required. A case does not have to be removed,
and no particular ordinary support material or fixed stabilization duration is
required. Missing recommended observations should be shown as `not recorded`;
they do not by themselves make a result ineligible.

## What temperature can mean

`ProcessInfo.thermalState` is categorical system evidence: `nominal`, `fair`,
`serious`, or `critical`. It is not a temperature sensor reading and must never
be converted into degrees Celsius.

The public benchmark App has no supported API for exact iPhone internal
temperature. A contributor may optionally report a surface temperature from
an external instrument, but must label it as surface temperature and include:

- instrument or method;
- measurement location, such as back center;
- whether the case was installed; and
- whether the reading was taken before or after the workload.

An infrared, contact, or other surface reading is useful context, but it is not
an internal battery, SoC, or enclosure temperature.

## Thermal-assistance disclosure

Every new pull request seeking ordinary live-ranking placement must disclose
one of these values:

- `none`;
- `deliberate-cooling`;
- `deliberate-heating`;
- `other-assisted`; or
- `unknown`.

Ordinary room heating or air conditioning that is not directed at the iPhone
is `none`. Deliberate thermal assistance includes ice, chilled objects, fans or
vents aimed at the phone, powered phone coolers, heating pads, and deliberately
heated or cooled supports.

The current two-file package has no machine-readable field for this
declaration, and the live-ranking generator cannot separate assisted evidence
after merge. Therefore, only a declaration of `none` may be merged into the
ordinary live intake under this draft. Assisted and unresolved `unknown`
submissions remain reviewable in their pull requests but are not merged into
`main`. An `unknown` declaration may be clarified before merge. A future schema
may support retained, separately labeled environmental classes; this draft
does not add one.

The project relies on transparent contributor disclosure and maintainer review.
It does not require App Attest, a persistent device identifier, photographs, or
other anti-fraud hardware evidence.

## Pull-request record

For each result, the pull request should identify:

- result ID;
- thermal-assistance disclosure; and
- any available recommended observations listed above.

One observation block may cover consecutive exported workloads only when the
environment and device setup did not change and every covered result ID is
listed. The untouched App export remains the measurement record; these notes do
not authorize editing `result.json` or adding a third package file.

## Ranking and historical evidence

- Temperature, case, and placement observations are context only in this
  draft. They are not exact-cell keys, aggregation inputs, or hard admission
  gates.
- Ordinary live-intake merge requires a thermal-assistance declaration of
  `none`. Assisted or unresolved `unknown` evidence remains reviewable in its
  pull request until a separately labeled intake path exists.
- An observation does not override any protocol, metric, trust, or ranking
  requirement.
- Historical results are not retroactively invalidated. Missing observations
  are simply `not recorded` unless contemporaneous evidence exists.

Any future decision to require a temperature method, temperature range, case
state, or placement must use a separately reviewed protocol/schema migration.
It must not silently reinterpret existing Power 1.0 evidence.
