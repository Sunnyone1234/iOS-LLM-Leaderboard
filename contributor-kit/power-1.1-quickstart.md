# Power 1.1 contributor quickstart

This is the current path for adding genuine physical-device evidence to the
live Power ranking.

## What you need

- a Mac with Xcode;
- a physical iPhone connected by cable;
- enough free iPhone storage for the selected model;
- a GitHub fork of this repository.

The official result contract is tied to Benchmark App 0.13.0 build 16 at
source commit `f5b863cc0ca4d82d987cd9779f8875939d7bf90c`. Use a separate worktree so
your contribution branch can remain on current `main`:

```bash
git clone https://github.com/YOUR_GITHUB_HANDLE/iOS-LLM-Leaderboard.git
cd iOS-LLM-Leaderboard
git worktree add ../ios-llm-power-app \
  f5b863cc0ca4d82d987cd9779f8875939d7bf90c
open ../ios-llm-power-app/ios-app/BenchmarkApp/BenchmarkApp.xcodeproj
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

Return to the current repository checkout and create a branch:

```bash
git switch main
git pull --ff-only
git switch -c results/power-DEVICE-MODEL
python3 scripts/power.py submit /path/to/result.json \
  --github YOUR_GITHUB_HANDLE \
  --accept-declarations
```

If applicable, add `--display-name`, `--conflict-category`,
`--conflict-statement`, `--thermal-assistance`, or `--environment-notes`.
`none` is the default conflict category and thermal-assistance value.

The command prints the generated package directory. Validate it:

```bash
python3 scripts/power.py validate \
  submissions/suite-b/power-1.1.0/draft/<submission-id>
```

Review both JSON files, then commit only the package:

```bash
git add submissions/suite-b/power-1.1.0/draft/<submission-id>
git commit -m "Add Power 1.1 result"
git push -u origin results/power-DEVICE-MODEL
```

Open a pull request. The pull-request author must match
`contributor.githubHandle` in `submission.json` (case-insensitive).

## What happens next

CI validates the package and creates a ranking preview. After maintainer review
and merge, valid evidence appears in the live community view. One account
counts once per exact cell; two independent contributors mark the cell as
reproduced. Merge does not modify the frozen Power 1.1 release or automatically
assign Verified status.
