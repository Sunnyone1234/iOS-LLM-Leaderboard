# Git History Authorship Correction — 2026-07-14

## Purpose

Two commits were imported from mail patches whose `From` headers incorrectly
identified the author as `Codex <codex@openai.com>`. The repository maintainer
confirmed that this was not a valid contributor attribution. On 2026-07-14,
the Author fields of those two commits were corrected to
`Yize Sun <martin.yize.sun@gmail.com>`.

| Original commit | Corrected equivalent | Unchanged tree |
| --- | --- | --- |
| `4b65078212509978e153f4dcbf6cb055f2787118` | `e9a785b2faede4b0913b6b846ac6deab45e913f0` | `7f20900a4b371b1903b14385300ec140a636f8c1` |
| `3e596d509b2a7b9bc6b7e826d370d62c28611a46` | `da2d7392bd829726f2c6fdb19cfa9b298a9c9db2` | `fb9d18fe45045a71b37629c64512b695fae99494` |

Because a Git commit includes its parent commit IDs, correcting these Author
fields changed the IDs of every descendant even when its files did not change.
The complete translation is recorded in
[`2026-07-14-commit-map.tsv`](2026-07-14-commit-map.tsv).

## Evidence preservation

The correction did not modify a benchmark protocol, app implementation,
schema, result, measurement, ranking rule, or other historical file content.
A mechanical audit compared all 90 mapped commits and confirmed identical tree
objects, parent topology, commit messages, dates, and committer identities. The
only Author changes were the two listed above.

Raw benchmark exports intentionally retain their original `appSourceCommit`
values. Those values describe what the App recorded at measurement time and
must not be rewritten. Resolve the currently used evidence SHAs as follows:

| Recorded `appSourceCommit` | Corrected equivalent | Unchanged tree |
| --- | --- | --- |
| `2f105ff463bc9b281b19655ba711b1ca7dee8759` | `d7fcff7e27b4c46b1121df8988a0b2fb76d56804` | `6c15ea47b35a980997f62e659df082a28f66075a` |
| `07a79186a701afee93d3ae8d8dd77a7b50b702ae` | `f676981e508d007694850125eca139aee32043ce` | `7980cceaf3946edd4e3582e2d733c8c76096d50d` |
| `c8b1f7bc404e9b506aa5d7d5f9e7d8b7978271be` | `c06cc31388bb6f60349154ad5c99e278bf1e3dcb` | `2d50d4d6f8e7dc3bb90b54101f7949a5dde7821f` |

The machine-readable summary is
[`2026-07-14-history-correction.json`](2026-07-14-history-correction.json).

## Public refs and releases

The active branches and annotated release tags were retargeted to their
content-equivalent rewritten commits. The release names, release notes, and
repository files were preserved. Cryptographic signatures attached to old
commit objects cannot remain valid after any commit-object rewrite; the
original objects are retained in the maintainer's verified offline backup.

| Ref | Original target | Content-equivalent target |
| --- | --- | --- |
| `main` before the remediation record | `66034b506c8a0dbaa79922251d5a7c0b6c5344ba` | `5e5d1a4f949f57f1d667f157e6ac63fab76d3a0b` |
| `codex/power-benchmark-app-lab` | `ac086f505fd199b84d226ccf598019dc628eebf1` | `00bff5161bd8def350ab3f93f87bdaaf1b760c2e` |
| `codex/recommended-model-catalog` | `0607d7375edd6996ba18a5580fa7c544f9bb7c6f` | `5ed418f014c4640d73510af93a570d5cfeb646ed` |
| tag `1.0.0` target | `f0381df16abff108b56a674eb1541c73b3d11629` | `4f1fe77864e285295dc271c3f3b203a17331ec0f` |
| tag `ship-1.0.0` target | `d5d3d7ad389984181d01a29b55015b41f6e61f20` | `a09a91d248d0a56304342a775a9ad7cbed317aa0` |

The full-map SHA-256 is
`84ea489473b0fecca3d4bf7df4d55e3573ebe6f77fc8e6068ef9f5a7017220b6`.
The pre-rewrite all-refs backup bundle SHA-256 is
`10fce161db96450f408b3316d789f783aa721ca839bf05aac941bac38987b399`.
