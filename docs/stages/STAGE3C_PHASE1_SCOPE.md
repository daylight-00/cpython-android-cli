# Stage 3-C Phase 1 Scope: Promoted Product Role Inventory

> **Status:** ACTIVE — mechanical inventory PASS, semantic decomposition pending
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

## Selected roles

```text
RUNTIME
DEVELOPMENT
METADATA
LICENSE
DEBUG_OR_OPTIONAL
UNKNOWN
```

`UNKNOWN` is a review state, not a distributable role.

## Implementation

```text
experiments/stage3c-product-role-inventory/
  classify-promoted-product.py
  verify-promoted-product-roles.py
  run-role-inventory.sh
  analyze-role-inventory.py
  analyze-role-inventory.sh
  README.md
```

The classifier:

```text
walks all product entries
hashes every regular file
identifies ELF objects by magic
records mode, size, mtime and symlink target
applies ordered semantic rules
computes mixed-directory descendant roles
writes a normalized role-manifest hash
re-inventories the source tree for mutation control
```

The 43-check verifier independently checks the frozen entry, ELF and symlink counts, exact schemas, declared rules, role/type counts, UNKNOWN rows, ELF role, bytecode absence, special-file absence, mixed-directory state, anchors, manifest hash, and before/after source fingerprint.

The decomposition analyzer consumes only accepted inventory evidence. It does not reclassify or mutate the product.

All Python probes run with:

```text
promoted-python -I -B -S
```

## Directory ownership model

Directory entries are not forced to pretend that every descendant has the same semantic role.

Each directory records:

```text
role
  minimum archive-owner role

descendant_roles
  complete semantic role set below the directory

mixed_directory
  whether more than one role occurs below it
```

Current ownership precedence:

```text
RUNTIME
DEVELOPMENT
METADATA
LICENSE
DEBUG_OR_OPTIONAL
UNKNOWN
```

This is an inventory convention for shared parent paths. Final archive ownership is not selected until the semantic decomposition is reviewed.

## Step 1 result: complete role inventory — PASS

```text
entry count                         3155
regular files                       2934
directories                          216
symlinks                               5
ELF objects                           81
UNKNOWN                                0
pycache/pyc paths                       0
unsupported special files              0
machine verifier                    43/43
source mutation control              PASS
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

Role manifest:

```text
092ea87eed2a3c800053a0ef480abd8ef836bda8a8890549ce84370eae6e2a0f
```

Source before/after fingerprint:

```text
5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c
```

Observed mixed directories:

```text
lib
lib/python3.14
lib/python3.14/config-3.14-aarch64-linux-android
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE1_ROLE_INVENTORY_FIRST_RESULT.md
```

## Step 2: exact role decomposition — ACTIVE

The `DEBUG_OR_OPTIONAL` surface is not a trivial tail: it contains 1986 entries and 35,466,620 regular-file bytes. It must be decomposed before any archive omission decision.

Run:

```sh
bash \
  experiments/stage3c-product-role-inventory/analyze-role-inventory.sh
```

The runner first requires the accepted Step 1 verifier evidence:

```text
pass=true
check_count=43
failed_checks=[]
missing_outputs=[]
parse_errors={}
```

It then requires the exact frozen inventory identity:

```text
manifest
  092ea87eed2a3c800053a0ef480abd8ef836bda8a8890549ce84370eae6e2a0f

entries / ELF / symlinks
  3155 / 81 / 5
```

Decomposition outputs:

```text
role-overview.tsv
role-by-rule.tsv
role-by-type.tsv
role-by-top-level.tsv
python-subtree-summary.tsv
optional-component-summary.tsv
optional-root-summary.tsv
development-surface-summary.tsv
runtime-surface-summary.tsv
selected-boundary-rows.tsv
largest-regular-files.tsv
role-review.json
role-review.log
```

The decomposition must sum exactly back to every accepted role count and byte total.

Expected marker:

```text
ROLE_INVENTORY_ACCEPTED_EVIDENCE=PASS
STAGE3C_PHASE1_ROLE_DECOMPOSITION=PASS
```

## Acceptance conditions

Mechanical inventory:

```text
[x] source entry count = 3155
[x] source ELF count = 81
[x] source symlink count = 5
[x] every path has one valid primary role
[x] UNKNOWN count = 0
[x] unknown.tsv has no data rows
[x] all 81 ELF entries are RUNTIME
[x] no __pycache__ or .pyc entries exist
[x] no unsupported special files exist
[x] mixed-directory rows and flags cross-check
[x] required runtime/development anchors match
[x] role counts and type counts cross-check
[x] role-manifest SHA-256 recomputes
[x] source before/after fingerprints match
[x] independent verifier passes 43/43 checks
```

Semantic decomposition and policy selection:

```text
[ ] role/rule decomposition sums exactly
[ ] optional component/root decomposition sums exactly
[ ] CPython regression tests separated from package-local tests
[ ] Tkinter reviewed as its own consumer-facing optional component
[ ] IDLE and turtledemo reviewed separately
[ ] development surface decomposed by headers/config/pkg-config/static libraries
[ ] runtime surface decomposed by bin/libpython/lib-dynload/stdlib/data
[ ] exact LICENSE and METADATA rows reviewed
[ ] shared-directory ownership model selected
[ ] runtime/development/optional archive split selected
```

## Claim boundary

The current result proves:

```text
all 3155 paths are covered by the selected rule set
UNKNOWN=0
accepted inventory is internally consistent and non-mutating
```

It does not yet prove:

```text
all DEBUG_OR_OPTIONAL paths are safely removable
one particular archive split is correct
shared parent directories belong exclusively to one archive
installed sysconfig/config metadata belongs to one final product role
```

Phase 1 remains active until the decomposition and policy review close those questions.
