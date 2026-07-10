# Stage 3-A Zoneinfo Boundary Summary

> **Status:** Selected evidence
> **Stage:** 3-A
> **Result:** FAIL for all tested base-runtime data-source scenarios

## Purpose

This summary records the non-ELF timezone-data boundary probe for the relocated Stage 2 runtime.

The probe tested whether `zoneinfo.ZoneInfo` could resolve representative IANA zone keys from:

```text
1. the runtime's default configured TZPATH;
2. first-party Python tzdata package fallback only;
3. an explicit Termux `$PREFIX/share/zoneinfo` directory.
```

Representative keys:

```text
UTC
Asia/Seoul
America/New_York
```

## Default scenario

Observed configured search path:

```text
/usr/share/zoneinfo
/usr/lib/zoneinfo
/usr/share/lib/zoneinfo
/etc/zoneinfo
```

All four directories were absent.

Observed:

```text
tzdata_spec_found=false
UTC                  FAIL
Asia/Seoul           FAIL
America/New_York     FAIL
```

Frozen interpretation:

> The base runtime has configured POSIX-style timezone search paths, but none of those paths exist on the tested device and no Python `tzdata` package is available.

## tzdata-only fallback scenario

The probe set:

```text
PYTHONTZPATH=""
```

which forces `zoneinfo` to ignore system TZPATH directories and rely on the Python `tzdata` package fallback.

Observed:

```text
zoneinfo.TZPATH=[]
tzdata_spec_found=false
UTC                  FAIL
Asia/Seoul           FAIL
America/New_York     FAIL
```

Frozen interpretation:

> The base runtime does not currently include the first-party Python `tzdata` package.

## Explicit Termux zoneinfo scenario

The probe set:

```text
PYTHONTZPATH=/data/data/com.termux/files/usr/share/zoneinfo
```

Observed:

```text
termux_zoneinfo_exists=false
UTC                  FAIL
Asia/Seoul           FAIL
America/New_York     FAIL
```

Frozen interpretation:

> The tested Termux environment did not expose a POSIX-style zoneinfo tree at `$PREFIX/share/zoneinfo`.

This result does not claim that no Termux package can provide such data. It only records the tested environment state.

## Overall result

```text
default             FAIL
tzdata_only         FAIL
termux_zoneinfo     FAIL
```

The runtime Python process itself exited normally in each scenario; the failure was specifically inability to resolve IANA zone keys.

## CPython data-source model

CPython `zoneinfo` searches configured `TZPATH` directories first and falls back to the first-party `tzdata` package. If neither source is available, `ZoneInfo` raises `ZoneInfoNotFoundError`.

The observed behavior matches that model exactly:

```text
configured TZPATH directories absent
    +
tzdata package absent
    ->
ZoneInfoNotFoundError
```

## Android boundary note

Android itself ships and updates timezone rule data for platform components, but Android's platform time-zone data path and format are not automatically exposed as the POSIX-style per-key TZif directory tree searched by CPython `zoneinfo`.

The Stage 3-A probe therefore treats Android platform timezone data and CPython `zoneinfo` data sourcing as separate integration domains.

## Architecture consequence

Timezone data is now a confirmed non-ELF runtime dependency gap.

Current tested state:

```text
native ELF closure              resolved
extension execution             PASS
CA trust source                 Termux host integration
zoneinfo source                 missing
```

The next experiment should compare a non-mutating Python `tzdata` package fallback against any host-provided timezone database option before choosing a distribution contract.

## Next experiment

Use uv to run the frozen interpreter in an ephemeral environment containing only the first-party `tzdata` package, force:

```text
PYTHONTZPATH=""
```

and re-run the representative ZoneInfo keys.

This tests whether the Python package fallback cleanly solves the timezone boundary without modifying the base runtime prefix.
