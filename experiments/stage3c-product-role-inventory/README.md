# Stage 3-C Phase 1: Promoted Product Role Inventory

> **Status:** INVENTORY PASS, DECOMPOSITION PASS, SEMANTIC CAPABILITY PROBES ACTIVE
> **Input:** frozen Stage 3-B promoted runtime
> **First gate:** complete semantic role classification with `UNKNOWN=0`

## Question

> Which exact paths in the frozen promoted product are runtime, development, metadata, license, or optional/debug surfaces before an archive split is selected?

## Frozen input

```text
work/termux/stage3b-promoted-runtime/prefix
```

```text
entry count      3155
ELF objects        81
symlinks             5
```

## Step 1: complete role inventory — PASS

```sh
bash \
  experiments/stage3c-product-role-inventory/run-role-inventory.sh
```

Observed:

```text
UNKNOWN                              0
machine verifier                 43/43
source mutation control           PASS
role manifest
  092ea87eed2a3c800053a0ef480abd8ef836bda8a8890549ce84370eae6e2a0f
```

Role counts:

```text
RUNTIME               711
DEVELOPMENT           449
METADATA                8
LICENSE                 1
DEBUG_OR_OPTIONAL    1986
```

Regular-file bytes:

```text
RUNTIME             38,775,506
DEBUG_OR_OPTIONAL   35,466,620
DEVELOPMENT          4,737,164
METADATA               356,169
LICENSE                  13,804
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE1_ROLE_INVENTORY_FIRST_RESULT.md
```

## Step 2: exact role decomposition — PASS

```sh
bash \
  experiments/stage3c-product-role-inventory/analyze-role-inventory.sh
```

Observed:

```text
machine checks      18/18
manifest             exact
entries/ELF/links    3155 / 81 / 5
role counts          exact
role byte totals     exact
unmatched optional   0
```

Optional decomposition:

```text
lib/python3.14/test          1785 entries   33,476,596 bytes
lib/python3.14/idlelib        161 entries    1,624,586 bytes
lib/python3.14/tkinter         14 entries      303,444 bytes
lib/python3.14/turtledemo      23 entries       61,800 bytes
lib/python3.14/__phello__       3 entries          194 bytes
```

Development decomposition:

```text
include/                                      434 entries   4,701,144 bytes
lib/pkgconfig/                                  9 entries       1,689 bytes
lib/python3.14/config-*                         6 entries      34,331 bytes
```

Runtime decomposition:

```text
stdlib and runtime data                       622 entries  12,362,626 bytes
lib-runtime                                    16 entries  12,950,104 bytes
lib-dynload                                    68 entries   7,630,224 bytes
libpython                                       1 entry     5,821,560 bytes
bin                                             4 entries      10,992 bytes
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE1_ROLE_DECOMPOSITION_RESULT.md
```

The decomposition proves exact accounting. It does not prove that all optional paths may be omitted together.

## Roles

```text
RUNTIME
DEVELOPMENT
METADATA
LICENSE
DEBUG_OR_OPTIONAL
UNKNOWN
```

`UNKNOWN` is a review state, not a distributable role. `METADATA` is descriptive and must be assigned to a consumer-facing archive role after capability testing.

## Directory model

Directories can contain more than one semantic role. Each directory records:

```text
role
  minimum archive-owner role

descendant_roles
  complete role set below the directory

mixed_directory
  true when descendant roles are mixed
```

Observed mixed directories:

```text
lib
lib/python3.14
lib/python3.14/config-3.14-aarch64-linux-android
```

Final archive ownership therefore cannot use a naive whole-directory split.

## Step 3: semantic capability probes — ACTIVE

The next probe observes actual target consumers before any payload is removed.

```sh
bash \
  experiments/stage3c-product-role-inventory/run-role-semantic-probes.sh
```

It checks:

```text
venv and ensurepip imports
test and test.support imports
__phello__ import
_tkinter presence and importability
tkinter import and Tcl interpreter creation
turtle import
idlelib and idlelib.pyshell imports
turtledemo import
sysconfig variables and active paths
_sysconfigdata import
_sysconfig_vars JSON presence
build-details JSON parsing
Makefile and pyconfig.h discovery
complete before/after source fingerprint
```

Optional capability failure is an observation, not an automatic probe failure. The mechanical verifier requires only that every observation is complete, core/sysconfig services work, and the canonical product remains unchanged.

Outputs:

```text
results/termux/stage3c-phase1-role-semantics/
  semantic-probes.json
  verification.json
  probe.log
  verifier.log
```

Expected markers:

```text
STAGE3C_PHASE1_ROLE_SEMANTIC_PROBE=PASS
ROLE_SEMANTICS_SOURCE_MUTATION_CHECK=PASS
STAGE3C_PHASE1_ROLE_SEMANTICS=PASS
```

## Non-mutation contract

All Python inventory and semantic probes run under the promoted interpreter as:

```text
python -I -B -S
```

The source tree fingerprint includes path, type, mode, size, mtime, regular-file SHA-256, and symlink target. No bytecode may be written into the candidate.

## Current policy hypotheses

```text
lib/python3.14/test
  OPTIONAL_TEST_SUITE candidate

idlelib + turtledemo
  OPTIONAL_GUI_TOOLING candidates

tkinter
  OPTIONAL_GUI_RUNTIME candidate, pending _tkinter/Tcl evidence

__phello__
  OPTIONAL_TEST_DEMO candidate

include + pkgconfig + config development rows
  DEVELOPMENT candidate

_sysconfigdata + _sysconfig_vars + build-details
  RUNTIME_METADATA candidate

config-tree Makefile/Setup/config/python-config rows
  DEVELOPMENT_METADATA candidate
```

Do not turn these hypotheses into archive deletion rules until the semantic probes and later isolated payload-variant tests pass.
