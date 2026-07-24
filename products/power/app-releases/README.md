# Power App releases

This directory owns immutable identities for distributed Power benchmark Apps.
It does not own Runner measurement behavior or Apple signing teams.

`candidate.json` is generated from the closed Power migration pointer. It
binds the future Official version/build, Bundle ID, complete App component
manifest SHA-256, embedded measurement-stack SHA-256, and the Runner
certificate it may support.

The candidate is not installable authority. A supported release record is
issued only after its Runner certificate is active, generic iOS builds pass,
and the exact Official physical-device rehearsal is reviewed. The Runner
certificate is active and the build 4 generic build gate passes. Prior
Official build 2 end-to-end rehearsals remain retained audit evidence; the
exact Official build 4 physical-device result is still pending. Immutable App
release issuance and public intake activation remain pending. Personal Team
IDs never enter this directory.

The only issuance operation is `python3 scripts/repoctl.py activate-power`.
It reviews the exact raw result and renders the retained evidence, immutable
release record, active pointer, and registry together. The command is a dry
run unless `--write` is explicit; merge atomicity prevents a supported App
release and public intake from diverging.

The exact Official candidate may measure and create a result-only rehearsal
pull request, but trusted CI cannot publish or rank it while public intake is
closed. Any App, stack, or Runner digest change resets the affected generated
verification state and requires a new exact review.
