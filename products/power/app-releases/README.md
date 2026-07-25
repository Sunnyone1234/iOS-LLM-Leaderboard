# Power App releases

This directory owns immutable identities for distributed Power benchmark Apps.
It does not own Runner measurement behavior or Apple signing teams.

`candidate.json` records the reviewed pre-activation identity. It binds the
Official version/build, Bundle ID, complete App component
manifest SHA-256, embedded measurement-stack SHA-256, and the Runner
certificate it may support.

A candidate is not installable authority. The supported build 5 release record
was issued only after its Runner certificate was active, generic iOS builds
passed, and the exact Official physical-device rehearsal was reviewed. The
release record is pinned by `products/power/current.json`. Prior supported
build 4 and Official build 2 evidence remain retained audit history. Personal
Team IDs never enter this directory.

Subsequent issuance uses
`python3 scripts/repoctl.py activate-power-next EXACT_RESULT.json`. It reviews
the exact raw result and renders the retained evidence, immutable release
record, active pointer, completed release plan, and registry together. The
command is a dry run unless `--write` is explicit; merge atomicity prevents a
supported App release and public intake from diverging. The original
`activate-power` command is retained only to audit the one-time initial
activation.

The supported Official release may create public result-only pull requests.
Any App, stack, or Runner digest change requires a new versioned candidate,
exact review, and immutable release; it cannot mutate this release.

The most recently completed cycle is retained under `candidates/` and
`next.json`. Official build 5 is bound to the rc.2 stack and
`power2-runner-ac490be49347`. Its replacement App component manifest
`a9b1c359…` was frozen before testing; generic build and exact physical-device
rehearsal both passed, and the reviewed result activated that same source
without recompilation. Candidate rehearsal permission remains a local,
ignored build setting and is not compiled into the hashed lifecycle-neutral
source.

The prior `bf5362…` candidate passed its physical rehearsal, but compiled
candidate lifecycle state would have kept submission closed after activation.
Its raw `656CF217…` result, passing review, old component snapshot, and
supersession link are retained under
`evidence/656cf217-8ef5-4ccd-bb18-cb34062d4b7c/`. They remain explicitly
non-publishable and non-ranking. Neither candidate is a supported public
release; only the replacement `a9b1c359…` identity became supported when
`current.json` advanced atomically.
