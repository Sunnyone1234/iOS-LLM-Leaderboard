# Power 1.1 contributor quickstart

This is the current path for adding genuine physical-device evidence to the
live Power ranking.

## What you need

- a Mac with Xcode;
- a physical iPhone connected by cable;
- enough free iPhone storage for the selected model;
- a GitHub fork of this repository.

The frozen reference remains Benchmark App 0.13.0 build 16 at source commit
`f5b863cc0ca4d82d987cd9779f8875939d7bf90c`. Current compatibility policy
1.1.4 preserves Benchmark App 0.16.0 build 19 and both approved Benchmark App
0.17.0 build 20 identities, then approves Benchmark App 0.18.0 build 21 at
protected-merge commit `8920a423f4b4abff4e34a2d8a128a3962899258e`. The App embeds the latest commit
that changed `ios-app/`, so repository documentation and ranking updates do not
silently change its runner identity.

For a new run, build the current `main` checkout and verify the App displays
version 0.18.0 and shows **Approved for Power 1.1.4**:

```bash
git clone https://github.com/YOUR_GITHUB_HANDLE/iOS-LLM-Leaderboard.git
cd iOS-LLM-Leaderboard
open ios-app/BenchmarkApp.xcodeproj
```

## Run one exact cell

1. In Xcode, select your connected iPhone and run the Release app.
2. In the App, select **one model only**.
3. Download and prepare it while the phone is connected to power if needed.
4. Fully close and relaunch the App after any download.
5. Remove the cable for measurement and satisfy the App preflight checks.
6. Run one workload. Let the session finish without switching apps.
7. Share or save the exported JSON.

Do not manually edit the export. The result records the exact device, OS,
model artifact, runtime, workload, attempts, memory, and thermal state.

Normal tabletop, stand, handheld, or cased use is acceptable when accurately
observed by the App. Do not deliberately cool or heat the phone for an ordinary
ranking run. Assisted runs can still be submitted if disclosed, but they are
kept outside the ordinary live ranking.

## Create the pull-request package

If the App build has direct GitHub submission configured, open the **Results**
tab after a completed result, select the result, review the disclosures, accept
the declarations, and tap **Submit to GitHub**. The App uses GitHub's device flow,
creates the current two-file package without rewriting `result.json`, commits
it to a contributor-owned fork, and opens the PR. The access token stays in the
submission session and is not written into the evidence package.

Direct submission does not relax runner identity. A development App whose
version, build, source commit, or runtime differs from every entry in the
versioned compatibility policy is rejected as `runner_incompatible`; it cannot
be made eligible by App-side packaging, a second contributor, or maintainer
review.

## Run and submit more than one result

App 0.18.0 saves every completed or safely recovered Power result as a separate
immutable JSON file in its Documents `PowerBenchmarkResults` directory. An App
launch validates all saved files, selects the newest one by default, and shows
the collection in the **Results** tab. Selecting an older entry changes
only the result displayed, shared, or submitted; it does not recalculate or
rewrite that result.

After a successful upload, the local JSON remains on the iPhone. To run the
same model/workload again, tap **Prepare Model**, wait for preparation, then tap
**Run Benchmark**. The new result receives a new result/session identity, is
saved separately, and becomes the selected result. To change model identity,
select the model and fully relaunch when the process-isolation notice requires
it; then prepare and run. Changing workload does not transform any previously
saved result.

To upload an older result, choose it in the **Results** tab, confirm its
result ID and runner line, accept the declarations again, and tap **Submit to
GitHub**. The declaration and current submission state reset when selection
changes. Do not submit the same saved result twice: duplicate raw SHA-256,
result ID, or session ID is rejected. Use **Share Raw Power JSON** to keep an
external backup; uninstalling the App removes its iOS sandbox and local
history.

App 0.18.0 requires a configured GitHub OAuth Client ID for the supported
submission route. A development build without that configuration may still
share the untouched raw JSON as a backup, but it cannot create the contributor
manifest or PR. Do not send an App 0.18.0 result through the retained
`scripts/power.py` command: that command is an immutable Power 1.1.1 asset and
correctly rejects runners added by later policies. Configure the public Client ID
and rebuild the App instead.

The older CLI remains available only for exact App 0.13.0/App 0.16.0 runner
identities already covered by its pinned policy. The pull-request author must
always match `contributor.githubHandle` in `submission.json`
(case-insensitive).

## What happens next

CI validates and classifies the package as automatic acceptance, manual review,
or rejection, and creates a ranking preview. A clean evidence-only PR is
squash-merged after the repository's required checks; disclosed conflicts or
thermal assistance require maintainer review. After merge, valid evidence
appears in the live community view. One account
counts once per exact cell; two independent contributors mark the cell as
reproduced. Merge does not modify the frozen Power 1.1 release or automatically
assign Verified status.
