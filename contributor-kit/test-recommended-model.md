# Test a Recommended Power Model

This guide is for the four pinned artifacts in the
[Power model test catalog](../models/power-test-catalog.json). They are
available in App `0.9.0` build `11`, but they have no accepted physical-iPhone
evidence yet. A catalog entry is not a compatibility claim, benchmark result,
or ranking.

Use the existing [Power 1.0 quickstart](power-1.0-quickstart.md) instead when
you want to reproduce one of the published App-0.8.0 Qwen comparison cells.
App version and source commit are part of the exact comparison identity.

## Recommended candidates

- `mlx-community/Llama-3.2-1B-Instruct-4bit`;
- `mlx-community/gemma-3-1b-it-qat-4bit`;
- `mlx-community/granite-3.3-2b-instruct-4bit`;
- `mlx-community/SmolLM3-3B-4bit`.

The catalog pins each exact artifact revision, license source, repository
size, and locked-runtime registry basis. Do not substitute a similarly named
artifact or a newer revision.

## 1. Check out the exact candidate App source

Fork and clone the repository, then create a detached worktree at the source
commit embedded by App 0.9.0:

```bash
git clone https://github.com/YOUR_GITHUB_HANDLE/iOS-LLM-Leaderboard.git
cd iOS-LLM-Leaderboard
git remote add upstream https://github.com/YizeSun/iOS-LLM-Leaderboard.git
git fetch upstream
git worktree add ../ios-llm-power-candidates 002c76ccbfed7b1c8b7c13313b887aaebf610a3e
```

Open:

```text
../ios-llm-power-candidates/ios-app/BenchmarkApp.xcodeproj
```

## 2. Build on a physical iPhone

In Xcode:

1. select your Apple Development team and physical iPhone;
2. open **Product → Scheme → Edit Scheme → Run → Info**;
3. set **Build Configuration** to `Release`;
4. turn off **Debug executable**; and
5. build and install the App.

Before measurement, turn off Low Power Mode, charge above 50%, disconnect
external power, close unnecessary background work, and wait for nominal
thermal state. Simulator runs are useful for App tests but are not Power
benchmark evidence.

## 3. Run one candidate cell

Choose one model marked **Untested** and either frozen Power workload.

1. Tap **Prepare Model**.
2. If preparation downloads the artifact, fully close and relaunch the App.
3. Select the same model and workload, then prepare again until the exact
   cached artifact is verified and loaded.
4. Confirm Release, no debugger, Low Power Mode off, unplugged power, battery
   at least 50%, and nominal thermal state.
5. Tap **Run Benchmark** once and let the fixed warm-up plus five measured
   attempts finish.
6. Tap **Export Raw JSON** and keep the original file unchanged.

Do not rerun to hide a slow, failed, cancelled, OOM, not-run, or
metric-ineligible outcome. If the App produces a raw result, preserve and
submit it. If model preparation fails before a benchmark session can exist,
do not manufacture JSON or measurements; report the exact artifact and App
error separately as a compatibility finding, not as a leaderboard result.

## 4. Package and validate the export

Return to the main checkout, update it, and create a result branch:

```bash
cd ../iOS-LLM-Leaderboard
git switch main
git pull --ff-only upstream main
git switch -c power-result/YOUR_SHORT_DESCRIPTION
```

After reviewing and accepting the seven declarations in the
[Power 1.0 submission definition](../docs/power-benchmark-1.0-submission.md),
create the immutable two-file package:

```bash
python3 scripts/create_suite_b_power_submission.py \
  /path/to/app-export.json \
  --output-root submissions/suite-b/power-1.0.0-rc.1/draft \
  --contributor YOUR_GITHUB_HANDLE \
  --conflict-category none \
  --conflict-statement "No conflict of interest disclosed." \
  --accept-declarations
```

Use the real conflict disclosure when an affiliation exists. Validate the
generated directory:

```bash
python3 scripts/validate_suite_b_power_submission.py \
  submissions/suite-b/power-1.0.0-rc.1/draft/YOUR_SUBMISSION_ID
```

## 5. Open the pull request

Commit only the new package, push it, and open a pull request from the same
GitHub account named in `contributor.githubHandle`:

```bash
git add submissions/suite-b/power-1.0.0-rc.1/draft/YOUR_SUBMISSION_ID
git commit -m "Submit recommended Power model result"
git push -u origin power-result/YOUR_SHORT_DESCRIPTION
gh pr create --web \
  --repo YizeSun/iOS-LLM-Leaderboard \
  --base main \
  --head YOUR_GITHUB_HANDLE:power-result/YOUR_SHORT_DESCRIPTION
```

CI validates package structure, the adopted Power protocol, recalculated raw
evidence, integrity binding, and GitHub-handle match. A valid merged package
creates a live exact comparison cell for that model, App source, runtime,
device, OS, and workload. One account counts once inside that cell; two
independent metric-eligible accounts display as `Reproduced`. The candidate
does not receive a placeholder value while evidence is absent.
