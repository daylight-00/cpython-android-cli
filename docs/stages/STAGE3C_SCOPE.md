# Stage 3-C Scope: Distribution Archive and Installation Contract

> **Status:** ACTIVE — Phases 1–4 frozen; Phase 5 Gate 1 active
> **Primary target:** Termux on Android arm64
> **Python baseline:** CPython 3.14.6

## Stage question

> What archive and installation contract allows downstream tools to inspect, verify, stage, install, repair, recover, remove, relocate, and execute the runtime without project-specific knowledge or unsafe ownership assumptions?

## Phase roadmap

```text
Phase 1  product roles and isolated component validation     FROZEN
Phase 2  ownership, shared namespace, and manifests          FROZEN
Phase 3  reproducible archive serialization                  FROZEN
Phase 4  installation registry, recovery, and durability     FROZEN
Phase 5  installed runtime and lifecycle validation          ACTIVE
```

## Frozen Phase 1 — product semantics

```text
canonical entries          3155
canonical fingerprint      5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c
runtime-base entries        714
runtime-base fingerprint    9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796
native closure              81 ELF / 329 edges / unresolved 0
extension imports           67/67
isolated relocation         PASS
```

```text
docs/stages/STAGE3C_PHASE1_FINAL.md
```

## Frozen Phase 2 — ownership and manifests

```text
runtime-base owned paths        714
development-addon owned paths   454
test-addon owned paths         1788
selected total                 2956
unsupported GUI excluded        199
exact owned overlap               0
shared structural directories     2
```

Manifest index:

```text
540adfaacf9387e80a258dfa3db8c299ad775d99e771c475a89dfc61de6868c1
```

```text
docs/stages/STAGE3C_PHASE2_FINAL.md
```

## Frozen Phase 3 — deterministic archives

```text
runtime-base archive
  2ba7c309b1700926dc423eb4305a9eba1a53c023a11617e490b151be71e49743
development-addon archive
  f77ea24c92fdd982cd32e172b2d38134f1d785b1f106d1bfe36a9bffa9cc8eea
test-addon archive
  02a1fad1af5528a4e910f0eb3370f4a2696da4f78067586e8b62f2a10fb4c9b1

builder                    31/31 PASS
extraction preflight       28/28 PASS
archive verifier           76/76 PASS
safe staging extraction      3/3 PASS
```

Frozen serialization:

```text
POSIX pax tar + gzip level 9
mtime 0
uid/gid 0/0
empty owner names
exact member order
hardlinks and special entries forbidden
```

```text
docs/stages/STAGE3C_PHASE3_FINAL.md
```

## Frozen Phase 4 — installation transactions

### Gate 1 contract

```text
contract derivation       54/54 PASS
independent verifier      59/59 PASS
registered ownership       2956
structural references         4
contract index
  79e3c173639047bc23b7dbe3c2135abe8f0b868d787735c094cbe06749c7dde3
```

### Gate 2 isolated lifecycle

```text
scenario runner       61/61 PASS
independent verifier  58/58 PASS
result-index
  0041f1c3c73dc7a62291b6c3b244ac885d9bad6799d4115280febc20f61384da
```

### Gate 3 recovery and lock

```text
scenario runner       55/55 PASS
independent verifier  82/82 PASS
result-index
  f5ba124ebb9752b45d60f027474a399adf61fc5db033c1165a79664cbfc743bd
```

### Gate 4 durability protocol

```text
scenario runner       64/64 PASS
independent verifier  53/53 PASS
result-index
  3cb7e83eb6dc6c186a36da512ed41cbba4566abfc4bd4f5f71766ea1fcf075c4
```

### Gate 5A production inventory

```text
inventory scenario       32/32 PASS
independent verifier     29/29 PASS
all rows                     81
production rows              67
UNKNOWN                       0
result-index
  ac11225ae6b45ac45f1e378ecf7bba9cd074a1f779009318e001d5694d89ead8
```

### Gate 5B integrated durability

```text
source integration             29/29 PASS
recovery replay                55/55 PASS
recovery verifier              82/82 PASS
durability replay              64/64 PASS
durability verifier            53/53 PASS
focused exercises              20/20 PASS
trace verifier                 29/29 PASS
overall verifier               36/36 PASS
result-index
  878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce
```

Accepted Phase 4 final archive:

```text
stage3c-phase4-integrated-durability-results-20260712-082135.tgz
sha256
  76bb78f200d9836d96f677cc1eca1e2f1483186f3655efa17a8e1f2361bd0187
```

```text
docs/stages/STAGE3C_PHASE4_FINAL.md
docs/evidence/STAGE3C_PHASE4_INTEGRATED_DURABILITY_RESULT.md
```

## Active Phase 5 — installed runtime and lifecycle

Phase 5 validates the product after installation through the frozen Phase 4 engine.

### Active Gate 1 — installed runtime baseline

```text
fresh runtime-base install          714 payload rows
registry mapping                    exact
installed tree fingerprint          exact
runtime and subprocess identity     installed prefix
HTTPS                               200
uv venv                             PASS
uv run with anyio                   PASS
native closure                      81 ELF / 329 edges / unresolved 0
system SONAME dlopen                5/5
extension imports                   67/67
installed prefix mutation           none
verifier                            80/80
```

Run:

```sh
bash experiments/stage3c-installed-runtime-baseline/run-installed-runtime-baseline.sh
```

Detailed scope:

```text
docs/stages/STAGE3C_PHASE5_SCOPE.md
experiments/stage3c-installed-runtime-baseline/README.md
```

### Deferred Gate 2 — installed-prefix relocation

```text
portable installed tree fidelity
registry consistency after move
runtime, HTTPS, uv, and closure revalidation
stale source-prefix rejection
```

### Deferred Gate 3 — same-version lifecycle and exact uninstall

```text
exact reinstall NOOP
registered corruption repair
modified owned leaf preservation
unowned sentinel preservation
addon composition and removal
runtime dependency enforcement
final registry and ownership boundary
```

### Deferred Gate 4 — explicit second-version lifecycle

Upgrade and downgrade require a second complete frozen product identity. Synthetic version labels are insufficient.

## Physical failure boundary

Stage 3-C does not claim persistence across actual sudden power loss, kernel panic, storage-controller failure, write-cache loss, or interruption inside one filesystem primitive.

## Non-reopening rule

Later work must not silently change frozen product roles, ownership, manifests, archive bytes, extraction rules, installation policy, recovery semantics, durability ordering, or integrated source identities.

Any intentional change reopens the corresponding phase and evidence chain.

## Evidence layout

Tracked:

```text
docs/stages/STAGE3C_*.md
docs/evidence/STAGE3C_*.md
experiments/stage3c-*/
```

Generated:

```text
results/termux/stage3c-*/
work/termux/stage3c-*/
```

## Current action

Execute and independently verify the installed runtime-base baseline from a fresh Phase 4 installation root.
