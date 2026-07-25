# Power product

Power measures one exact model artifact and runtime configuration on a
physical Apple device under a versioned Program and Target.

The first active stack contains:

- Product: `power`
- Program: `text-generation-performance@2.0.0-draft.2`
- Target: `apple-iphone-physical@1.0.0-draft.1`
- Model Catalog: four exact MLX artifacts selected only for new reruns

`current.json` is the only public pointer. It pins a separate
measurement-stack manifest, active Runner certificate, supported App release,
and retained activation evidence. The App embeds the measurement-stack digest,
not the digest of a pointer that contains the App itself.

The Runner certificate binds every measurement-affecting Swift
component plus the canonical runtime identity and retained physical
Certification evidence. The immutable App release binds the complete App
component manifest, exact stack, Official bundle identity, and supported
Runner certificate.

The automated suite, generic iOS configurations, Runner
physical-device smoke, exact Official build 5 rehearsal, and raw-result review
pass for the recorded digests. The immutable App release and `current.json`
were issued atomically, so public intake is open. Prior candidates and
Official build 2 and build 4 releases remain retained audit history; superseded
rehearsals remain explicitly non-publishable.

`candidate.json` remains the pre-activation audit surface. Any future stack,
Runner, or App digest change requires a new versioned candidate and release;
it cannot silently modify the active pointer.

Power 1.1 files are not dependencies of this product tree.
