# Stage 3-C Phase 4: Installation Transaction Prototype

> **Status:** ACTIVE — target evidence pending
> **Input:** frozen Phase 4 Gate 1 contract

## Run

```sh
bash experiments/stage3c-installation-transaction/run-installation-transaction.sh
```

## Isolation

All mutation occurs below:

```text
work/termux/stage3c-phase4-installation-transaction/
```

The canonical promoted prefix, isolated runtime-base source, and live Termux prefix are read-only inputs or remain untouched.

## Scenario gates

```text
fresh runtime/addon composition
exact reinstall NOOP
registered mismatch repair
prerequisite rejection
unowned collision rejection
install rollback after five mutations
uninstall rollback after five mutations
modified-path preservation
unowned sentinel preservation
exact addon and runtime uninstall
retained directory reuse
```

## Checks

```text
scenario runner       61/61
independent verifier  58/58
input mutation        PASS
```

## Expected markers

```text
STAGE3C_PHASE4_TRANSACTION_SCENARIOS=PASS
INSTALLATION_TRANSACTION_ACCEPTED_INPUTS=PASS
INSTALLATION_TRANSACTION_SCENARIOS=61/61 PASS
INSTALLATION_TRANSACTION_VERIFICATION=58/58 PASS
INSTALLATION_TRANSACTION_FRESH_COMPOSITION=2956 PASS
INSTALLATION_TRANSACTION_INSTALL_ROLLBACK=PASS
INSTALLATION_TRANSACTION_UNINSTALL_ROLLBACK=PASS
INSTALLATION_TRANSACTION_SENTINEL_PRESERVATION=PASS
INSTALLATION_TRANSACTION_INPUT_MUTATION_CHECK=PASS
STAGE3C_PHASE4_INSTALLATION_TRANSACTION=PASS
```

## Results

```text
results/termux/stage3c-phase4-installation-transaction/
```

## Upload

```sh
RESULTS="$PWD/results/termux/stage3c-phase4-installation-transaction"
ARCHIVE="$HOME/Downloads/stage3c-phase4-installation-transaction-results-$(date +%Y%m%d-%H%M%S).tgz"

tar czf "$ARCHIVE" "$RESULTS"
printf 'upload: %s\n' "$ARCHIVE"
```

The result includes the self-contained Gate 1 input and can be large.

## Claim boundary

This gate does not claim crash recovery, concurrent lock contention, upgrade/downgrade, or installed runtime smoke.
