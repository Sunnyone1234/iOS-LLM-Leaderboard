# Project structure and growth policy

This policy keeps a rigorous benchmark from becoming difficult to understand
or contribute to.

## Four layers

| Layer | Audience | Canonical paths | Rule |
| --- | --- | --- | --- |
| Public surface | Developers and new contributors | `README.md`, website, `contributor-kit/`, current guides | One current answer and one current workflow per subject |
| Normative standard | Implementers and reviewers | `benchmarks/`, `schemas/`, `methodology/` | Versioned, reviewable, and immutable once pinned |
| Evidence | Auditors and ranking generators | `results/`, `submissions/` | Preserve raw bytes, failures, hashes, provenance, and generated derivatives |
| Maintenance | Project maintainers | `scripts/`, `tests/`, `.github/` | Automate validation without becoming a second product surface |

Complexity is acceptable in the normative and evidence layers when it protects
reproducibility. It must not leak into the contributor entry path.

## Stable top-level map

Do not add a new top-level directory unless none of these owns the content:

- `benchmarks/` — suite specifications and release contracts;
- `contributor-kit/` — the current short contribution path plus clearly
  labeled historical guides;
- `docs/` — product, governance, current methods, and retained decisions;
- `examples/` — focused integration recipes;
- `ios-app/` — official benchmark runner;
- `methodology/` — cross-suite benchmark conventions;
- `models/` — model catalogs and compatibility metadata;
- `results/` — raw and generated evidence by release;
- `schemas/` — machine-readable contracts;
- `scripts/` — validators and deterministic generators;
- `site/` — website code;
- `submissions/` — contributor-owned packages;
- `tests/` — regression tests.

A pull request proposing a new top-level directory must document its owner,
lifecycle, license, and why an existing path is insufficient.

## Rules that prevent growth from becoming bloat

1. **One current public guide.** Update it instead of adding `new`, `final`,
   `v2`, or `latest` copies. Versioned historical records may remain, but they
   are de-indexed from the public path.
2. **One public command per product.** Power contributors use
   `scripts/power.py`. Release-specific tools may remain internal and are
   indexed in `scripts/README.md`.
3. **No duplicate deploy pipelines.** Only one workflow may deploy GitHub
   Pages.
4. **Generated outputs have one source.** A generated file identifies its
   generator and is checked in only when the website or release consumes it.
5. **Pinned assets are immutable.** A new contract receives a new version and
   path. Do not silently repair a released asset.
6. **Drafts are not public truth.** Draft protocols and research notes must say
   `Draft` and must not be the homepage methodology link.
7. **Failures remain evidence.** Simplifying navigation never deletes raw
   failed, OOM, cancelled, or ineligible attempts from a released evidence set.
8. **A–E stay navigable, not equally active.** Suite A/C are Build Research,
   Suite B is active Power, Suite D is future Power quality, and Suite E is
   future Ship evidence.
9. **No speculative infrastructure.** Do not add a runner, schema, workflow,
   or website view for an unapproved benchmark category.
10. **Every new public file removes ambiguity.** If it creates a second answer
    to “what is current?” it must replace or explicitly archive the old answer.

## Review checklist for structural changes

- Does the homepage remain understandable without reading historical docs?
- Can a new result contributor reach a working command in two clicks?
- Is the normative source distinct from the short public explanation?
- Is an existing stable ID, raw result, checksum, or release manifest changed?
- Does the change introduce a second workflow, deploy job, or current guide?
- Are A–E roles still complete and accurately labeled?
- Do tests guard the public links and single-deploy rule?

Repository size is not the main metric. The goal is low cognitive load at the
entrance and complete evidence behind every claim.
