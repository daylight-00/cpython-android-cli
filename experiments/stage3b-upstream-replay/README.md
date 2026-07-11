# Stage 3-B Phase 2: Controlled Upstream Android Replay

> **Status:** ACTIVE
> **Parent scope:** `docs/stages/STAGE3B_PHASE2_SCOPE.md`

## Purpose

Replay the exact CPython source commit identified in Phase 1 through the preserved Android producer model on Victor Linux, without mutating the original source checkout or historical prefixes.

## Step 1: prepare isolated replay state

```sh
git pull --ff-only

bash \
  experiments/stage3b-upstream-replay/prepare-replay.sh
```

Expected marker:

```text
STAGE3B_REPLAY_PREPARE=PASS
```

Preparation performs:

```text
Phase 1 readiness check
exact source commit resolution
detached Git worktree creation
NDK presence check
Android/android.py snapshot equality check
Android/android-env.sh snapshot equality check
separate cross-build root creation
replay-plan.json generation
```

## Step 2: execute producer replay

```sh
bash \
  experiments/stage3b-upstream-replay/run-replay.sh
```

The runner executes the upstream producer graph:

```text
build Python
Android target configure/build/install
package archive creation
replay prefix inventory
selected sysconfig metadata capture
```

Expected final marker:

```text
STAGE3B_UPSTREAM_REPLAY=PASS
```

## Output roots

```text
work/workstation/stage3b-phase2-replay/
results/workstation/stage3b-phase2-replay/
cache/workstation/stage3b-source-deps/
```

Important result files:

```text
replay-plan.json
replay-build.log
replay-build-result.json
replay-output-summary.json
```

## Failure interpretation

Preparation failure means a provenance or producer-model gate is not closed.

Build failure means the controlled Linux replay exposed a producer portability or host-build issue and should be analyzed from `replay-build.log` before changing the producer model.

A successful replay does not yet prove Stage 3-A equivalence. It only creates the clean replay product that later comparison phases will evaluate.
