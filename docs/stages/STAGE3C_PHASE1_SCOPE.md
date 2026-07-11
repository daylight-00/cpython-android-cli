# Stage 3-C Phase 1 Scope: Promoted Product Role Inventory

> **Status:** ACTIVE — inventory PASS, decomposition PASS, semantic capability probes pending
> **Input:** frozen Stage 3-B promoted runtime
> **Execution host:** Termux on Android arm64
> **Completed hard gate:** `UNKNOWN=0`

## Question

> Which exact paths in the frozen promoted product are runtime, development, metadata, license, or optional/debug surfaces before an archive split and ownership model are selected?

## Input contract

```text
work/termux/stage3b-promoted-runtime/prefix
```

Frozen Stage 3-B properties:

```text
entry count                         3155
ELF objects                           81
symlinks                               5
unresolved native edges                0
extension imports                   67/67
promoted relocation verifier        31/31
candidate mutation control           PASS
relocated-product fidelity           PASS
```

Phase 1 observes this product. It must not modify, prune, strip, rewrite, or package it.

## Selected descriptive roles

```text
RUNTIME
DEVELOPMENT
METADATA
LICENSE
DEBUG_OR_OPTIONAL
UNKNOWN
```

`UNKNOWN` is a review state, not a distributable role.

`METADATA` is not assumed to be one archive. Its paths are assigned to runtime or development consumers only after semantic and variant testing.

## Implementation

```text
experiments/stage3c-product-role-inventory/
  classify-promoted-product.py
  verify-promoted-product-roles.py
  run-role-inventory.sh
  analyze-role-inventory.py
  analyze-role-inventory.sh
  probe-role-semantics.py
  verify-role-semantics.py
  run-role-semantic-probes.sh
  README.md
```

All Python probes run under:

```text
promoted-python -I -B -S
```

## Step 1: complete role inventory — PASS

```text
entries                              3155
regular files                        2934
directories                           216
symlinks                                5
ELF objects                            81
UNKNOWN                                 0
pycache/pyc paths                        0
unsupported special files               0
machine verifier                     43/43
source mutation control               PASS
```

Role counts:

```text
RUNTIME               711
DEVELOPMENT           449
METADATA                8
LICENSE                 1
DEBUG_OR_OPTIONAL    1986
```

Role manifest:

```text
092ea87eed2a3c800053a0ef480abd8ef836bda8a8890549ce84370eae6e2a0f
```

Source before/after fingerprint:

```text
5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE1_ROLE_INVENTORY_FIRST_RESULT.md
```

## Step 2: exact role decomposition — PASS

Machine result:

```text
check_count       18
failed_checks     []
pass              true
```

Optional surface:

```text
lib/python3.14/test          1785 entries   33,476,596 bytes
lib/python3.14/idlelib        161 entries    1,624,586 bytes
lib/python3.14/tkinter         14 entries      303,444 bytes
lib/python3.14/turtledemo      23 entries       61,800 bytes
lib/python3.14/__phello__       3 entries          194 bytes
```

Development surface:

```text
include/                                      434 entries   4,701,144 bytes
lib/pkgconfig/                                  9 entries       1,689 bytes
lib/python3.14/config-*                         6 entries      34,331 bytes
```

Runtime surface:

```text
stdlib and runtime data                       622 entries  12,362,626 bytes
lib-runtime                                    16 entries  12,950,104 bytes
lib-dynload                                    68 entries   7,630,224 bytes
libpython                                       1 entry     5,821,560 bytes
bin                                             4 entries      10,992 bytes
```

Exact metadata split candidate:

```text
runtime metadata candidates
  _sysconfigdata__android_aarch64-linux-android.py
  _sysconfig_vars__android_aarch64-linux-android.json
  build-details.json

development metadata candidates
  config-*/Makefile
  config-*/Setup
  config-*/Setup.local
  config-*/config.c
  config-*/python-config.py
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE1_ROLE_DECOMPOSITION_RESULT.md
```

## Directory ownership model

