# Stage 3-A Sysconfig Absolute-Path Census Summary

> **Status:** PROVISIONAL EVIDENCE — extractor v1 counts superseded pending rerun
> **Stage:** 3-A
> **Result:** Directionally useful; exact counts require extractor v2 rerun

## Supersession note

The first census used a path extractor that could misclassify a slash inside a relative path as the start of an absolute path.

Concrete observed example:

```text
raw value:
  ../..

v1 extracted path candidate:
  /
```

The same issue affected relative build/source paths such as `../Include/...` and similar values.

Therefore the exact v1 counts below are preserved only as experiment history and must not be treated as final Stage 3-A counts.

The extractor was corrected in v2 to:

```text
accept standalone/delimited absolute paths
accept common -I/-L/-B/-isystem/--sysroot= absolute-path forms
reject slashes embedded in relative ../... paths
```

The census, analysis, and triage must be rerun before this document is promoted back to selected final evidence.

## Original v1 observation

The v1 run reported:

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

The important durable observation from this run is not the exact count. It is that the relocated runtime exposes a mixed metadata surface containing both runtime-aware paths and stale build/development paths, including:

```text
DESTSHARED=/usr/local/lib/python3.14/lib-dynload
```

That concrete stale value remains valid evidence independently of the v1 extraction bug.

## Relationship to runtime correctness

This metadata finding does not invalidate the frozen Stage 2 runtime result.

The same runtime has demonstrated:

```text
whole-prefix runtime relocation                PASS
67/67 isolated extension imports               PASS
9 unique ELF SONAME dependency names
5/5 Android-system SONAME dlopen probes        PASS
0 unresolved DT_NEEDED edges
0 Termux native-library provider edges
```

The working distinction remains:

```text
runtime execution correctness
    !=
development metadata relocation correctness
```

## Required rerun

Run, in order:

```text
probe-sysconfig-paths.sh
analyze-sysconfig-paths.sh
triage-sysconfig-paths.sh
```

Only the extractor-v2 outputs should be used for final Stage 3-A path counts and classification claims.
