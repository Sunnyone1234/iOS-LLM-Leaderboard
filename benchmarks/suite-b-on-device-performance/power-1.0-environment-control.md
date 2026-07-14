# Power 1.0 Environmental Control Addendum

## Status and compatibility

This is a normative intake addendum for new Power 1.0 community evidence
captured on or after **2026-07-14**. It closes an environmental-control gap in
the frozen Power 1.0 execution contract without changing:

- `suite-b-power@1.0.0` or its signed release assets;
- the adopted `suite-b-power@1.0.0-rc.1` protocol identity;
- workload IDs, prompts, generation settings, metrics, or eligibility math;
- the Power result or submission schemas;
- the reference App; or
- previously published Maintainer Reference evidence.

The original result JSON does not contain ambient-temperature or placement
fields. Until a future schema version can carry them, the pull request is the
public declaration record and maintainer review is the enforcement boundary.
Passing the frozen JSON validators alone does not establish conformance with
this addendum.

Normative requirements use **must**. A result that misses a requirement remains
valuable retained evidence, but new community evidence is not eligible for the
live ranking unless every requirement below is declared and reviewable.

## Controlled environment

For every Power workload session, the contributor must:

1. run indoors with ambient temperature between **20.0 °C and 25.0 °C** at
   both session start and session end;
2. read ambient temperature from a room thermostat or a thermometer located
   in the same room and no more than 1 m from the iPhone;
3. remove the case, MagSafe accessories, and any other attached accessory that
   can materially change heat transfer;
4. place the iPhone screen-up, stationary, and uncovered on a dry,
   room-temperature, non-metal tabletop such as wood or laminate;
5. leave the iPhone unheld and untouched from request start through the final
   attempt, except when the App explicitly requires an interaction;
6. keep the device on battery power and satisfy every existing Power 1.0
   admission rule; and
7. begin only after the iPhone has remained in this setup with
   `ProcessInfo.thermalState == nominal` for at least five consecutive minutes.

Ordinary room heating or air conditioning is allowed only when it controls the
room generally and is not directed at the iPhone.

## Prohibited thermal assistance

The following are prohibited before and during the stabilization period and
measurement session:

- ice, cold packs, refrigerated or frozen objects, chilled food or drink,
  wet towels, and refrigerators or freezers;
- fans or air-conditioning vents aimed at the iPhone;
- powered phone coolers, cooling plates, laptop cooling pads, external
  heatsinks, or other equipment intended to remove heat from the device;
- metal, stone, glass, or another deliberately thermally conductive support
  used to improve cooling; and
- direct sunlight, heaters, warming pads, or any other deliberate external
  heating.

The goal is to measure the retail iPhone in an ordinary controlled indoor
environment, not the best result obtainable with an undeclared cooling setup.

## Required pull-request declaration

For each submitted result, the pull request must record:

- ambient temperature at session start and end, in degrees Celsius;
- whether the reading came from a room thermostat or nearby thermometer;
- confirmation that the case and thermally relevant accessories were removed;
- confirmation that the device was stationary, screen-up, and unheld on the
  permitted support surface;
- confirmation that no prohibited cooling or heating was used; and
- confirmation that the five-minute nominal stabilization completed.

Approximate or inferred device temperature is not a substitute for the ambient
reading. `ProcessInfo.thermalState` remains the only in-App thermal-state
evidence and must not be converted into degrees Celsius.

If a session spans more than one exported workload result, the same declaration
may cover those results only when they were collected consecutively without
changing the environment or device setup. Each result must still be identified
unambiguously in the pull request.

## Admission and historical evidence

For evidence captured on or after the effective date:

- missing declarations make environmental conformance **unreviewed**;
- a declared violation makes the result environment-ineligible for the live
  ranking; and
- a compliant declaration does not override any other protocol, metric, trust,
  or ranking requirement.

Power 1.0 evidence captured before this addendum remains published with its
existing status. Because ambient temperature, placement, case use, and external
thermal assistance were not recorded in the frozen schema, those historical
results must not be described as conforming to this addendum unless separate
contemporaneous evidence exists. They are not retroactively invalidated.

