# Stage 3-B Phase 3 Dependency Input Capture

> **Status:** CAPTURED — promoted lock verification pending
> **Source replay:** frozen Stage 3-B Phase 2
> **Target:** aarch64-linux-android

## Purpose

This record preserves the low-level transition from incidental download-cache files to explicit dependency product identities.

The Phase 2 replay proved that the six archives were sufficient to build CPython. That success alone did not prove which exact bytes were consumed. Phase 3 therefore inspected the cached files without extracting, rewriting, redownloading, or deleting them.

Observed marker:

```text
STAGE3B_DEPENDENCY_INPUT_CAPTURE=PASS
```

## Identity layers

The capture distinguishes:

```text
release declaration
  name + version + recipe revision + target

remote product identity
  release tag + canonical URL + filename

byte identity
  SHA-256 + compressed size

archive structure
  member types + declared file bytes + top-level paths

machine-local observation
  cache_path
```

Only the first four layers belong in the tracked lock. The machine-local cache path remains generated evidence.

## Captured products

| Product | Release | Bytes | SHA-256 |
|---|---:|---:|---|
| bzip2 | 1.0.8-3 | 197400 | `2385f46e173d525f079946957c007000a8ad11d8496ba66bae99129183d74bd9` |
| libffi | 3.4.4-3 | 42455 | `9f2c0255ce025c177d44db16174ad5158c7560efe3c7ef0c8c0c64b2196e6a9d` |
| openssl | 3.5.7-0 | 6321792 | `3d62143ba57f17dfa25816b1ce06256944cb23e5bad1212a419cfd073b1eebab` |
| sqlite | 3.50.4-0 | 1287749 | `f446f18d381ed641cb9d58b4768097f9cb7fcce79f7d13be371ee089f2c93e27` |
| xz | 5.4.6-1 | 651211 | `320b76d45dc3499cf855e5310f875cba61c2608e4a98bb280cc4f1b8f189da1a` |
| zstd | 1.5.7-2 | 490959 | `c3ae98fbe54b0cef9601d9dc120ed692d79609087e6926c70d8fc30face07fe7` |

Combined compressed size:

```text
8,991,566 bytes
```

## Archive structure

| Product | Members | Files | Directories | Symlinks | Declared file bytes | Top-level paths |
|---|---:|---:|---:|---:|---:|---|
| bzip2 | 26 | 17 | 5 | 4 | 426553 | bin, include, lib, man |
| libffi | 18 | 11 | 7 | 0 | 190956 | include, lib, share |
| openssl | 169 | 158 | 9 | 2 | 22016703 | bin, include, lib |
| sqlite | 15 | 6 | 7 | 2 | 2939515 | bin, include, lib, share |
| xz | 164 | 120 | 13 | 31 | 2529682 | bin, include, lib, share |
| zstd | 8 | 5 | 3 | 0 | 2411257 | include, lib |

No hardlinks were observed.

## Product-boundary interpretation

These archives are upstream prebuilt Android dependency-prefix fragments. During host configuration, `Android/android.py` unpacks all six into the target prefix before CPython is built and installed.

Therefore:

```text
six immutable archives
    -> merged target dependency prefix
    -> CPython configure/link input
    -> CPython install added to the same prefix
```

The final replay prefix is a composite development/install tree. This explains why archive identity promotion must precede runtime pruning or Stage 3-A equivalence comparison.

Phase 3 does not claim that these archives were rebuilt reproducibly from their own source repositories. It promotes the exact binary products consumed by the successful replay.

## Tracked promotion

Canonical lock:

```text
config/dependencies/android-source-deps-aarch64-linux-android.lock.json
```

Verification intentionally excludes `cache_path` and compares all stable identity and archive-structure fields exactly.

Run:

```sh
bash experiments/stage3b-dependency-promotion/verify-promoted-inputs.sh
```

Expected marker:

```text
STAGE3B_DEPENDENCY_INPUT_VERIFY=PASS
```
