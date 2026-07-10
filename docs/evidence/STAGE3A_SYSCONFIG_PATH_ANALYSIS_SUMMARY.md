# Stage 3-A Sysconfig Path Analysis Summary

> **Status:** Selected evidence
> **Stage:** 3-A
> **Result:** PASS with strong evidence of mostly non-live absolute-path residue

## Purpose

This summary freezes the first decomposition of the absolute-path records previously observed in the relocated runtime's `sysconfig` metadata surface.

The prior census found:

```text
absolute_path_record_count             291
BUILD_PREFIX_RESIDUE                    25
OTHER_ABSOLUTE                         209
RUNTIME_PREFIX                          56
ANDROID_SYSTEM                           1
```

The purpose of this analysis was to distinguish live filesystem references from stale or historical metadata residue.

## Result

Observed existence counts:

```text
ANDROID_SYSTEM:yes            1
BUILD_PREFIX_RESIDUE:no      25
OTHER_ABSOLUTE:no           202
OTHER_ABSOLUTE:yes            7
RUNTIME_PREFIX:no            20
RUNTIME_PREFIX:yes           36
```

Observed unique-path counts:

```text
ANDROID_SYSTEM                 1
BUILD_PREFIX_RESIDUE          12
OTHER_ABSOLUTE                92
RUNTIME_PREFIX                12
```

Additional aggregation:

```text
build_residue_key_count              21
other_absolute_top_prefix_count      43
```

## Immediate interpretation

The result strongly constrains the meaning of the previously observed `OTHER_ABSOLUTE=209` count.

Of those records:

```text
202 do not exist on the tested runtime host
7 exist
```

Therefore:

```text
OTHER_ABSOLUTE record count
    !=
external runtime dependency count
```

Most observed absolute-path records are not live filesystem paths on the tested device.

Likewise, all 25 `/usr/local` build-prefix residue records were nonexistent:

```text
BUILD_PREFIX_RESIDUE:no = 25
BUILD_PREFIX_RESIDUE:yes = 0
```

This supports interpreting the `/usr/local` paths as stale build/development metadata rather than live runtime dependencies on the tested environment.

## What remains unresolved

Seven `OTHER_ABSOLUTE` records refer to paths that exist on the tested device.

Those seven records must be reviewed individually before making a final non-ELF external-dependency claim.

Possible interpretations include:

```text
Android runtime filesystem paths
shell or command paths
Termux host paths not rooted under the configured Termux prefix classifier
procfs/devfs paths
shared temporary paths
actual external runtime resources
```

The analysis count alone is insufficient to choose among these categories.

## Runtime-prefix path records

The census also found:

```text
RUNTIME_PREFIX:yes = 36
RUNTIME_PREFIX:no  = 20
```

A missing runtime-prefix-derived path is not automatically a defect.

Possible reasons include:

```text
optional install-scheme destinations
header/development paths omitted from runtime-only layout
script/data destinations not created yet
metadata paths that are valid layout conventions but currently absent
```

These 20 records should therefore be analyzed by key and role rather than treated as runtime failures.

## Stage 3 design implication

The current evidence increasingly supports separating:

```text
runtime execution contract
    currently strong

from

development/build metadata contract
    currently mixed and partially stale
```

The tested runtime already has strong execution evidence:

```text
whole-prefix relocation PASS
native ELF closure census complete
0 unresolved DT_NEEDED edges
5/5 Android-system SONAME dlopen probes PASS
67/67 isolated extension imports PASS
Stage 2-C smoke PASS
```

By contrast, development metadata contains:

```text
25 stale /usr/local records
12 unique /usr/local paths
92 unique OTHER_ABSOLUTE paths
202 nonexistent OTHER_ABSOLUTE records
7 existing OTHER_ABSOLUTE records requiring review
```

## Next triage step

The next Stage 3-A step is to inspect:

```text
1. the 7 existing OTHER_ABSOLUTE records exactly;
2. the top-prefix and key distribution of the 202 missing OTHER_ABSOLUTE records;
3. the keys associated with the 20 nonexistent RUNTIME_PREFIX records.
```

The repository triage helper should produce explicit tables for those categories before Stage 3-A moves to broader non-ELF runtime dependency probing.

This summary is evidence for `docs/stages/STAGE3_SCOPE.md`.
