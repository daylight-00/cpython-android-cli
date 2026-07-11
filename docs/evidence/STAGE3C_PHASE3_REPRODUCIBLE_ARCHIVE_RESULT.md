# Stage 3-C Phase 3 Reproducible Archive Result

> **Status:** PASS — reproducible archive serialization gate closed
> **Target:** Termux on Android arm64
> **Result archive:** `stage3c-phase3-reproducible-archives-results-20260711-220238.tgz`

## Result archive identity

```text
sha256
  51a334a8bbaa16e89a1f3aeb10373cb72a862d3063e25ffb6844f15ce731b946

size
  21,858,727 bytes

members
  36

unsafe member names
  0

special archive entries
  0
```

The uploaded TGZ was independently inspected and extracted into a review directory before its retained JSON and three nested tar.gz archives were analyzed.

## Machine result

```text
reproducible archive builder     31/31 PASS
archive extraction preflight     28/28 PASS
independent archive verifier     76/76 PASS
workflow return codes             all 0
failed checks                         []
source errors                         []
```

```text
STAGE3C_PHASE3_REPRODUCIBLE_ARCHIVE_BUILD=PASS
STAGE3C_PHASE3_REPRODUCIBLE_ARCHIVES=PASS
```

## Byte-identical builds

Build A and build B agree exactly for all three artifacts:

```text
artifact               members      bytes        sha256
runtime-base                722   13,684,443   2ba7c309b1700926dc423eb4305a9eba1a53c023a11617e490b151be71e49743
development-addon           464    1,037,544   f77ea24c92fdd982cd32e172b2d38134f1d785b1f106d1bfe36a9bffa9cc8eea
test-addon                 1798    7,135,813   02a1fad1af5528a4e910f0eb3370f4a2696da4f78067586e8b62f2a10fb4c9b1
```

For every artifact:

```text
build A SHA-256       == build B SHA-256
build A size          == build B size
build A member count  == build B member count
retained archive      == build A index identity
```

## Normalized gzip identity

All three archives begin with the exact expected gzip header:

```text
1f8b08000000000002ff
```

This records:

```text
gzip method       deflate
gzip mtime        0
extra flags       maximum compression
OS byte           255
embedded filename absent
```

## Normalized tar identity

All retained members satisfy:

```text
format             POSIX pax tar
uid / gid          0 / 0
uname / gname      empty / empty
mtime              0
hardlinks          0
special entries    0
member names       unique
member order       exact manifest order
```

Observed PAX keys:

```text
path
```

No non-deterministic or unapproved PAX key was present.

## Archive envelope

Every archive begins with the exact eight envelope members:

```text
<artifact-id>
<artifact-id>/metadata
<artifact-id>/metadata/licenses
<artifact-id>/payload
<artifact-id>/metadata/manifest.json
<artifact-id>/metadata/manifest-index.json
<artifact-id>/metadata/product-lock.json
<artifact-id>/metadata/licenses/CPython-LICENSE.txt
```

The remaining members are the schema-v1 payload and structural rows in exact manifest order.

## Metadata fidelity

For all three artifacts:

```text
metadata/manifest.json
  exact retained artifact manifest bytes

metadata/manifest-index.json
  exact frozen manifest index bytes

metadata/product-lock.json
  exact frozen product lock bytes

metadata/licenses/CPython-LICENSE.txt
  exact frozen license hash and size
```

## Payload fidelity

Independent inspection re-read every retained archive member and verified:

```text
regular-file mode, size, and SHA-256
symlink mode and target
directory mode and zero archive size
exact member count and ordering
absolute paths absent
parent traversal absent
unsupported entry types absent
```

No independently detected payload or metadata mismatch exists.

## Extraction preflight

Before staging extraction, the 28-check preflight proved:

```text
exact trusted member set
exact member order
safe prefix-relative names
allowed directory/regular/symlink types only
hardlinks absent
symlink set exact and prefix-contained
no archive member beneath a symlink parent
```

The extraction verifier was permitted to run only after this preflight passed.

## Safe staging extraction

The custom staging extractor passed for all three artifacts:

```text
runtime-base          PASS
development-addon     PASS
test-addon            PASS
```

Extracted metadata, regular files, directories, and symlinks exactly match the frozen manifests.

Extraction remains staging, not installation.

## Source mutation

Canonical promoted source:

```text
entries before/after
  3155 / 3155

fingerprint before/after
  5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c

pycache paths
  0

special paths
  0
```

Runtime-base:

```text
entries before/after
  714 / 714

fingerprint before/after
  9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796

pycache paths
  0

special paths
  0
```

```text
source mutation check
  PASS
```

## Closed claims

This result proves:

```text
three frozen artifacts serialize to deterministic pax tar.gz bytes
independent target builds A and B are byte-identical
retained archive identities match the build index
normalized gzip and tar ownership/time metadata is exact
archive member order and member set exactly match schema-v1 manifests
metadata and payload bytes are exact
unsafe paths, hardlinks, and special entries are absent
fail-closed preflight gates extraction
safe staging extraction reproduces every manifest entry
canonical and runtime-base source products remain unchanged
```

## Claim boundary

This result does not prove direct installation into a live prefix, installed ownership registry behavior, collision handling, same-version reinstall, upgrade or downgrade, rollback, interrupted-operation recovery, concurrency, or uninstall behavior.

Those begin in Stage 3-C Phase 4.
