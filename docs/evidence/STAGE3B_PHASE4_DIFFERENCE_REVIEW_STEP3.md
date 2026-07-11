# Stage 3-B Phase 4.1 Closed Difference Review: Step 3

> **Status:** PASS — mechanical review set closed
> **Final marker:** `STAGE3B_PACKAGE_DIFF_REVIEW=PASS`

## Complete mechanical classes

```text
total differences              78
ELF content differences        69
non-ELF file differences        5
historical-only paths           4
package-only paths              0
kind changes                    0
symlink-target changes          0
```

All differences are under:

```text
bin/   4
lib/  74
```

## Historical-only assembly layer

```text
bin/
bin/python3.14
bin/python3
bin/python
```

These are the project launcher and its two command-name symlinks plus their directory. They are not expected inside the upstream package because `scripts/termux/prepare-runtime.sh` installs them during project runtime assembly.

This closes the four historical-only paths as an assembly-layer distinction, not a missing upstream runtime dependency.

## ELF accounting

The counts close exactly:

```text
historical ELF objects  81
package ELF objects     80
historical-only launcher 1
```

Within the package:

```text
changed CPython ELF     69
byte-identical ELF      11
```

The 69 changed ELF paths are exactly:

```text
libpython shared objects      2
CPython extension modules    67
```

This matches the frozen Stage 3-A extension candidate count.

Interpretation:

```text
11 exact ELF
    dependency products preserved byte-for-byte

69 changed ELF
    CPython-generated native surface rebuilt by the Linux producer

1 historical-only ELF
    project launcher added during assembly
```

## Remaining gates

Byte difference alone is expected for regenerated CPython ELF objects. The next gate compares semantic consumer surfaces:

```text
ELF class/data/type/machine/flags
DT_SONAME
DT_NEEDED
DT_RPATH / DT_RUNPATH
defined and undefined dynamic symbol sets
```

Build IDs, section offsets, symbol addresses, and debug bytes are not semantic equality requirements.

The five non-ELF changed files are captured separately for exact metadata-role classification.
