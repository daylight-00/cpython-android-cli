# Stage 3-C Phase 4 Integrated Durability Result

> **Status:** PASS — Gate 5B closed
> **Target:** Termux on Android arm64
> **Result archive:** `stage3c-phase4-integrated-durability-results-20260712-082135.tgz`

## Archive identity

```text
sha256
  76bb78f200d9836d96f677cc1eca1e2f1483186f3655efa17a8e1f2361bd0187

size
  23,917,838 bytes

members
  325

regular files
  300

directories
  25

symlinks / hardlinks / special entries
  0 / 0 / 0

unsafe member names
  0
```

## Result index

```text
sha256
  878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce

indexed files
  294

independent hash, size, and mode mismatches
  0
```

## Machine verdict

```text
source integration             29/29 PASS
recovery replay                55/55 PASS
recovery independent verifier  82/82 PASS
durability replay              64/64 PASS
durability verifier            53/53 PASS
focused exercises              20/20 PASS
integrated trace verifier      29/29 PASS
overall verifier               36/36 PASS
workflow return codes          all 0
failed checks                  []
```

```text
STAGE3C_PHASE4_INTEGRATED_DURABILITY=PASS
```

## Integrated source identities

```text
recovery_common.py
  3183ba0861ef45e7a395201bec0085f3f69fb248

recovery_operations.py
  8a307065e00fd7a7332541f4911c5478945374ee

recovery_engine.py
  aebf5b9a33d163f7f8758f785ca621c94c0e478b

recovery_durability.py
  61bfb859f73acccb0dfcce1d2a630bfd1ffc2d3f
```

The target source-integration verifier retained all 81 frozen Gate 5A rows, all 67 production rows, both checkpoint rows, and reported no direct production mutation violations or missing helper mappings.

## Recovery replay

The unchanged Gate 3 scenario and verifier tools passed against the integrated engine:

```text
scenario checks              55/55
independent checks           82/82
canonical scenario logs      40/40
snapshot pairs                 5
```

Observed crash exits and recovery:

```text
PREPARED
  exit 90
  rollback restored 0

INTENT
  exit 93
  rollback restored 0

install APPLYING
  exit 91
  rollback restored 5

uninstall APPLYING
  exit 91
  rollback restored 5

registry-applied pre-commit repair
  exit 91
  rollback restored 2

COMMITTED before cleanup
  exit 92
  recovery FINALIZED_COMMIT

lock contender
  installation lock busy
  no mutation

repeated ROLLED_BACK recovery
  NOOP_ROLLED_BACK
```

## Focused integrated exercises

```text
fresh runtime install
  create 714
  mutations 715
  verify 714 owned paths

directory mode repair
  NOOP 713
  repair-dir 1

symlink repair
  NOOP 713
  repair 1

development-addon install
  create 454
  verify 1168 owned paths

development-addon uninstall
  preserved []
  verify 714 owned paths

unjournaled preparation
  DISCARDED_PREPARE

runtime-base uninstall
  preserved []
  empty registry

fresh registry-applied pre-commit crash
  exit 91
  rollback restored 715
  empty registry
```

## Integrated trace evidence

```text
trace files
  25

events
  42,941

canonical JSONL
  PASS

PID anchoring
  PASS

ordering violations
  0
```

Operations:

```text
OPEN_TEMP       4,845
COPY_TEMP       3,294
WRITE_TEMP      1,551
FSYNC_FILE      4,848
REPLACE         4,861
FSYNC_DIR      14,916
SYMLINK_TEMP       16
MOVE            1,117
MKDIR             327
CHMOD               1
FSYNC_PATH           1
UNLINK           6,638
RMDIR              526
```

Independently reconstructed valid sequences:

```text
atomic file publication   4,845
symlink publication          16
move                       1,117
mkdir                        327
chmod                          1
unlink                     6,638
rmdir                        526
```

Required labels for journal, registry, regular and symlink payload publication, backup moves, uninstall, rollback, unjournaled preparation, and COMMITTED cleanup were all present.

## Durability protocol replay

The unchanged Gate 4 tools passed again:

```text
scenario checks              64/64
independent checks           53/53
positive traces                7
transaction events            27
negative controls               2
```

## Input mutation controls

```text
Gate 5A input
  entries 187 / 187
  fingerprint
    858bd9d2b713ad2adb97a8881d2104db9a14a8aacfd2e7e534c51ac4cbf8f30e

Gate 3 recovery input
  entries 87 / 87
  fingerprint
    5abf67d8e4d8b23ce569b61aba8ce1e96e69d6c894afcb7e6078ef9842d59d0a

Gate 4 durability input
  entries 150 / 150
  fingerprint
    af7b64f51fb8d7f21d206dc3683507e9155aa117d77378c0d63125422887f3d6
```

All three controls passed.

## Canonical evidence boundary

All Gate 5B generated JSON and JSONL evidence was canonical. One inherited Phase 2 `product-lock.json` retains its older serialization and remains outside the generated-evidence canonicalization claim.

## Closed claim

The exact integrated source set resolves the frozen Gate 5A production inventory, preserves the complete Gate 3 recovery behavior, preserves the complete Gate 4 durability protocol, and emits correctly ordered file and directory sync traces for every exercised production path.

## Claim boundary

This result does not prove persistence across actual sudden power loss, kernel panic, storage-controller failure, write-cache loss, or interruption inside one filesystem primitive. Those physical-failure claims remain outside Stage 3-C Phase 4.
