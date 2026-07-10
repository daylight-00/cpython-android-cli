# Stage 3-A Extension Import Sweep Summary

> **Status:** Selected evidence
> **Stage:** 3-A
> **Result:** PASS

## Purpose

This summary freezes the isolated extension-module import sweep performed against the frozen Stage 2 runtime during Stage 3-A closure analysis.

The sweep was designed to answer:

> Do all extension modules present in the active runtime dynamic-load directory import successfully when each is tested in a fresh runtime-Python subprocess?

## Initial discovery failure

The first probe attempted to use:

```text
sysconfig.get_config_var("DESTSHARED")
```

as the authoritative extension directory.

Observed value:

```text
/usr/local/lib/python3.14/lib-dynload
```

That path did not exist in the relocated runtime.

The first probe therefore failed before importing any extension modules.

Frozen interpretation:

> The failure was a probe discovery error, not an extension-import failure. The active relocated runtime paths and at least some sysconfig build metadata paths are different problem domains.

## Corrected discovery policy

The corrected probe uses runtime-observed paths first:

```text
1. active sys.path entry named lib-dynload
2. sys.base_prefix-derived lib/pythonX.Y/lib-dynload
3. sysconfig platstdlib-derived candidate
4. configured DESTSHARED as a final fallback
```

The successful discovery result was:

```text
configured DESTSHARED:
  /usr/local/lib/python3.14/lib-dynload

selected extension directory:
  /data/data/com.termux/files/home/projects/cpython-android-cli/work/termux/stage2c/runtime/prefix/lib/python3.14/lib-dynload

selected method:
  sys.path
```

The observed runtime identity was:

```text
sys.prefix:
  /data/data/com.termux/files/home/projects/cpython-android-cli/work/termux/stage2c/runtime/prefix

sys.base_prefix:
  /data/data/com.termux/files/home/projects/cpython-android-cli/work/termux/stage2c/runtime/prefix
```

and active `sys.path` included the relocated runtime:

```text
<runtime-prefix>/lib/python314.zip
<runtime-prefix>/lib/python3.14
<runtime-prefix>/lib/python3.14/lib-dynload
<runtime-prefix>/lib/python3.14/site-packages
```

## Import probe method

The probe enumerated extension files in the selected active runtime extension directory using `importlib.machinery.EXTENSION_SUFFIXES`.

Each candidate was imported in a separate process:

```text
runtime python
    -I
    -S
    -c importlib.import_module(module)
```

This isolation ensures:

```text
one module failure does not hide later results
one native loader failure is attributed to one module
one process crash does not abort the complete sweep
```

## Result

Observed summary:

```text
extension_candidate_count    67
import_pass_count             67
import_fail_count              0
EXTENSION_IMPORT_PROBE      PASS
```

Frozen interpretation:

> Every extension-module candidate discovered in the active runtime `lib-dynload` directory imported successfully in its own fresh isolated subprocess on the tested runtime and device.

## Relationship to the ELF closure census

The earlier Stage 3-A closure census found:

```text
81 ELF objects
329 DT_NEEDED edges
9 unique SONAMEs
4 runtime-internal unique SONAMEs
5 Android-system unique SONAMEs
0 unresolved edges
5/5 Android-system SONAME dlopen probes PASS
```

The extension import sweep adds behavioral evidence on top of the static graph:

```text
static dependency census
    +
Android-system SONAME loadability probe
    +
67/67 isolated extension imports
```

Together, these support a strong native runtime-closure result for the tested target.

## Important metadata finding

The successful runtime is relocation-aware for active execution paths, while `DESTSHARED` retains the build-time absolute path:

```text
runtime execution paths:
  relocated prefix paths
  functional

DESTSHARED metadata:
  /usr/local/lib/python3.14/lib-dynload
  stale for the relocated runtime
```

This finding does not invalidate Stage 2 runtime relocation.

It creates a Stage 3 distribution/development metadata question:

```text
Which sysconfig values are runtime-relative?
Which retain build-time absolute paths?
Which stale values affect runtime-only consumers?
Which stale values affect native extension builds and development workflows?
```

## Next Stage 3-A step

The next observational step is a complete sysconfig absolute-path residue census.

The census should classify path-bearing sysconfig variables and scheme paths into:

```text
RUNTIME_PREFIX
TERMUX_PREFIX
ANDROID_SYSTEM
BUILD_PREFIX_RESIDUE
OTHER_ABSOLUTE
```

and record whether each referenced path exists.

This summary is evidence for `docs/stages/STAGE3_SCOPE.md`.
