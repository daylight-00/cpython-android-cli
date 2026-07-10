# Stage 3-A Sysconfig Missing-Path Classifier Result

> **Status:** Selected evidence
> **Stage:** 3-A
> **Result:** PASS

## Purpose

This summary records the machine-classifier verification of the manually reviewed extractor-v2 missing sysconfig path set.

Input:

```text
91 records
27 unique paths
```

## Result

Observed category record counts:

```text
BUILD_WORKSPACE_RESIDUE          58
HOST_BUILD_TOOL_RESIDUE           5
TOOLCHAIN_RESIDUE                 8
TZDATA_SEARCH_PATH_METADATA       4
USER_SCHEME_DESTINATION          16
```

Observed category unique-path counts:

```text
BUILD_WORKSPACE_RESIDUE          10
HOST_BUILD_TOOL_RESIDUE           1
TOOLCHAIN_RESIDUE                 3
TZDATA_SEARCH_PATH_METADATA       4
USER_SCHEME_DESTINATION           9
```

Closure checks:

```text
record_count=91
unique_path_count=27
unknown_record_count=0
unknown_unique_path_count=0
```

Final marker:

```text
SYSCONFIG_MISSING_PATH_CLASSIFICATION=PASS
```

## Interpretation

The machine classifier reproduced the manual semantic partition without leaving an unknown bucket.

Therefore the missing extractor-v2 `OTHER_ABSOLUTE` set is closed as:

```text
build/development provenance residue
  BUILD_WORKSPACE_RESIDUE
  TOOLCHAIN_RESIDUE
  HOST_BUILD_TOOL_RESIDUE

installation destination metadata
  USER_SCHEME_DESTINATION

runtime-relevant data-source metadata requiring behavior probe
  TZDATA_SEARCH_PATH_METADATA
```

The next unresolved Stage 3-A question from this set is the actual timezone-data source boundary.
