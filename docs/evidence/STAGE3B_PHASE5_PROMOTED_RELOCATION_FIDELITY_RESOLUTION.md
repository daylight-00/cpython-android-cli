# Stage 3-B Phase 5 Promoted Relocation Fidelity Resolution

> **Status:** FROZEN
> **Functional relocation:** PASS
> **Portable tree fidelity:** PASS
> **Final clean rerun:** PASS
> **Previous strict fingerprint failure:** False positive caused by directory `st_size`

## Purpose

This document records the selected fidelity contract, the reason for the correction, and the final end-to-end result.

## First-run diagnosis

The first run passed all functional relocation assertions but reported:

```text
relocated_runtime_matches_source=false
```

The canonical candidate and frozen control remained unchanged. The retained source and location-B trees were compared path by path with regular-file SHA-256 hashes.

```text
source_entry_count          3155
relocated_entry_count       3155
added_count                    0
removed_count                  0
portable_changed_count         0
pycache_path_count              0
portable_pass                true
```

The strict comparison found exactly one changed row:

```text
path
  lib/python3.14/lib-dynload

type
  directory

changed field
  size

source st_size
  12288

relocated st_size
  20480
```

No regular file changed content, size, mode, or mtime. No symlink target changed. No path was added or removed.

## Classification

The failure was not:

```text
runtime relocation failure
validation-induced bytecode mutation
regular-file content mutation
symlink mutation
path-set mutation
```

It was a fingerprint-contract false positive.

The previous source/B fingerprint included `find -printf %s` for every tree entry. For a directory, `%s` is directory `st_size`, which reflects filesystem directory allocation rather than product payload size.

## Correct fidelity contracts

Two different questions use two different contracts.

### Same-tree mutation control

Candidate and frozen before/after checks measure the same inode tree twice.

The strict fingerprint includes:

```text
path
type
mode
size
mtime
symlink target
```

Any change is suspicious because validation must not write those source/control trees.

### Cross-tree product fidelity

Canonical source and relocated B are different inode trees.

The portable comparison requires:

```text
identical relative path set
identical entry type
identical mode
identical mtime

regular files
  identical size
  identical SHA-256

symlinks
  identical target

directories
  st_size intentionally ignored
```

This contract is stronger than the previous fingerprint for regular files because it hashes their content. It excludes only copied-directory allocation size.

## Gate implementation

The promoted relocation workflow uses:

```text
candidate/frozen mutation controls
  -> same-tree strict fingerprint

source/B fidelity
  -> path-level portable manifest comparison
  -> strict comparison retained as a non-gating diagnostic
```

The machine verifier checks:

```text
portable contract version
correct source and relocated roots
source and relocated entry counts equal and non-zero
portable fingerprints equal
added_count=0
removed_count=0
portable_changed_count=0
status and JSON evidence cross-consistent
```

## Final clean rerun

The corrected workflow passed end to end:

```text
schema_version      2
check_count        31
failed_checks      []
missing_outputs    []
parse_errors       {}
pass               true
```

Final fidelity result:

```text
source_entry_count             3155
relocated_entry_count          3155
added_count                       0
removed_count                     0
portable_changed_count            0
pycache_path_count                 0
portable_pass                   true
strict_changed_count               0
strict_pass                     true
```

Portable source/B fingerprint:

```text
79ca7d53f25810b1f5276d18df31f10f2ae981dc24caf67c5f33d37fa75127c8
```

Path-level strict diagnostic source/B fingerprint:

```text
f46b5d81917e9d5dbcfc826a7ef33ef84c1b7db127689def7f20966037a57011
```

Candidate source mutation fingerprint:

```text
834f7aeb2e5266f027b6ee43dd77255079b2e01cf049dad56fda5ef39ce048b0
```

Frozen control mutation fingerprint:

```text
5a14f213bbf069b844a799615ed2b87eb34b48b4251b0a48bf431337e929ce0e
```

Final markers:

```text
LOCATION_RECONFIRM[A]=PASS
LOCATION_RECONFIRM[B]=PASS
STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS
RELOCATED_RUNTIME_PORTABLE_FIDELITY_CHECK=PASS
CANDIDATE_RUNTIME_MUTATION_CHECK=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
STAGE3B_PROMOTED_RELOCATION=PASS
```

## Conclusion

```text
functional relocation at A                 PASS
functional relocation at B                 PASS
stale A-prefix active-state assertions      PASS
canonical candidate mutation control        PASS
frozen control mutation control             PASS
path set equality                            PASS
regular-file content equality               PASS
symlink equality                             PASS
portable relocated-product fidelity         PASS
final machine verdict                       31/31 PASS
previous failure classification              FINGERPRINT CONTRACT FALSE POSITIVE
```

The contract correction and Gate 4 are frozen.
