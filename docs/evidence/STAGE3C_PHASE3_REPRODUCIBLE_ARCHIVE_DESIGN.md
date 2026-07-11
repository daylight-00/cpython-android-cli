# Stage 3-C Phase 3 Reproducible Archive Design

> **Status:** IMPLEMENTED — target evidence pending

## Serialization contract

```text
format                     POSIX pax tar + gzip
gzip level                 9
gzip filename              empty
gzip mtime                 0
tar member mtime           0
uid/gid                    0/0
uname/gname                empty
envelope directory mode    0755
metadata file mode         0644
payload mode               schema-v1 exact mode
hardlinks                  forbidden
special entries            forbidden
PAX headers                path/linkpath only when required
```

## Envelope

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

## Evidence chain

```text
builder
  31 checks
  validates accepted Phase 2 identities and source payloads
  builds every artifact twice
  requires identical SHA-256, size, and member count

preflight
  28 checks
  requires exact member order and set
  rejects unsafe paths, extra symlinks, hardlinks, and special types
  rejects any member whose parent path is a symlink

independent verifier
  76 checks
  validates gzip and tar normalization
  validates metadata and payload bytes
  performs safe custom staging extraction
  validates extracted metadata, regular files, directories, and symlinks
```

Extraction is blocked unless both the builder and preflight pass.

## Source mapping

```text
runtime-base payload
  isolated validated runtime-base prefix

development and test payloads
  canonical promoted prefix selected by frozen manifests

STRUCTURAL_PARENT
  emitted as a directory header
  remains non-owning
```

## Reproducibility boundary

Build A archives are retained. Build B archives are created in an independent temporary directory; their hashes, sizes, member counts, and manifest identities are retained in `build-b-index.json` before temporary bytes are removed.

## Failure preservation

```text
builder failure
  preflight and extraction verifier are blocked with explicit JSON records

preflight failure
  extraction verifier is blocked

no blocked downstream stage can claim archive or extraction validity
```

## Claim boundary

A PASS proves target-local byte reproducibility, normalized archive headers, exact schema-v1 member fidelity, and safe staging extraction under the tested implementation.

It does not prove direct installation, collision handling, lifecycle transactions, upgrade, rollback, or uninstall.
