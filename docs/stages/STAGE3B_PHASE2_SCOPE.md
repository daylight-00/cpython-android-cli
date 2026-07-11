# Stage 3-B Phase 2 Scope: Controlled Linux Replay of the Android Producer Graph

> **Status:** ACTIVE
> **Input:** Frozen Stage 3-B Phase 1 provenance reconstruction
> **Target:** `aarch64-linux-android`
> **Android API intent:** 24
> **NDK:** 27.3.13750724
> **CPython source:** exact Git identity recovered in Phase 1

## Question

> Can the identified CPython source commit be rebuilt on Victor through the preserved Android producer model using the matched NDK and dependency graph, without mutating historical inputs?

## Replay constraints

The replay must not modify:

```text
original CPython source checkout
historical bootstrap experiment tree
historical CPYTHON_DEV_PREFIX
frozen Stage 2-C runtime prefix
frozen Stage 3-A results
```

The replay uses:

```text
exact source commit
    -> detached Git worktree

preserved Android producer model
    -> source-tree Android/android.py
    -> hash-checked against preserved snapshot

separate cross-build root
    -> work/workstation/stage3b-phase2-replay/cross-build

separate dependency cache
    -> cache/workstation/stage3b-source-deps

separate results root
    -> results/workstation/stage3b-phase2-replay
```

## Preparation gate

Run:

```sh
bash experiments/stage3b-upstream-replay/prepare-replay.sh
```

The preparation step requires:

```text
Phase 1 phase2_ready=true
exact source Git repo and commit available
matching active NDK directory present
Android/android.py matches preserved snapshot
Android/android-env.sh matches preserved snapshot
```

Expected marker:

```text
STAGE3B_REPLAY_PREPARE=PASS
```

The preparation step creates:

```text
results/workstation/stage3b-phase2-replay/replay-plan.json
```

## Replay command path

Run:

```sh
bash experiments/stage3b-upstream-replay/run-replay.sh
```

The runner performs:

```text
Android/android.py build
    -> build Python
    -> target dependency prefix
    -> Android CPython host build
    -> install target prefix

Android/android.py package
    -> packaged replay archive

capture-replay-output.py
    -> inventory and selected sysconfig metadata
```

The effective producer commands are:

```sh
python3 Android/android.py \
  build \
  --cross-build-dir <phase2 cross-build root> \
  --cache-dir <shared dependency cache> \
  aarch64-linux-android

python3 Android/android.py \
  package \
  --cross-build-dir <phase2 cross-build root> \
  aarch64-linux-android
```

## Phase 2 output products

Expected primary build prefix:

```text
work/workstation/stage3b-phase2-replay/
  cross-build/aarch64-linux-android/prefix
```

Expected package product:

```text
work/workstation/stage3b-phase2-replay/
  cross-build/aarch64-linux-android/dist/*.tar.gz
```

Result metadata:

```text
results/workstation/stage3b-phase2-replay/
  replay-plan.json
  replay-build.log
  replay-build-result.json
  replay-output-summary.json
```

## Success conditions for the replay step

```text
[ ] exact source commit detached worktree prepared
[ ] source Android producer scripts match preserved snapshot
[ ] Android SDK root resolved
[ ] active NDK version matches 27.3.13750724
[ ] build Python configured and built
[ ] Android host prefix configured and built
[ ] target prefix installed
[ ] expected Python headers exist
[ ] expected libpython exists
[ ] expected stdlib exists
[ ] package archive produced
[ ] replay output summary captured
```

Expected final marker:

```text
STAGE3B_UPSTREAM_REPLAY=PASS
```

## What Phase 2 does not prove by itself

A successful build does not prove equivalence with Stage 3-A.

After replay, later comparison must examine:

```text
file inventory
ELF inventory
DT_NEEDED graph
unique SONAME set
Android provider classification
extension candidate/import surface
active runtime paths
sysconfig metadata differences
CA behavior
timezone boundary behavior
canonical smoke behavior
whole-prefix relocation behavior
```

Expected producer-host metadata deltas such as Linux build paths or `BUILD_GNU_TYPE` are not failures by themselves.