Observed mixed directories:

```text
lib
lib/python3.14
lib/python3.14/config-3.14-aarch64-linux-android
```

The inventory stores a minimum directory-owner role and the complete descendant-role set. This is not a final archive ownership decision.

A final split must operate on exact manifest paths, not on naive whole-directory moves.

## Step 3: semantic capability probes — ACTIVE

Question:

> Which candidate optional and metadata surfaces actually provide working target capabilities, and which are inert or development-only?

Run:

```sh
bash \
  experiments/stage3c-product-role-inventory/run-role-semantic-probes.sh
```

Observed capabilities will include:

```text
venv
ensurepip
test and test.support
__phello__
_tkinter
tkinter
Tcl interpreter construction
turtle
idlelib
idlelib.pyshell
turtledemo
sysconfig variables and paths
_sysconfigdata import
_sysconfig_vars JSON
build-details JSON
Makefile discovery
pyconfig.h discovery
```

The semantic probe is observational:

```text
optional-module success or failure is retained as evidence
core/sysconfig services must succeed
the canonical source must not change
all observation fields must parse and cross-check
```

Expected machine result:

```text
semantic probe verifier   36/36
source mutation           PASS
```

Expected markers:

```text
STAGE3C_PHASE1_ROLE_SEMANTIC_PROBE=PASS
ROLE_SEMANTICS_SOURCE_MUTATION_CHECK=PASS
STAGE3C_PHASE1_ROLE_SEMANTICS=PASS
```

## Provisional policy classes

```text
lib/python3.14/test
  OPTIONAL_TEST_SUITE candidate

idlelib + turtledemo
  OPTIONAL_GUI_TOOLING candidates

tkinter
  OPTIONAL_GUI_RUNTIME candidate; pending _tkinter/Tcl evidence

__phello__
  OPTIONAL_TEST_DEMO candidate

include + pkgconfig + config development rows
  DEVELOPMENT candidate

_sysconfigdata + _sysconfig_vars + build-details
  RUNTIME_METADATA candidate

config-tree Makefile/Setup/config/python-config rows
  DEVELOPMENT_METADATA candidate
```

## Acceptance conditions

Mechanical inventory:

```text
[x] source entry count = 3155
[x] source ELF count = 81
[x] source symlink count = 5
[x] every path has one valid primary role
[x] UNKNOWN count = 0
[x] all 81 ELF entries are RUNTIME
[x] no pycache/pyc entries exist
[x] no unsupported special files exist
[x] role-manifest SHA-256 recomputes
[x] source before/after fingerprints match
[x] independent verifier passes 43/43
```

Semantic decomposition:

```text
[x] role/rule decomposition sums exactly
[x] optional component/root decomposition sums exactly
[x] development surface decomposed
[x] runtime surface decomposed
[x] exact LICENSE and METADATA rows recorded
[x] decomposition verifier passes 18/18
```

Capability and policy selection:

```text
[ ] target optional-module capability matrix recorded
[ ] sysconfig runtime/development metadata consumers recorded
[ ] semantic probe verifier passes 36/36
[ ] semantic probe source mutation control passes
[ ] CPython regression suite policy selected
[ ] Tkinter/IDLE/turtle/turtledemo policy selected
[ ] __phello__ policy selected
[ ] runtime metadata set selected
[ ] development metadata set selected
[ ] shared-directory ownership selected
[ ] runtime/development/optional archive split selected
[ ] isolated payload variants validate the selected split
```

## Claim boundary

Current evidence proves:

```text
all 3155 paths are completely classified and decomposed
regression tests dominate the optional byte surface
development, runtime, metadata, license, and symlink boundaries are explicit
accepted inventories are internally consistent and non-mutating
```

It does not yet prove:

```text
all DEBUG_OR_OPTIONAL paths can be removed together
tkinter is functional on the tested target
config-tree metadata can be removed from the runtime product
one particular archive split is correct
```

Phase 1 remains active until capability probes and isolated payload variants close those questions.
