# Stage 3-A tzdata Fallback Summary

> **Status:** Selected evidence
> **Stage:** 3-A
> **Result:** PASS

## Purpose

This summary records the follow-up timezone-data experiment after the base runtime failed all tested `zoneinfo` data-source scenarios.

The experiment asked:

> Can CPython's first-party `tzdata` package satisfy the timezone-data boundary without modifying the frozen base runtime prefix?

## Method

The probe used uv ephemeral dependency injection:

```text
PYTHONTZPATH=""
UV_PYTHON_DOWNLOADS=never
uv run
  --no-project
  --with tzdata
  --python <frozen runtime Python>
```

`PYTHONTZPATH=""` removed system TZPATH directories from the search path, forcing the Python-package fallback path to carry the test.

The base runtime prefix was not modified.

## Result

Observed:

```text
tzdata_spec_found=true
tzdata_version=2026.3
zoneinfo.TZPATH=[]
all_keys_pass=true
```

Representative keys:

```text
UTC                  PASS
Asia/Seoul           PASS
America/New_York     PASS
```

Runtime identity:

```text
sys.executable:
  ~/.cache/uv/builds-v0/.tmp.../bin/python

sys.prefix:
  uv ephemeral environment

sys.base_prefix:
  work/termux/stage2c/runtime/prefix
```

Final marker:

```text
ZONEINFO_UV_TZDATA_PROBE=PASS
```

## Interpretation

The timezone failure observed in the base runtime is a missing data-source problem, not a failure of the frozen CPython runtime or its `zoneinfo` implementation.

The tested first-party `tzdata` package fallback succeeds when supplied as a normal Python dependency while preserving the frozen runtime as `sys.base_prefix`.

## Distribution implication

The Stage 3 distribution design now has evidence for a Python-native timezone-data contract:

```text
base runtime
  may omit a POSIX zoneinfo tree

consumer environment
  can provide tzdata package

zoneinfo
  resolves IANA keys successfully
```

This does not yet decide whether the final runtime distribution should:

```text
bundle tzdata
make tzdata a declared runtime dependency
or expose a host POSIX TZif tree
```

It proves that the first-party package fallback is a working option on the tested target.

## uv hardlink warning

uv reported a hardlink fallback warning and then successfully installed one package by copy fallback.

Frozen interpretation:

```text
hardlink optimization:
  unavailable in the tested cache/target filesystem arrangement

copy fallback:
  successful

functional impact:
  none observed
```

## Stage 3-A consequence

Timezone data boundary status:

```text
base default TZPATH            FAIL
base tzdata fallback           FAIL: package absent
Termux zoneinfo path           FAIL: path absent
uv ephemeral tzdata fallback   PASS
```

The next non-ELF boundary to isolate is CA trust sourcing.
