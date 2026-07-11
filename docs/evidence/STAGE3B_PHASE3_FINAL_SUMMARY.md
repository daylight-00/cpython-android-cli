# Stage 3-B Phase 3 Final Summary

> **Status:** FROZEN
> **Stage:** 3-B Phase 3
> **Result:** PASS — dependency product identities promoted and verified

## Result

The six prebuilt Android dependency archives consumed by the successful Phase 2 replay were captured, promoted into a tracked lock, recaptured, and compared field-by-field.

Final markers:

```text
STAGE3B_DEPENDENCY_INPUT_CAPTURE=PASS
STAGE3B_DEPENDENCY_INPUT_VERIFY=PASS
```

Top-level verification:

```text
schema_version                  PASS
source_head                     PASS
target_host                     PASS
producer_files                  PASS
product_count                   PASS
product_filenames               PASS
all_expected_products_present  PASS
```

Per-product exact identity:

```text
bzip2-1.0.8-3-aarch64-linux-android.tar.gz    PASS
libffi-3.4.4-3-aarch64-linux-android.tar.gz   PASS
openssl-3.5.7-0-aarch64-linux-android.tar.gz  PASS
sqlite-3.50.4-0-aarch64-linux-android.tar.gz  PASS
xz-5.4.6-1-aarch64-linux-android.tar.gz       PASS
zstd-1.5.7-2-aarch64-linux-android.tar.gz     PASS
```

## Promoted contract

Canonical lock:

```text
config/dependencies/android-source-deps-aarch64-linux-android.lock.json
```

The lock records:

```text
name
version
recipe revision
release tag
target
filename
canonical source URL
compressed size
SHA-256
tar member structure
```

It deliberately excludes:

```text
machine-local cache path
download timestamp
filesystem mtime
```

This means a dependency cache is accepted only when its stable product identity matches the tracked contract, regardless of where that cache is stored.

## Product boundary

The producer unpacks all six archives into a shared target prefix, then configures and installs CPython into that same prefix:

```text
six immutable dependency archives
    -> merged dependency prefix
    -> CPython configure/link input
    -> composite CPython development/install prefix
```

The replay prefix is therefore not itself a minimal runtime definition.

## Exact scope of the claim

Phase 3 proves:

> The exact binary dependency products consumed by the frozen Phase 2 replay are explicit, immutable, tracked, and independently re-verifiable.

Phase 3 does not prove:

```text
reproducible source builds of the six dependency projects
source archive identity for their upstream source trees
byte-reproducible regeneration of the six binary archives
final runtime archive membership
Stage 3-A closure equivalence
```

Those claims must not be inferred from the promoted binary product lock.

## Frozen conclusion

```text
STAGE3B_PHASE3=FROZEN
STAGE3B_PHASE4=READY
```

Phase 4 must now promote explicit CPython development and runtime product boundaries without treating the complete composite prefix as a final runtime by default.
