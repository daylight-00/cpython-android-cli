# Stage 3-B Phase 4.1 Metadata Delta Capture: Step 5

> **Status:** PASS — schema preserved, exact critical-value review pending
> **Final marker:** `STAGE3B_METADATA_DELTA_CAPTURE=PASS`

## Parsed files

```text
_sysconfig_vars__android_aarch64-linux-android.json
_sysconfigdata__android_aarch64-linux-android.py
build-details.json
config-3.14-aarch64-linux-android/Makefile
config-3.14-aarch64-linux-android/config.c
```

All five parsed successfully.

## Key-space stability

| Surface | Historical keys | Package keys | Equal values | Different values | Added/removed keys |
|---|---:|---:|---:|---:|---:|
| sysconfig vars JSON | 1098 | 1098 | 987 | 111 | 0 |
| sysconfigdata Python | 1083 | 1083 | 972 | 111 | 0 |
| build-details JSON | 32 | 32 | 31 | 1 | 0 |
| installed Makefile | 442 | 442 | 411 | 31 | 0 |

No structured metadata schema gained or lost a key.

## Delta concentration

The 111 sysconfig differences concentrate in:

```text
host/build identity
compiler and binutils paths
configure arguments
CFLAGS/LDFLAGS and derived module flags
source/build workspace paths
build-Python and freeze-module paths
Git-derived producer fields
generated command paths
user/build scheme residue
```

The 31 Makefile differences are a subset of the same producer-expanded surface.

## config.c

The generated C configuration has the same 122-line structure. Its only unified-diff hunk changes the generator input comment:

```diff
-/* Generated automatically from ../../Modules/config.c.in by makesetup. */
+/* Generated automatically from ../../source/Modules/config.c.in by makesetup. */
```

No module table content changed.

## Producer-token evidence

```text
historical macOS workspace tokens  142
replay Linux workspace tokens      163
darwin NDK prebuilt tokens          20
linux NDK prebuilt tokens           20
macOS host identity tokens           9
Linux host identity tokens          38
/usr/local prefix tokens             0
```

The token distribution supports a producer-host/path delta interpretation and does not show an install-prefix contract change in the differing values.

## Remaining exact review

Before closing the metadata surface, exact old/new values must be reviewed for:

```text
BUILD_GNU_TYPE
GITBRANCH
GITTAG
GITVERSION
CONFIG_ARGS
CC / AR
PYTHON_FOR_BUILD
PYTHON_FOR_FREEZE
abs_builddir / abs_srcdir / srcdir
userbase
build-details suffixes.extensions[0]
```

This prevents source-identity or runtime-suffix drift from being hidden inside a broad “metadata only” label.
