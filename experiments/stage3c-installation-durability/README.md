# Stage 3-C Phase 4: Installation Durability Protocol

> **Status:** ACTIVE — target evidence pending
> **Input:** frozen Phase 4 Gate 3 recovery result

## Run

```sh
bash experiments/stage3c-installation-durability/run-installation-durability.sh
```

## Isolation

All mutable files remain below:

```text
work/termux/stage3c-phase4-installation-durability/
```

The copied Gate 3 result is treated as immutable input and fingerprinted before and after execution.

## Capability gates

```text
regular-file fsync
directory fsync
O_DIRECTORY support
same-filesystem work layout
```

## Primitive traces

```text
atomic create
atomic replace
mkdir
move between two directories
unlink
rmdir
transaction ordering
```

Atomic replacement requires:

```text
OPEN_TEMP
WRITE_TEMP
FSYNC_FILE
REPLACE
FSYNC_DIR(target parent)
```

Namespace mutations require the affected parent directory to be synced.

## Transaction ordering

```text
journal PREPARED
payload
journal APPLYING/APPLIED
registry
journal COMMITTED
backup cleanup
```

Each journal, payload, and registry replacement uses the complete atomic-replacement sequence.

## Negative controls

```text
missing target-parent fsync
registry declared before payload
```

Both invalid traces must be rejected.

## Checks

```text
scenario runner       64/64
independent verifier  53/53
positive traces         7
transaction events     27
input mutation        PASS
```

## Expected markers

```text
STAGE3C_PHASE4_DURABILITY_SCENARIOS=PASS
INSTALLATION_DURABILITY_ACCEPTED_INPUTS=PASS
INSTALLATION_DURABILITY_SCENARIOS=64/64 PASS
INSTALLATION_DURABILITY_VERIFICATION=53/53 PASS
INSTALLATION_DURABILITY_REGULAR_FSYNC=PASS
INSTALLATION_DURABILITY_DIRECTORY_FSYNC=PASS
INSTALLATION_DURABILITY_ATOMIC_REPLACE=PASS
INSTALLATION_DURABILITY_PARENT_FSYNC=PASS
INSTALLATION_DURABILITY_TRANSACTION_ORDER=PASS
INSTALLATION_DURABILITY_NEGATIVE_CONTROLS=PASS
INSTALLATION_DURABILITY_INPUT_MUTATION_CHECK=PASS
STAGE3C_PHASE4_INSTALLATION_DURABILITY=PASS
```

## Results

```text
results/termux/stage3c-phase4-installation-durability/
```

## Upload

```sh
RESULTS="$PWD/results/termux/stage3c-phase4-installation-durability"
ARCHIVE="$HOME/Downloads/stage3c-phase4-installation-durability-results-$(date +%Y%m%d-%H%M%S).tgz"

tar czf "$ARCHIVE" "$RESULTS"
printf 'upload: %s\n' "$ARCHIVE"
```

The bundle contains the self-contained Gate 3 evidence and can be large.

## Claim boundary

A PASS proves successful tested `fsync` operations and declared ordering on the target filesystem. It does not prove persistence after actual sudden power loss, kernel panic, controller failure, or a crash inside one filesystem primitive. It also does not prove that the complete recovery engine has already been migrated to these durability helpers.
