# Stage 3-C Phase 5 Gate 3C Target Implementation Result

> **Status:** READY FOR TERMUX — authoritative target archive pending

## Result

The repository now contains the single-wrapper target implementation for the frozen 50-scenario Gate 3C addon lifecycle and dependency-enforcement matrix.

```text
scenario groups
  preflight rejection       10
  composition and repair    10
  addon uninstall            9
  crash recovery            12
  lock exclusion             2
  behavior/final audit       7
  total                     50
```

This is an implementation readiness result, not target acceptance.

## Input authority

The wrapper requires the exact historical Gate 3B archive and does not regenerate or recompress it.

```text
Gate 3B archive sha256
  0be850523ddc9b0fcb652d47f4414d0772dea1d8767f23490c3655576683270b

Gate 3B root result-index sha256
  f3e0bd34c61f5b1e0960d002175478b112641fa71f0e914ec712e6c514e52fe9

installation contract index sha256
  79e3c173639047bc23b7dbe3c2135abe8f0b868d787735c094cbe06749c7dde3

manifest index sha256
  540adfaacf9387e80a258dfa3db8c299ad775d99e771c475a89dfc61de6868c1

matrix sha256
  52c622450e9664c6738a75fbc947b809cf1f4766e61b04a68a1a8dcc24b6c14a
```

The runner independently reopens the accepted Gate 3B index, scenario summary, verifier, workflow status, wrapper status, contract, manifests, and artifact archives before creating any scenario state.

## Execution model

```text
one Termux wrapper
fresh extraction of accepted authority
inode-separated scenario roots
actual corrected transaction engine
raw stdout and stderr
real process return codes
canonical per-scenario JSON
independent result verifier
root result-index
new .tar.zst evidence on PASS or FAIL
```

The external user wrapper also downloads the authority archive when absent, verifies its SHA-256, applies the repository patch, runs the target workflow synchronously, and uploads the resulting archive and checksum.

## Recovery retention clarification

The implementation preserves the already accepted engine behavior.

```text
PREPARED / late APPLYING
  recover exact prior payload and registry
  persist one ROLLED_BACK audit tombstone
  second recovery reports NOOP_ROLLED_BACK

COMMITTED
  finalize exact new payload and registry
  clean the transaction
  second recovery observes zero transactions
```

The earlier design sentence requiring zero residual transactions for every recovery boundary was too broad. Zero transaction residue remains mandatory for normal successful lifecycle roots and committed recovery; it is not imposed on the frozen rollback audit tombstone. No engine code is changed by this clarification.

## Functional surface

Target execution must prove:

```text
include/python3.14/Python.h while development-addon is installed
import test.support while test-addon is installed
python -m test -j1 test_json test_hashlib
absence of test payload after test-addon removal
absence of development payload after development-addon removal
runtime HTTPS and uv production smoke
81 ELF / 329 DT_NEEDED / 0 unresolved
67/67 extension imports
final runtime registry 1 artifact / 714 owned paths
```

## Files

```text
experiments/stage3c-installed-runtime-lifecycle/gate3c_addon_lifecycle_support.py
experiments/stage3c-installed-runtime-lifecycle/run-gate3c-addon-lifecycle.py
experiments/stage3c-installed-runtime-lifecycle/verify-gate3c-addon-lifecycle.py
experiments/stage3c-installed-runtime-lifecycle/run-gate3c-addon-lifecycle-termux.sh
```

## Development validation

The implementation was exercised locally against the exact Gate 3B contract and artifacts with durability fsync shortcuts enabled only for development speed. Android executables were not treated as runnable on the Linux/x86 development host.

```text
authority verification       PASS
seed construction            PASS
clone separation             50/50 PASS
preflight                     10/10 PASS
composition and repair        10/10 PASS
addon uninstall                9/9 PASS
crash recovery                12/12 PASS
lock exclusion                 2/2 PASS
non-executable behavior        4/4 PASS
executable-independent total  47/47 PASS
local executable behavior      3 target-only / intentionally not accepted
independent verifier surface  102 checks
```

The three target-only checks are `import test.support`, selected CPython regression tests, and the complete runtime HTTPS/uv/closure/extension regression. Their absence from local acceptance is deliberate and must be closed only by the Termux archive.

## Claim boundary

This result proves repository implementation readiness only. It does not prove the target addon lifecycle, close Gate 3C, or claim Gate 3D final runtime-base uninstall, upgrade, or downgrade. Gate 3C can close only after a complete Termux `.tar.zst` archive is independently checked for safety, root-index identity, scenario evidence, verifier output, and raw process consistency.
