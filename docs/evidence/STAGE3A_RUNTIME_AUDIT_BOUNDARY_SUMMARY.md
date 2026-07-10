# Stage 3-A Representative Runtime Audit Boundary Summary

> **Status:** Selected evidence
> **Stage:** 3-A
> **Result:** Representative workload audit complete; no new broad host filesystem dependency class observed

## Purpose

This summary records a Python audit-hook observation pass over representative runtime workloads for the frozen Stage 2 runtime.

The probe was intended to answer:

> During representative runtime activity, which filesystem and process boundaries are observed outside the runtime prefix?

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

## Result

Observed path event counts:

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

No `OTHER_ABSOLUTE`, `ANDROID_SYSTEM`, or broad `TERMUX_PREFIX` path class appeared in the summary of the observed Python-level path events.

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

This is consistent with the frozen base runtime carrying no installed Python distributions in its active environment.

HTTPS result:

```text
200
```

The active CA source remained the Termux CA bundle selected by the launcher.

## Interpretation

The representative Python-level audit did not reveal a new broad live host-filesystem dependency class beyond already-understood categories.

Observed external categories were bounded to:

```text
DEVFS
HOME_STATE
TERMUX_TEMP
```

plus:

```text
RESULT_OUTPUT
```

which is probe-generated state rather than runtime product dependency.

The exact paths and special audit events remain available in:

```text
runtime-audit-unique-paths.tsv
runtime-audit-special-events.tsv
```

and should be reviewed before final Stage 3-A freeze.

## Limitation

This probe uses Python audit hooks.

Therefore it should not be interpreted as:

```text
complete syscall trace
complete native-library open() census
proof that no unobserved external path can ever be accessed
```

Its claim is narrower:

> The tested representative Python-level workload exposed only the summarized path classes and no additional unknown broad host filesystem dependency class.

## Stage 3-A consequence

Current non-ELF boundary model:

```text
CA trust
  Termux host CA integration confirmed

Timezone data
  absent in base runtime
  first-party tzdata package fallback confirmed

Representative Python-level filesystem audit
  no new broad unknown path class observed
  exact DEVFS/HOME_STATE/TERMUX_TEMP and special events pending direct row review
```

After direct review of the unique-path and special-event tables, Stage 3-A can proceed to final Stage 2-C smoke and relocation reconfirmation before freeze.
