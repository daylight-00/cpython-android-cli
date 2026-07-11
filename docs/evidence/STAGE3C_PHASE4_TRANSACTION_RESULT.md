# Stage 3-C Phase 4 Installation Transaction Result

> **Status:** PASS — Gate 2 isolated transaction execution closed
> **Target:** Termux on Android arm64
> **Result archive:** `stage3c-phase4-installation-transaction-results-20260711-230729.tgz`

## Result archive identity

```text
sha256
  9ea7379263711c8501d674e78e25d29ccd1764db30497c5dc2414030d378c005

size
  22,322,682 bytes

members
  88

regular files
  77

directories
  11

unsafe member names
  0

special archive entries
  0
```

## Machine result

```text
transaction scenarios       61/61 PASS
independent verifier        58/58 PASS
workflow return codes        all 0
failed checks                    []
```

```text
STAGE3C_PHASE4_TRANSACTION_SCENARIOS=PASS
STAGE3C_PHASE4_INSTALLATION_TRANSACTION=PASS
```

## Result index

```text
sha256
  0041f1c3c73dc7a62291b6c3b244ac885d9bad6799d4115280febc20f61384da

indexed files
  75

independent hash, size, and mode mismatches
  0
```

## Fresh composition

```text
runtime-base install
  create 714
  registry 714

development-addon install
  create 454

test-addon install
  create 1788

composed registry
  artifacts 3
  owned paths 2956
  bad paths 0
```

## Same-version lifecycle

```text
runtime-base exact reinstall
  NOOP 714
  mutations 0

registered runtime corruption
  detected path bin/python3.14

repair
  NOOP 713
  repair 1
  mutations 2

post-repair registry
  owned paths 2956
  bad paths 0
```

## Preflight rejection

Runtime-base uninstall was rejected while addons remained installed:

```text
dependent addons installed
mutation
  none
```

An unowned required leaf was rejected before mutation:

```text
path
  bin/python3.14

error
  unowned collision bin/python3.14

registry created
  false

sentinel sha256
  e6edbfd5475588dd2f8dd20437dfc9718c237693d7ddfa6f09bfaa6a97e5b339
```

A development addon without runtime-base was also rejected before mutation:

```text
error
  prerequisite not installed

registry created
  false
```

## Synchronous rollback execution

Test-addon uninstall failure injection:

```text
injected after mutations
  5

journal state
  ROLLED_BACK

post-rollback registry
  artifacts 3
  owned paths 2956
  bad paths 0
```

Development-addon install failure injection:

```text
injected after mutations
  5

journal state
  ROLLED_BACK

post-rollback registry
  artifacts 1
  owned paths 714
  bad paths 0
```

The independently fingerprinted installation states before failure and after rollback are exact matches in both cases.

## Uninstall and preservation

A locally modified test path was preserved and reported:

```text
path
  lib/python3.14/__phello__/__init__.py

sha256
  ad5b93b7eb42dbb3fe7f6c03bda593042363ca51ecc44428afa91905e6525722

registered after uninstall
  false
```

An unowned sentinel was preserved:

```text
path
  lib/python3.14/unowned-sentinel.txt

sha256
  71c601a6dcad1963d55d338cd15c5c05c13f6f3bf94324c8970ea93f997ee656

registered
  false
```

Lifecycle order:

```text
test-addon uninstall          registry 1168
development-addon uninstall   registry 714
runtime-base uninstall        registry 0
```

Runtime uninstall retained the nonempty exact directory paths:

```text
lib
lib/python3.14
```

Runtime reinstall then proved exact-directory reuse without descendant adoption:

```text
create      712
reuse-dir     2
registry    714
bad paths     0
```

The modified test leaf and unowned sentinel remained outside the runtime registry.

## Final state

```text
primary final registry owned paths
  714

primary final registry sha256
  4fb42e5ceeabb4eb8a6c321b88446ccc67a1153bd3a4dafb9279b506b39b04d8

primary final installation fingerprint
  e7614a2317ed3e697ba6b41bd6f227ae0b766ff5b69826de2d4841a6e8758514

registry mode
  0600

lock mode
  0600
```

## Input mutation

```text
input entries before/after
  40 / 40

input fingerprint before/after
  c45b416b2834eb656c3b6efaf3c8a014514e57afb74eb1cb784692729be703db

special paths
  0
```

## Closed claims

This result proves the tested isolated fresh composition, dependency and collision preflight, exact reinstall no-op, registered repair, synchronous install and uninstall rollback, exact artifact uninstall, locally modified path preservation, unowned sentinel preservation, and retained-directory reuse behavior.

## Claim boundary

This result does not prove recovery after abrupt process termination, concurrent lock contention, upgrade or downgrade, kernel or power-loss durability, parent-directory fsync, or installed runtime behavior. Those begin in Gate 3 and later phases.
