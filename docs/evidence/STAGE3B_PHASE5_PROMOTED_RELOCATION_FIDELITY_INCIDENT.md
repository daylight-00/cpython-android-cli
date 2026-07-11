# Stage 3-B Phase 5 Promoted Relocation Fidelity Incident

> **Status:** Resolved and superseded by final PASS
> **Execution host:** Termux on Android arm64
> **Functional relocation:** PASS at A and B
> **Source mutation controls:** PASS
> **Initial strict fingerprint:** FAIL
> **Corrected portable fidelity:** PASS
> **Final clean rerun:** PASS

## Purpose

This document preserves the first promoted whole-prefix relocation run, its exact failure, the row-level diagnosis, and the later clean rerun that closed the gate.

## First-run functional result

The first run validated both locations:

```text
runtime identity re-rooted
active sysconfig paths re-rooted
HTTPS 200
child interpreter identity re-rooted
fresh uv venv PASS
venv base-prefix identity PASS
uv run PASS
uv run base-prefix identity PASS
stale A-prefix active assertions absent at B
```

Observed markers:

```text
LOCATION_RECONFIRM[A]=PASS
LOCATION_RECONFIRM[B]=PASS
STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS
STAGE3A_PRODUCTION_RELOCATION_RECONFIRM=PASS
```

The initial machine verifier reported:

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

The failure was classified as:

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

Cross-tree source/B fidelity requires:

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

## Final clean rerun

The corrected end-to-end wrapper later passed:

```text
schema_version      2
check_count        31
failed_checks      []
missing_outputs    []
parse_errors       {}
pass               true
```

Final product comparison:

```text
source entries               3155
relocated entries            3155
added paths                     0
removed paths                   0
portable changed paths          0
pycache paths                    0
portable fidelity             PASS
strict fidelity               PASS
```

Portable source/B fingerprint:

```text
79ca7d53f25810b1f5276d18df31f10f2ae981dc24caf67c5f33d37fa75127c8
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

## Current conclusion

The incident is closed. It remains preserved because it explains why same-tree mutation controls and cross-tree product fidelity use different contracts.

Final selected evidence:

```text
docs/evidence/STAGE3B_PHASE5_PROMOTED_RELOCATION.md
docs/evidence/STAGE3B_PHASE5_FINAL_SUMMARY.md
```
