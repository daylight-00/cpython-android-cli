# Stage 3-C Phase 3 Scope: Reproducible Archive Serialization

> **Status:** FROZEN
> **Input:** frozen Stage 3-C Phase 2 manifests
> **Primary target:** Termux on Android arm64

## Frozen result

```text
artifact               members      bytes        sha256
runtime-base                722   13,684,443   2ba7c309b1700926dc423eb4305a9eba1a53c023a11617e490b151be71e49743
development-addon           464    1,037,544   f77ea24c92fdd982cd32e172b2d38134f1d785b1f106d1bfe36a9bffa9cc8eea
test-addon                 1798    7,135,813   02a1fad1af5528a4e910f0eb3370f4a2696da4f78067586e8b62f2a10fb4c9b1
```

Build A and build B are byte-identical for every artifact.

## Frozen normalization

```text
format                     POSIX pax tar + gzip
gzip level                 9
gzip filename              empty
gzip mtime                 0
tar member mtime           0
uid / gid                  0 / 0
uname / gname              empty / empty
envelope directory mode    0755
metadata file mode         0644
payload mode               schema-v1 exact mode
hardlinks                  forbidden
special entries            forbidden
PAX keys observed          path
```

Exact gzip header:

```text
1f8b08000000000002ff
```

## Frozen envelope

```text
<artifact-id>/
  metadata/
    manifest.json
    manifest-index.json
    product-lock.json
    licenses/CPython-LICENSE.txt
  payload/
    <schema-v1 archive paths>
```

Extraction is staging, not installation.

## Frozen safety chain

```text
archive builder             31/31 PASS
extraction preflight        28/28 PASS
archive verifier            76/76 PASS
safe staging extraction       3/3 PASS
source mutation                  PASS
```

Extraction is blocked until exact member set, member order, path safety, entry type, hardlink absence, symlink containment, and symlink-parent traversal checks pass.

## Authoritative record

```text
docs/stages/STAGE3C_PHASE3_FINAL.md
docs/evidence/STAGE3C_PHASE3_REPRODUCIBLE_ARCHIVE_RESULT.md
```

Accepted result bundle:

```text
stage3c-phase3-reproducible-archives-results-20260711-220238.tgz
sha256
  51a334a8bbaa16e89a1f3aeb10373cb72a862d3063e25ffb6844f15ce731b946
```

## Deferred to Phase 4

```text
installed state layout
ownership registry
collision policy
same-version reinstall
mutation journal
rollback and recovery
concurrent-operation locking
upgrade and downgrade
uninstall
```

Next scope:

```text
docs/stages/STAGE3C_PHASE4_SCOPE.md
```

## Final marker

```text
STAGE3C_PHASE3=FROZEN
```
