# Stage 3-C Phase 1 Product-Role Inventory Design

> **Status:** IMPLEMENTED — target execution pending
> **Input:** frozen promoted runtime candidate
> **Execution host:** Termux on Android arm64
> **Gate:** complete semantic role classification with `UNKNOWN=0`

## Purpose

Stage 3-C begins by classifying the frozen promoted product before selecting an archive split or installer model.

The input tree is:

```text
work/termux/stage3b-promoted-runtime/prefix
```

The inventory is read-only. It does not remove files, rewrite metadata, create bytecode, strip binaries, or construct an archive.

## Roles

Every product entry receives one primary role:

```text
RUNTIME
DEVELOPMENT
METADATA
LICENSE
DEBUG_OR_OPTIONAL
UNKNOWN
```

The first hard gate is:

```text
UNKNOWN=0
```

## Classification model

Classification is evidence-driven and ordered.

High-confidence rules include:

```text
ELF objects                              -> RUNTIME
bin/ entry points                        -> RUNTIME
Python stdlib/extension tree             -> RUNTIME
installed test/demo/GUI trees            -> DEBUG_OR_OPTIONAL
runtime shared libraries                 -> RUNTIME
include/ headers                         -> DEVELOPMENT
static libraries                         -> DEVELOPMENT
pkg-config surfaces                      -> DEVELOPMENT
installed config development surface     -> DEVELOPMENT or METADATA
_sysconfigdata / _sysconfig_vars         -> METADATA
build-details and producer metadata       -> METADATA
license/copying/notice surfaces           -> LICENSE
known debug/symbol surfaces               -> DEBUG_OR_OPTIONAL
unmatched paths                           -> UNKNOWN
```

Rules are ordered so that legal, debug, optional, and metadata exceptions are selected before broad runtime-tree fallbacks.

## Directory semantics

A directory can contain multiple semantic roles. The inventory therefore records:

```text
role
  minimum archive-owner role selected by explicit precedence

descendant_roles
  complete sorted role set beneath the directory

mixed_directory
  true when more than one descendant role exists
```

Ownership precedence is:

```text
RUNTIME
DEVELOPMENT
METADATA
LICENSE
DEBUG_OR_OPTIONAL
UNKNOWN
```

This does not claim that all contents of a mixed directory share the directory's primary role. It identifies which product must own/create the shared directory path while retaining the full descendant-role set for later archive-split design.

An empty directory is classified directly from its path. An unmatched empty directory remains `UNKNOWN`.

## Inputs and outputs

The classifier walks the canonical candidate directly and hashes every regular file.

Outputs:

```text
results/termux/stage3c-phase1-role-inventory/
  product-role-inventory.tsv
  unknown.tsv
  mixed-directories.tsv
  rules.tsv
  role-summary.json
  mutation-check.txt
  verification.json
```

The inventory TSV records:

```text
path
type
mode
size
mtime_ns
sha256
symlink_target
elf
role
rule_id
reason
descendant_roles
mixed_directory
```

## Non-mutation control

The candidate tree is inventoried before and after classification.

The same-tree fingerprint includes:

```text
path
type
mode
size
mtime_ns
regular-file SHA-256
symlink target
```

The gate requires the before and after fingerprints to be identical.

The classifier itself runs as:

```text
candidate-python -I -B -S
```

This prevents validation-induced bytecode writes and avoids ambient Python package state.

## Machine verifier

The verifier independently checks:

```text
all required outputs exist and parse
schema version matches
entry count equals frozen Stage 3-B count (3155)
TSV paths are unique
role/type counts match the summary
UNKNOWN count is zero
unknown.tsv has no data rows
all ELF entries are RUNTIME
no __pycache__ or .pyc paths exist
no unsupported special-file entries exist
candidate mutation check passes
required runtime/development anchor paths exist with expected roles
manifest hash recomputes exactly
classifier and verifier verdicts agree
```

## Claim boundary

A passing role inventory proves only that every current promoted path has a selected semantic role under the recorded rule set and that the census did not mutate the product.

It does not yet select:

```text
single versus split archive layout
which roles are bundled together
installation prefix
ownership transaction semantics
manifest publication format
archive normalization or compression
```

Those decisions follow after the exact role counts and mixed-directory surface are reviewed.
