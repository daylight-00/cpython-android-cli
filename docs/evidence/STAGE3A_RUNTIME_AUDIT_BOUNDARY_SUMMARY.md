# Stage 3-A Representative Runtime Audit Boundary Summary

> **Status:** Selected evidence
> **Stage:** 3-A
> **Result:** Representative workload audit complete; exact rows reviewed and classified

## Purpose

This summary records a Python audit-hook observation pass over representative runtime workloads for the frozen Stage 2 runtime.

The probe asked:

> During representative runtime activity, which filesystem, subprocess, dlopen, and network boundaries are observed outside the runtime prefix?

This is an observational probe, not an exhaustive syscall trace. Python audit hooks do not capture every native-library filesystem access.

## Workload

The observed workload included:

```text
ssl default verify paths
HTTPS request to PyPI
mimetypes initialization
locale initialization and preferred encoding
runtime temporary directory discovery
SQLite in-memory database use
ctypes loading of libc.so
multiprocessing method discovery
platform identity
sysconfig path discovery
importlib.metadata distribution enumeration
zoneinfo UTC lookup
```

## Aggregate result

Observed:

```text
path_event_count=26
special_event_count=5
```

Path classification record counts:

```text
DEVFS            2
HOME_STATE       1
RESULT_OUTPUT    8
RUNTIME_PREFIX  14
TERMUX_TEMP      1
```

Unique path counts:

```text
DEVFS            1
HOME_STATE       1
RESULT_OUTPUT    8
RUNTIME_PREFIX  13
TERMUX_TEMP      1
```

No `OTHER_ABSOLUTE`, `ANDROID_SYSTEM`, or broad `TERMUX_PREFIX` path class appeared in the observed Python-level path events.

## Workload result matrix

Observed PASS:

```text
ctypes_libc
https_pypi
locale_preferred_encoding
locale_setlocale
metadata_distribution_count
mimetypes_init
multiprocessing_methods
platform
sqlite_memory
ssl_default_verify_paths
sysconfig_paths
tempdir
```

Observed FAIL:

```text
zoneinfo_UTC
```

The zoneinfo failure is not a new unknown. Earlier Stage 3-A evidence already established:

```text
base runtime zoneinfo source absent
uv ephemeral tzdata fallback PASS
```

The audit therefore reconfirmed the known timezone-data boundary under the clean base-runtime environment.

## Exact-row review result

The exact-row review is complete and frozen separately in:

```text
STAGE3A_RUNTIME_AUDIT_EXACT_ROW_REVIEW.md
```

The observed external boundaries reduce to:

```text
/dev/null
    normal device boundary

project experiment directory under $HOME
    probe-code location, not generic home-state dependency

$PREFIX/tmp
    temporary-storage integration

libc.so
    already-characterized Android native boundary

network :443
    deliberate HTTPS workload

file / uname
    optional platform-information helper commands
```

No exact observed row remains semantically unknown.

## Notable runtime observations

Locale behavior:

```text
locale.setlocale(LC_CTYPE, "") -> C.UTF-8
preferred encoding             -> utf-8
```

Temporary directory:

```text
/data/data/com.termux/files/usr/tmp
```

Platform identity:

```text
Android-16-aarch64-64bit-ELF
```

Metadata distribution count:

```text
0
```

HTTPS result:

```text
200
```

The active CA source remained the Termux CA bundle selected by the launcher.

## Interpretation

The representative Python-level audit did not reveal a new broad live host-filesystem dependency class beyond already-understood categories.

The original `HOME_STATE` aggregate label was reviewed and found to refer to the repository experiment directory, because the repository itself resides under Termux `$HOME`.

The `TERMUX_TEMP` path was a temporary path under `$PREFIX/tmp` and was absent after the workload.

The `RESULT_OUTPUT` paths were redirected `PYTHONPYCACHEPREFIX` destinations created by the probe environment, not runtime product dependencies.

The two `subprocess.Popen` events were induced by the explicit `platform.platform()` workload:

```text
file -b <runtime-python>
uname -p
```

and are classified as optional host-command dependencies of that information path rather than core interpreter startup dependencies.

## Limitation

This probe uses Python audit hooks.

Therefore it should not be interpreted as:

```text
complete syscall trace
complete native-library open() census
proof that no unobserved external path can ever be accessed
```

Its exact claim is:

> Every path and special event observed in the tested representative Python-level workload has been classified, and no new unknown broad host dependency boundary remains in that observed set.

## Stage 3-A consequence

Current non-ELF boundary model:

```text
CA trust
  Termux host CA integration confirmed

Timezone data
  absent in base runtime
  first-party tzdata package fallback confirmed

Temporary storage
  Termux $PREFIX/tmp observed

Representative Python-level audit
  exact rows classified
  no new unknown broad boundary observed
```

The remaining Stage 3-A work is:

```text
1. production-shape Stage 2-C smoke reconfirmation;
2. production-shape whole-prefix relocation reconfirmation;
3. freeze review and Stage 3-A final synthesis.
```
