# Contribute a Power 1.0 Result

This is the shortest supported path from a physical-iPhone benchmark run to a
reviewable pull request. It preserves the frozen Power 1.0 measurement
identity and does not upload Apple ID, serial number, UDID, device name, or
personal prompts.

## What you need

- a Mac with Xcode;
- a physical iPhone with at least 50% battery;
- a room thermostat or thermometer for the required ambient reading;
- enough free space for the selected pinned model;
- a GitHub account and a fork of this repository; and
- GitHub CLI (`gh`) for the commands below, or equivalent GitHub web actions.

One genuine result is useful. You do not need to run every model or both
workloads. Failed, OOM, cancelled, not-run, and metric-ineligible outcomes are
retained evidence and must not be hidden by rerunning for a better number.

## 1. Prepare the repository and frozen App source

Fork `YizeSun/iOS-LLM-Leaderboard`, clone your fork, and enter the checkout.
Keep `main` available for packaging and create a detached worktree at the exact
Power 1.0 reference-App source commit:

```bash
git clone https://github.com/YOUR_GITHUB_HANDLE/iOS-LLM-Leaderboard.git
cd iOS-LLM-Leaderboard
git remote add upstream https://github.com/YizeSun/iOS-LLM-Leaderboard.git
git fetch upstream
git worktree add ../ios-llm-power-app 2f105ff463bc9b281b19655ba711b1ca7dee8759
```

Building from this exact worktree matters: the App embeds its checkout commit,
and that identity is part of the exact comparison cell.

## 2. Build on the physical iPhone

Open:

```text
../ios-llm-power-app/ios-app/BenchmarkApp.xcodeproj
```

In Xcode:

1. select your Apple Development team and physical iPhone;
2. open **Product → Scheme → Edit Scheme → Run → Info**;
3. set **Build Configuration** to `Release`;
4. turn off **Debug executable**; and
5. build and install the App.

Before measurement, turn off Low Power Mode, charge above 50%, disconnect
external power, close unnecessary background work, and wait for the App to
report nominal thermal state.

For evidence captured on or after 2026-07-14, also follow the
[environmental control addendum](../benchmarks/suite-b-on-device-performance/power-1.0-environment-control.md):
use a 20.0–25.0 °C indoor room, remove the case and thermally relevant
accessories, place the phone screen-up on a dry room-temperature non-metal
tabletop, use no external cooling or heating, and keep the device nominal in
that setup for five minutes before starting.

## 3. Run one locked benchmark cell

Choose one pinned model and one workload in the App.

1. Tap **Prepare Model**.
2. If the model was downloaded, fully close and relaunch the App.
3. Select the same model and workload, then prepare again until the cached
   artifact is verified.
4. Confirm Release, no debugger, Low Power Mode off, unplugged power, battery
   at least 50%, and nominal thermal state.
5. Record the ambient temperature and confirm the environmental setup before
   tapping **Run Benchmark**.
6. Tap **Run Benchmark** once and allow the fixed warm-up plus five measured
   attempts to finish.
7. Record the ambient temperature again, then tap **Export Raw JSON** and save
   the original file without editing it.

Do not use the historical **Export Submission JSON** action for Power 1.0.

## 4. Create the immutable submission package

Return to the main checkout, update it, and create a contribution branch:

```bash
cd ../iOS-LLM-Leaderboard
git switch main
git pull --ff-only upstream main
git switch -c power-result/YOUR_SHORT_DESCRIPTION
```

Review the seven declarations in the
[frozen package definition](../docs/power-benchmark-1.0-submission.md). If they
are all true, create the two-file package from the untouched export:

```bash
python3 scripts/create_suite_b_power_submission.py \
  /path/to/app-export.json \
  --output-root submissions/suite-b/power-1.0.0-rc.1/draft \
  --contributor YOUR_GITHUB_HANDLE \
  --conflict-category none \
  --conflict-statement "No conflict of interest disclosed." \
  --accept-declarations
```

Use the real conflict category and statement if an affiliation exists. The
command prints the new package directory. Validate that exact directory:

```bash
python3 scripts/validate_suite_b_power_submission.py \
  submissions/suite-b/power-1.0.0-rc.1/draft/YOUR_SUBMISSION_ID
```

## 5. Open the pull request

Commit only the new package, push it to your fork, and open the pull request as
the same GitHub account declared in `contributor.githubHandle`:

```bash
git add submissions/suite-b/power-1.0.0-rc.1/draft/YOUR_SUBMISSION_ID
git commit -m "Submit Power result"
git push -u origin power-result/YOUR_SHORT_DESCRIPTION
gh pr create --web \
  --repo YizeSun/iOS-LLM-Leaderboard \
  --base main \
  --head YOUR_GITHUB_HANDLE:power-result/YOUR_SHORT_DESCRIPTION
```

Select **Power 1.0 Draft package (adopted RC1 contract)** in the pull-request
checklist. CI validates the package, protocol, raw-evidence calculations,
integrity binding, and GitHub-handle match.

Complete the environmental declaration in the pull-request template for every
post-addendum result. CI does not read a room thermometer and therefore cannot
verify those conditions automatically; a maintainer reviews the declaration
before merge.

## What happens after merge

- the immutable Power 1.0 release and its tag remain unchanged;
- the valid package enters the separately labeled live community view;
- the same GitHub account counts once inside the same exact comparison cell;
- that account may contribute to any number of other cells;
- two independent metric-eligible accounts display as `Reproduced`; and
- three or more enable contributor-weighted community aggregation.

See the live [coverage report](../results/suite-b-power-community/COVERAGE.md)
to find cells that still need independent evidence. A result from a different
physical iPhone model or OS build creates new coverage rather than being
silently mixed with an incompatible cell.
