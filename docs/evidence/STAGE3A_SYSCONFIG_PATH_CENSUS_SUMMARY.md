# Stage 3-A Sysconfig Absolute-Path Census Summary

> **Status:** Selected evidence
> **Stage:** 3-A
> **Result:** PASS with significant metadata residue

## Purpose

This summary freezes the first complete census of absolute-path-bearing `sysconfig` values and install-scheme paths observed from the relocated Stage 2 runtime during Stage 3-A.

The census was introduced after the extension import probe found that runtime execution paths were relocation-aware while:

```text
DESTSHARED=/usr/local/lib/python3.14/lib-dynload
```

remained a stale build-time absolute path.

## Result

Observed summary:

```text
absolute_path_record_count                 291
build_prefix_residue_record_count           25
build_prefix_residue_unique_path_count      12

default_scheme:
  posix_prefix
```

Classification counts:

```text
ANDROID_SYSTEM           1
BUILD_PREFIX_RESIDUE    25
OTHER_ABSOLUTE         209
RUNTIME_PREFIX          56
```

No `TERMUX_PREFIX` record appeared in the first sysconfig path census.

## Immediate interpretation

The result shows that the stale `DESTSHARED` value is not an isolated one-off metadata artifact.

At least:

```text
25 records
12 unique /usr/local-prefixed paths
```

remain in the observed sysconfig metadata surface.

At the same time, 56 absolute-path records were correctly rooted in the active relocated runtime prefix.

Therefore the current Python installation exposes a mixed metadata model:

```text
runtime-aware paths
    +
build-prefix residue
    +
a large OTHER_ABSOLUTE set requiring further classification
```

## What the 209 OTHER_ABSOLUTE records do not mean

The census records path-like absolute substrings found inside:

```text
sysconfig config vars
install-scheme paths
compiler and linker command fragments
build configuration strings
```

Therefore:

```text
OTHER_ABSOLUTE record count
    !=
runtime external dependency count
```

The 209 records must be decomposed before any dependency or packaging claim is made.

Possible categories include:

```text
host build workspace residue
Android NDK/toolchain paths
compiler command fragments
sysroot paths
source-tree paths
runtime-useful paths
nonexistent historical build paths
actual external runtime filesystem dependencies
```

Stage 3-A must distinguish these categories empirically.

## Relationship to runtime correctness

This census does not invalidate the frozen Stage 2 runtime result.

The same runtime has already demonstrated:

```text
whole-prefix runtime relocation                PASS
67/67 isolated extension imports               PASS
9 unique ELF SONAME dependency names
5/5 Android-system SONAME dlopen probes        PASS
0 unresolved DT_NEEDED edges
0 Termux native-library provider edges
```

The sysconfig result instead identifies a new layer:

```text
runtime execution correctness
    !=
development metadata relocation correctness
```

## Stage 3 design implication

The evidence strengthens the case for treating at least two possible distribution contracts separately:

```text
runtime distribution
    execution-oriented
    relocation behavior validated
    Python/stdlib/extensions/native runtime closure

full/development distribution
    headers
    libpython development artifacts
    sysconfig correctness
    compiler/linker metadata
    native extension build workflows
```

This distinction is not yet frozen as final Stage 3-C design, but the sysconfig census provides evidence that a single undifferentiated archive may hide materially different requirements.

## Next analysis step

The next Stage 3-A analysis must decompose:

```text
OTHER_ABSOLUTE=209
```

and the 25 build-prefix residue records by:

```text
source key
path existence
unique path
common top-level prefix
config-var vs scheme-path origin
```

The repository analysis helper generates:

```text
sysconfig-path-analysis-summary.json
sysconfig-other-prefix-counts.tsv
sysconfig-build-residue-key-counts.tsv
sysconfig-path-key-counts.tsv
sysconfig-other-absolute-analysis.tsv
sysconfig-build-residue-analysis.tsv
```

Only after reviewing those outputs should Stage 3-A decide which path records represent:

```text
runtime requirements
build-only metadata
historical residue
or probe parsing artifacts
```

This summary is evidence for `docs/stages/STAGE3_SCOPE.md`.
