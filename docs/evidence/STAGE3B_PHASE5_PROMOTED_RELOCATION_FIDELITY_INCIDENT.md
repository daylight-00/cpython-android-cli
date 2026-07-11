# Stage 3-B Phase 5 Promoted Relocation Fidelity Incident

> **Status:** Diagnosed and resolved
> **Execution host:** Termux on Android arm64
> **Functional relocation:** PASS at A and B
> **Source mutation controls:** PASS
> **Initial strict fingerprint:** FAIL
> **Corrected portable fidelity:** PASS

## Purpose

This document preserves the first promoted whole-prefix relocation run, the exact failure, and its later classification.

The run used:

```text
source candidate
  work/termux/stage3b-promoted-runtime/prefix

location A
  work/termux/stage3b-promoted-relocation/location-a/prefix

location B
  work/termux/stage3b-promoted-relocation/location-b/prefix
```

## Functional result

Both locations passed:

```text
runtime identity re-rooted
active sysconfig paths re-rooted
HTTPS 200
child interpreter identity re-rooted
fresh uv venv PASS
venv base-prefix identity PASS
uv run PASS
uv run base-prefix identity PASS
```

At B, the old A prefix was absent from all tested active runtime assertions.

Observed markers:

```text
LOCATION_RECONFIRM[A]=PASS
LOCATION_RECONFIRM[B]=PASS
STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS
STAGE3A_PRODUCTION_RELOCATION_RECONFIRM=PASS
```

The uv hardlink warning was the already-reviewed fallback-to-copy performance warning. Both package installation and consumer validations completed.

## Initial machine verdict

```text
check_count       16
passed checks     15
failed checks      1
missing_outputs   []
parse_errors      {}
```

Only this check failed:

```text
relocated_runtime_matches_source=false
```

Candidate and frozen controls were unchanged.

## Read-only diagnosis

The retained source and B trees were compared path by path, hashing every regular file.

Result:

```text
source_entry_count          3155
relocated_entry_count       3155
added_count                    0
removed_count                  0
portable_changed_count         0
pycache_path_count              0
portable_pass                true
```

The strict comparison found exactly one difference:

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

No file content, file size, mode, mtime, symlink target, or path-set difference existed.

## Classification

The previous fingerprint used `find -printf %s` for all entry types. For directories, `%s` is directory `st_size`, an inode/filesystem allocation property rather than product payload size.

The failure is therefore classified as:

```text
FINGERPRINT CONTRACT FALSE POSITIVE
```

It was not:

```text
runtime relocation defect
validation-induced bytecode mutation
regular-file content mutation
symlink mutation
path-set mutation
```

## Corrected contract

Same-tree candidate/frozen before-and-after mutation controls retain the strict metadata-sensitive fingerprint.

Cross-tree source/B fidelity now requires:

```text
identical path set
identical type, mode and mtime
identical regular-file size and SHA-256
identical symlink target
```

Directory `st_size` is retained as a diagnostic observation but excluded from the cross-tree product gate.

Detailed resolution:

```text
docs/evidence/STAGE3B_PHASE5_PROMOTED_RELOCATION_FIDELITY_RESOLUTION.md
```

## Current conclusion

The first run proves functional relocation and corrected portable product fidelity. A clean end-to-end rerun of the corrected Gate 4 wrapper remains required before Phase 5 freeze.
