# Stage 3-A Sysconfig Absolute-Path Census Summary

> **Status:** Selected evidence
> **Stage:** 3-A
> **Result:** PASS with real build-prefix residue and bounded non-runtime paths

## Purpose

This summary freezes the extractor-v2 census of absolute-path-bearing `sysconfig` values and install-scheme paths observed from the relocated Stage 2 runtime.

The v2 extractor rejects relative `../...` paths that were misclassified by the original v1 parser and runs regression self-checks before collecting data.

## Extractor validation

Observed:

```text
extractor_version=2
extractor_self_check=PASS
```

Regression cases include:

```text
../..                         -> reject
../Include/internal           -> reject
/usr/local/...                -> accept
-I/abs/include                -> accept
-L/abs/lib                    -> accept
--sysroot=/ndk/sysroot        -> accept
-Wl,-rpath,/runtime/lib       -> accept
```

## Final v2 census result

Observed:

```text
absolute_path_record_count                 179
build_prefix_residue_record_count           25
build_prefix_residue_unique_path_count      12

default_scheme:
  posix_prefix
```

Classification counts:

```text
ANDROID_SYSTEM           1
BUILD_PREFIX_RESIDUE    25
OTHER_ABSOLUTE          97
RUNTIME_PREFIX          56
```

No `TERMUX_PREFIX` record appeared in the v2 census.

## Interpretation

The runtime exposes a mixed metadata surface:

```text
runtime-prefix-aware paths
    +
real stale build-prefix paths
    +
other absolute paths requiring role-based interpretation
```

The concrete stale metadata includes:

```text
DESTSHARED=/usr/local/lib/python3.14/lib-dynload
```

The v2 census confirms that this is not an isolated parser artifact: 25 records across 12 unique `/usr/local` paths remain in the metadata surface.

## Relationship to runtime correctness

This metadata result does not invalidate the frozen runtime behavior.

The same runtime has demonstrated:

```text
whole-prefix runtime relocation                PASS
67/67 isolated extension imports               PASS
9 unique ELF SONAME dependency names
5/5 Android-system SONAME dlopen probes        PASS
0 unresolved DT_NEEDED edges
0 Termux native-library provider edges
```

The working distinction is:

```text
runtime execution correctness
    !=
development metadata relocation correctness
```

## Next analysis layer

The census is complemented by:

```text
STAGE3A_SYSCONFIG_PATH_ANALYSIS_SUMMARY.md
```

which separates path existence and role.
