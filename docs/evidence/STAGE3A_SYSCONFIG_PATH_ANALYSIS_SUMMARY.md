# Stage 3-A Sysconfig Path Analysis Summary

> **Status:** PROVISIONAL EVIDENCE — based on extractor v1 output
> **Stage:** 3-A
> **Result:** Qualitative conclusions retained; exact counts superseded pending extractor v2 rerun

## Supersession note

The analysis summarized an absolute-path census produced by extractor v1.

Triage exposed a concrete parsing artifact:

```text
config_var VPATH
raw value: ../..
v1 extracted candidate: /
```

Relative source/build paths were therefore able to enter the v1 absolute-path dataset.

The exact v1 counts below are preserved as historical experiment output only:

```text
ANDROID_SYSTEM:yes            1
BUILD_PREFIX_RESIDUE:no      25
OTHER_ABSOLUTE:no           202
OTHER_ABSOLUTE:yes            7
RUNTIME_PREFIX:no            20
RUNTIME_PREFIX:yes           36
```

and:

```text
ANDROID_SYSTEM unique paths          1
BUILD_PREFIX_RESIDUE unique paths   12
OTHER_ABSOLUTE unique paths         92
RUNTIME_PREFIX unique paths         12
```

These numbers must be regenerated with extractor v2 before use in final Stage 3-A claims.

## Durable observations from the v1 triage

Several qualitative conclusions remain useful because they came from direct row inspection rather than aggregate counts.

### Active user install paths

The existing non-runtime-prefix paths inspected were:

```text
/data/data/com.termux/files/home/.local
/data/data/com.termux/files/home/.local/bin
```

They came from `userbase` and user install schemes. These are installation destinations, not evidence that base interpreter execution requires those paths.

### Inactive scheme paths

The inspected missing runtime-prefix paths came from:

```text
nt
nt_venv
posix_home
```

while the active default scheme was:

```text
posix_prefix
```

Therefore those missing paths must not be reported as defects in the active runtime layout.

### Concrete stale metadata

The concrete stale value:

```text
DESTSHARED=/usr/local/lib/python3.14/lib-dynload
```

remains valid evidence independently of the parser bug.

## Required next step

Regenerate all sysconfig path outputs with extractor v2:

```text
probe-sysconfig-paths.sh
analyze-sysconfig-paths.sh
triage-sysconfig-paths.sh
```

Only the regenerated counts should be promoted into final selected evidence.
