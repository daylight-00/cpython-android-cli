# Stage 3-B Phase 5 Promoted Relocation Fidelity Resolution

> **Status:** Selected diagnosis and contract correction
> **Functional relocation:** PASS
> **Portable tree fidelity:** PASS
> **Previous strict fingerprint:** False positive caused by directory `st_size`

## Purpose

This document closes the classification of the first promoted relocation fidelity failure.

The first run passed all functional relocation assertions but reported:

```text
relocated_runtime_matches_source=false
```

The canonical candidate and frozen control remained unchanged. The retained source and location-B trees were then compared path by path with regular-file SHA-256 hashes.

## Exact diagnostic result

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

All other fields matched:

```text
type
mode
mtime_ns
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

The previous source/B fingerprint included `find -printf %s` for every tree entry. For a directory, `%s` is directory `st_size`, which reflects filesystem directory allocation rather than product payload size. A copied directory can therefore have a different `st_size` while exposing the same child names and product content.

## Correct fidelity contract

Two distinct questions require two distinct contracts.

### Same-tree mutation control

For candidate and frozen before/after checks, the same inode tree is measured twice.

The existing metadata-sensitive fingerprint remains useful:

```text
path
type
mode
size
mtime
symlink target
```

Any change is suspicious because the workflow is not expected to write those source/control trees.

### Cross-tree product fidelity

For canonical source versus relocated copy, inode allocation metadata must not be treated as product content.

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

This contract is stronger than the previous fingerprint for regular files because it hashes their content. It is also more semantically correct because it excludes only copied-directory allocation size.

## Gate correction

The promoted relocation workflow is corrected to:

```text
candidate/frozen mutation controls
  -> existing same-tree strict fingerprint

source/B fidelity
  -> path-level portable manifest comparison
  -> retain strict comparison as a non-gating observation
```

The machine verifier directly checks:

```text
portable_pass=true
added_count=0
removed_count=0
portable_changed_count=0
source_entry_count == relocated_entry_count
```

The diagnostic artifacts remain under:

```text
results/termux/stage3b-promoted-relocation/fidelity-diagnosis/
```

## Claim boundary

The retained first-run evidence proves the corrected portable fidelity contract already passes for that source/B pair.

A clean rerun remains required because the final Gate 4 wrapper and machine verdict must execute the corrected contract end to end before Phase 5 is frozen.

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
previous failure classification              FINGERPRINT CONTRACT FALSE POSITIVE
```
