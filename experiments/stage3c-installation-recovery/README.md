# Stage 3-C Phase 4: Installation Recovery and Lock Contention

> **Status:** ACTIVE — target evidence pending
> **Input:** frozen Phase 4 Gate 2 transaction result

## Run

```sh
bash experiments/stage3c-installation-recovery/run-installation-recovery.sh
```

## Isolation

All mutable installation roots remain below:

```text
work/termux/stage3c-phase4-installation-recovery/
```

The canonical promoted prefix, runtime-base source, live Termux prefix, and copied Gate 2 input are not transaction targets.

## Recovery checkpoints

```text
PREPARED before the first mutation
INTENT recorded before an individual mutation
APPLIED recorded after an individual mutation
registry APPLIED before COMMITTED
COMMITTED before cleanup
ROLLED_BACK retained journal
```

Crash injection terminates a separate process with `os._exit`; no exception handler or in-process rollback runs.

## Lock contention

```text
holder process
  exclusive flock

nonblocking contender
  installation lock busy
  no mutation

post-release contender
  development-addon install PASS
```

## Scenario gates

```text
PREPARED recovery
INTENT-window recovery
APPLYING install recovery
APPLYING uninstall recovery
registry-applied pre-commit recovery
COMMITTED cleanup finalization
ROLLED_BACK recovery idempotence
nonblocking lock rejection
post-release install
```

## Checks

```text
scenario runner       55/55
independent verifier  82/82
input mutation        PASS
scenario logs         40
```

## Expected markers

```text
STAGE3C_PHASE4_RECOVERY_SCENARIOS=PASS
INSTALLATION_RECOVERY_ACCEPTED_INPUTS=PASS
INSTALLATION_RECOVERY_SCENARIOS=55/55 PASS
INSTALLATION_RECOVERY_VERIFICATION=82/82 PASS
INSTALLATION_RECOVERY_PREPARED=PASS
INSTALLATION_RECOVERY_INTENT=PASS
INSTALLATION_RECOVERY_APPLYING=PASS
INSTALLATION_RECOVERY_REGISTRY_PRECOMMIT=PASS
INSTALLATION_RECOVERY_COMMITTED_CLEANUP=PASS
INSTALLATION_RECOVERY_LOCK_CONTENTION=PASS
INSTALLATION_RECOVERY_INPUT_MUTATION_CHECK=PASS
STAGE3C_PHASE4_INSTALLATION_RECOVERY=PASS
```

## Results

```text
results/termux/stage3c-phase4-installation-recovery/
```

## Upload

```sh
RESULTS="$PWD/results/termux/stage3c-phase4-installation-recovery"
ARCHIVE="$HOME/Downloads/stage3c-phase4-installation-recovery-results-$(date +%Y%m%d-%H%M%S).tgz"

tar czf "$ARCHIVE" "$RESULTS"
printf 'upload: %s\n' "$ARCHIVE"
```

The bundle contains the self-contained Gate 2 result, including the three frozen Phase 3 archives, and can be large.

## Claim boundary

A PASS does not prove power-loss durability, parent-directory fsync, crashes inside an individual non-atomic filesystem primitive, adversarial mutation, fairness, upgrade/downgrade, or installed runtime behavior.
