# Stage 3-C Phase 1 Scope: Promoted Product Role Inventory

> **Status:** ACTIVE — target execution pending
> **Input:** frozen Stage 3-B promoted runtime
> **Execution host:** Termux on Android arm64
> **Hard gate:** `UNKNOWN=0`

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

## Selected implementation

```text
experiments/stage3c-product-role-inventory/
  classify-promoted-product.py
  verify-promoted-product-roles.py
  run-role-inventory.sh
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

The 43-check verifier independently parses the generated TSV/JSON evidence and checks the frozen entry, ELF and symlink counts, exact schemas, declared rules, role/type counts, UNKNOWN rows, ELF role, bytecode absence, special-file absence, mixed-directory state, anchors, manifest hash, and before/after source fingerprint.

Both run with:

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

This is an inventory convention for shared parent paths. Final archive ownership is not selected until the target result is reviewed.

## Run

```sh
cd "$HOME/projects/cpython-android-cli"

git pull --ff-only

git log -1 --oneline

bash \
  experiments/stage3c-product-role-inventory/run-role-inventory.sh
```

Default results:

```text
results/termux/stage3c-phase1-role-inventory/
  product-role-inventory.tsv
  unknown.tsv
  mixed-directories.tsv
  rules.tsv
  role-summary.json
  mutation-check.txt
  classifier.log
  verifier.log
  verification.json
```

## Target acceptance conditions

```text
[ ] source entry count = 3155
[ ] source ELF count = 81
[ ] source symlink count = 5
[ ] every path has one valid primary role
[ ] UNKNOWN count = 0
[ ] unknown.tsv has no data rows
[ ] all 81 ELF entries are RUNTIME
[ ] no __pycache__ or .pyc entries exist
[ ] no unsupported special files exist
[ ] mixed-directory rows and flags cross-check
[ ] required runtime/development anchors match
[ ] role counts and type counts cross-check
[ ] role-manifest SHA-256 recomputes
[ ] source before/after fingerprints match
[ ] independent verifier passes 43/43 checks
```

Expected markers when the first selected rule set closes the product:

```text
STAGE3C_PRODUCT_ROLE_CLASSIFIER=PASS
PRODUCT_ROLE_UNKNOWN_ZERO=PASS
PRODUCT_ROLE_MUTATION_CHECK=PASS
STAGE3C_PHASE1_ROLE_INVENTORY=PASS
```

## Failure handling

A non-zero unknown count is not repaired with a broad fallback.

For every exact unknown path:

```text
inspect path, type and content surface
identify its consumer or provenance role
add the narrowest justified rule
retain the failed first-run evidence
rerun from the unchanged canonical product
```

If the observed entry, ELF, or symlink count differs from the frozen `3155 / 81 / 5` contract, stop and classify the changed product boundary before overriding expected counts.

## Evidence

Design record:

```text
docs/evidence/STAGE3C_PHASE1_ROLE_INVENTORY_DESIGN.md
```

The target result document is created only after the Termux machine output is reviewed.

## Claim boundary

Phase 1 does not yet decide:

```text
single versus split archive
which semantic roles ship together
archive root naming
installation prefix
installer ownership and rollback
manifest publication schema
archive metadata normalization
compression format
```

It closes only the exact semantic inventory needed to make those decisions without guessing.
