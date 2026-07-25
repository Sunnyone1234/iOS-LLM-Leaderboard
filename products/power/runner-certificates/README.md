# Power runner certificates

The first Power 2.0 Runner certificate was
`power2-runner-87f62feecc2b.json`. It binds the exact Runner components,
runtime identity, text Program, physical-iPhone Target, release-candidate
measurement stack, and runner-certification policy.

The certificate was issued from the retained closed Certification evidence in
`evidence/b5d3c2cf-b2b8-4060-b00d-048102e6cfb9/`. That directory preserves the
raw physical-iPhone result byte-for-byte, its review report, and the exact App
component-manifest snapshot that produced it. The evidence and certificate
remain non-publishable and non-ranking; they establish measurement trust only.

`candidate.json` remains the generated certification audit surface. It records
the current Runner component identity, automated checks, the retained physical
review, and the active certificate reference. All checks pass only for the
exact digests recorded by the generator checkpoint. Changing the stack or
Runner identity creates a new candidate and requires new certification rather
than mutating this certificate.

An active Runner certificate does not release the App or open public intake.
The next closed gate is an end-to-end physical rehearsal of the exact Official
App release candidate.

The subsequent release cycle issued
`power2-runner-ac490be49347.json` from the retained result and review under
`evidence/83ecb818-e1f7-4118-80c9-1df9e6fbe8fe/`. It is bound to rc.2 and
Official build 5 through the completed `products/power/next.json` plan. The
atomic activation made it the certificate authorized by the public
`products/power/current.json`; the first certificate remains immutable
release history.

Power 1.1 compatible-runner records are not imported.
