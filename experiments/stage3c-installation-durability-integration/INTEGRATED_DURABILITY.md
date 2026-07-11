# Stage 3-C Phase 4: Integrated Durability

> **Status:** ACTIVE — authoritative Termux evidence pending
> **Input:** frozen Phase 4 Gate 5A inventory

## Run

```sh
bash experiments/stage3c-installation-durability-integration/run-integrated-durability.sh
```

## Inputs

```text
Gate 5A scenario       32/32 PASS
Gate 5A verifier       29/29 PASS
Gate 5A result index
  ac11225ae6b45ac45f1e378ecf7bba9cd074a1f779009318e001d5694d89ead8
```

The workflow copies the complete Gate 5A evidence under its result tree and fingerprints it before and after execution.

## Integrated source gate

```text
29/29 checks
```

Required conditions:

```text
exact integrated Git blobs
81 frozen inventory rows retained
67 frozen production rows retained
checkpoint rows retained
no direct mutation primitives in inventoried production functions
all required durability helper calls present
```

## Recovery replay

The unchanged Gate 3 scenario and verifier tools run against the integrated engine:

```text
recovery replay         55/55
recovery verifier       82/82
retained logs            40
snapshot pairs            5
```

## Focused exercises

```text
20/20 checks
16 canonical logs
```

They add successful lifecycle and pre-journal preparation coverage to the frozen crash matrix.

## Integrated traces

The workflow sets:

```text
CPYTHON_ANDROID_CLI_DURABILITY_TRACE_DIR
```

The trace verifier requires 29/29 checks with no ordering violations across journal, registry, payload, backup, rollback, uninstall, and cleanup operations.

## Durability replay

The unchanged Gate 4 scenario and verifier tools run again:

```text
durability replay       64/64
durability verifier     53/53
```

## Overall gate

```text
overall verifier        36/36
input mutation          PASS
```

## Expected markers

```text
INTEGRATED_DURABILITY_ACCEPTED_INPUTS=PASS
INTEGRATED_DURABILITY_SOURCE_INTEGRATION=29/29 PASS
INTEGRATED_DURABILITY_RECOVERY_REPLAY=55/55 PASS
INTEGRATED_DURABILITY_RECOVERY_VERIFICATION=82/82 PASS
INTEGRATED_DURABILITY_DURABILITY_REPLAY=64/64 PASS
INTEGRATED_DURABILITY_DURABILITY_VERIFICATION=53/53 PASS
INTEGRATED_DURABILITY_EXERCISES=20/20 PASS
INTEGRATED_DURABILITY_TRACE_VERIFICATION=29/29 PASS
INTEGRATED_DURABILITY_OVERALL_VERIFICATION=36/36 PASS
INTEGRATED_DURABILITY_INPUT_MUTATION_CHECK=PASS
STAGE3C_PHASE4_INTEGRATED_DURABILITY=PASS
```

## Results

```text
results/termux/stage3c-phase4-integrated-durability/
```

## Upload

```sh
RESULTS="$PWD/results/termux/stage3c-phase4-integrated-durability"
ARCHIVE="$HOME/Downloads/stage3c-phase4-integrated-durability-results-$(date +%Y%m%d-%H%M%S).tgz"

tar czf "$ARCHIVE" "$RESULTS"
printf 'upload: %s\n' "$ARCHIVE"
```

The result contains self-contained Gate 5A, Gate 4, Gate 3, Gate 2, and contract evidence and can be large.

## Claim boundary

A PASS proves integrated source mapping, frozen behavioral replay, frozen durability replay, and observed ordered sync traces for exercised paths. It does not prove actual sudden-power-loss persistence, kernel panic, storage-controller failure, or interruption inside one filesystem primitive.
