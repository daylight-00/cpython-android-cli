# Stage 3-C Phase 1 Product-Role Inventory: First Target Result

> **Status:** MECHANICAL GATE PASS — semantic split review remains active
> **Execution host:** Termux on Android arm64
> **Input:** frozen promoted runtime
> **Result:** `UNKNOWN=0`, verifier `43/43`, source non-mutation PASS

## Purpose

This document records the first complete target-side semantic inventory of the frozen Stage 3-B promoted product.

The result closes the mechanical completeness gate. It does not yet freeze the archive split or declare every `DEBUG_OR_OPTIONAL` subtree removable.

## Input contract

```text
runtime prefix
  work/termux/stage3b-promoted-runtime/prefix

expected entries
  3155

expected ELF objects
  81

expected symlinks
  5
```

## Mechanical result

```text
entry count                         3155
regular files                       2934
directories                          216
symlinks                               5
ELF objects                           81
UNKNOWN                                0
pycache/pyc paths                       0
unsupported special files              0
mixed directories                       3
machine verifier                    43/43
source mutation control              PASS
```

Machine verdict:

```text
failed_checks      []
missing_outputs    []
parse_errors       {}
pass               true
```

## Role counts

Counts include regular files, directories, and symlinks.

```text
RUNTIME               711
DEVELOPMENT           449
METADATA                8
LICENSE                 1
DEBUG_OR_OPTIONAL    1986
UNKNOWN                  0
```

## Regular-file bytes by role

```text
RUNTIME             38,775,506
DEBUG_OR_OPTIONAL   35,466,620
DEVELOPMENT          4,737,164
METADATA               356,169
LICENSE                  13,804
```

The `DEBUG_OR_OPTIONAL` surface is too large to treat as a trivial cleanup bucket. It is close to the runtime payload in byte size and contains most classified entries.

This is a design signal, not a failure.

## Mixed directories

```text
lib
  RUNTIME, DEVELOPMENT, METADATA, LICENSE, DEBUG_OR_OPTIONAL

lib/python3.14
  RUNTIME, DEVELOPMENT, METADATA, LICENSE, DEBUG_OR_OPTIONAL

lib/python3.14/config-3.14-aarch64-linux-android
  DEVELOPMENT, METADATA
```

The selected directory-owner role is only an inventory convention. It does not authorize one archive to claim all child paths in a mixed directory.

## Anchors

```text
bin/python3.14                     RUNTIME
bin/python3                        RUNTIME
bin/python                         RUNTIME
lib/libpython3.14.so               RUNTIME
include/python3.14/Python.h        DEVELOPMENT
include/python3.14/pyconfig.h      DEVELOPMENT
```

All 81 ELF objects were classified `RUNTIME`.

## Manifest and mutation evidence

Role manifest:

```text
092ea87eed2a3c800053a0ef480abd8ef836bda8a8890549ce84370eae6e2a0f
```

Same-tree source fingerprint before and after:

```text
5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c
```

```text
before == after
mutation_pass=true
```

## Exact conclusion

The first hard gate is closed:

```text
complete path coverage                     PASS
UNKNOWN=0                                  PASS
frozen 3155 / 81 / 5 input identity        PASS
source non-mutation                         PASS
machine verification                       43/43 PASS
```

The following claim is not yet allowed:

```text
all DEBUG_OR_OPTIONAL paths may be omitted from the default runtime archive
```

The role currently combines semantically different candidate surfaces such as:

```text
CPython regression tests
package-local tests
IDLE
turtle demos
Tkinter
other explicitly matched optional/demo trees
```

These need exact rule and subtree decomposition before the archive split is selected.

## Next gate

Produce machine-readable decomposition by:

```text
role and classifier rule
role and entry type
role and top-level path
optional matched subtree
runtime/development/metadata boundary surface
largest regular files
exact LICENSE and METADATA rows
```

The decomposition must cross-check back to:

```text
3155 total entries
81 ELF objects
5 symlinks
092ea87e... role-manifest hash
all role counts and regular-file byte totals
```

Only after this review may Phase 1 select whether the product should use:

```text
one combined archive
runtime + development archives
runtime + development + optional/debug archives
```
