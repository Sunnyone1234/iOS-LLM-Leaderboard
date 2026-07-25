# Applications and certified runners

`apps/` is the MIT-licensed implementation plane for benchmark applications
and runner components.

Owner: App and runner maintainers.

Lifecycle:

- source modules evolve through ordinary code review;
- released App identities and runner component digests are retained;
- a measurement-affecting change requires a new runner certificate;
- UI-only changes may reuse an existing certificate when its support record
  permits that App release.

This root is necessary because the Target model is not limited to one
iPhone App. Shared shell, evidence, runner, Program, Target, and Runtime
components must remain separately reviewable as iPad and macOS Targets are
added. `ios-app/` is retained historical Power 1.1 source; it is not the public
App or an active compatibility path.

Current Power 2 contents:

- `PowerRunnerKit/` — Power 2 evidence, Runner Core, text Program Module,
  Apple iPhone Target Adapter, and fixed-dependency MLX Runtime Adapter;
- `PowerAppKit/` — exact-byte result persistence, interrupted-run checkpoints,
  remote current-release preflight, two-file packaging, and GitHub submission;
- `ios/` — the active iOS App Shell with Test and Results tabs, generated
  identities/catalog, local-signing boundary, and explicit Developer,
  Certification, and Official source configurations.

The active immutable Runner certificate and App release remain under
`products/power/`. Editing measurement or App source does not mutate them; it
starts a new certificate/App-release candidate.
