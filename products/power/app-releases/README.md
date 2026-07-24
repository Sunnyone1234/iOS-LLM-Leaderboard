# Power App releases

This directory owns immutable identities for distributed Power benchmark Apps.
It does not own Runner measurement behavior or Apple signing teams.

`candidate.json` records the reviewed pre-activation identity. It binds the
Official version/build, Bundle ID, complete App component
manifest SHA-256, embedded measurement-stack SHA-256, and the Runner
certificate it may support.

A candidate is not installable authority. The supported build 4 release record
was issued only after its Runner certificate was active, generic iOS builds
passed, and the exact Official physical-device rehearsal was reviewed. The
release record is pinned by `products/power/current.json`. Prior Official
build 2 rehearsals remain retained audit evidence. Personal Team IDs never
enter this directory.

The only issuance operation is `python3 scripts/repoctl.py activate-power`.
It reviews the exact raw result and renders the retained evidence, immutable
release record, active pointer, and registry together. The command is a dry
run unless `--write` is explicit; merge atomicity prevents a supported App
release and public intake from diverging.

The supported Official release may create public result-only pull requests.
Any App, stack, or Runner digest change requires a new versioned candidate,
exact review, and immutable release; it cannot mutate this release.
