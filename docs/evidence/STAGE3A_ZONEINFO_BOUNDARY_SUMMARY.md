# Stage 3-A Zoneinfo Boundary Summary

> **Status:** Selected historical evidence with a later probe-contract correction
> **Stage:** 3-A
> **Result:** Default lookup failure and host-path absence observed; direct `PYTHONTZPATH` scenarios reopened

## Purpose

This summary records the non-ELF timezone-data boundary probe for the relocated Stage 2 runtime and the later correction discovered while preparing Stage 3-B Phase 5 promoted-runtime equivalence.

The original probe intended to test whether `zoneinfo.ZoneInfo` could resolve representative IANA zone keys from:

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

## Later probe-contract correction

The original fresh-process child was invoked with:

```text
python -I -c ...
```

while scenarios 2 and 3 attempted to set:

```text
PYTHONTZPATH=""
PYTHONTZPATH=$PREFIX/share/zoneinfo
```

CPython isolated mode ignores all `PYTHON*` environment variables. Therefore the direct child could not consume the `PYTHONTZPATH` value under test.

The historical output remains useful, but its claim boundary is narrower than originally documented.

Still supported:

```text
default lookup failed for all representative keys
default configured TZPATH directories were absent
base runtime did not expose a visible tzdata package in that child
$PREFIX/share/zoneinfo was absent at the outer filesystem check
```

Reopened for corrected execution:

```text
PYTHONTZPATH="" produced an empty zoneinfo.TZPATH
PYTHONTZPATH=$PREFIX/share/zoneinfo selected the explicit Termux path
per-scenario failures were caused by those delivered environment inputs
```

The corrected probe is documented in:

```text
docs/evidence/STAGE3B_PHASE5_BOUNDARY_PROBE_REASSESSMENT.md
```

It removes `-I`, sanitizes ambient `PYTHON*` variables, applies only the intended scenario input, and uses:

```text
python -B -P -s -c ...
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

Interpretation retained after correction:

> The base runtime's default child state had configured POSIX-style timezone search paths, none of those paths existed on the tested device, and no Python `tzdata` package was visible.

## Historical tzdata-only scenario

The probe wrapper attempted to set:

```text
PYTHONTZPATH=""
```

The intended meaning was to force `zoneinfo` to ignore system TZPATH directories and rely on the Python `tzdata` package fallback.

Historical output recorded:

```text
zoneinfo.TZPATH=[]
tzdata_spec_found=false
UTC                  FAIL
Asia/Seoul           FAIL
America/New_York     FAIL
```

Correction:

> Because the child used `-I`, this output cannot be attributed to the wrapper's `PYTHONTZPATH` environment input without a corrected rerun.

The separate uv-injected first-party `tzdata` experiment remains valid and passed all representative keys. It did not use this invalid isolated child contract.

## Historical explicit Termux zoneinfo scenario

The probe wrapper attempted to set:

```text
PYTHONTZPATH=/data/data/com.termux/files/usr/share/zoneinfo
```

Historical output recorded:

```text
termux_zoneinfo_exists=false
UTC                  FAIL
Asia/Seoul           FAIL
America/New_York     FAIL
```

The outer filesystem observation remains valid:

> The tested Termux environment did not expose a POSIX-style zoneinfo tree at `$PREFIX/share/zoneinfo`.

The direct child result does not prove that the explicit environment input was consumed, because `-I` ignored it.

This result does not claim that no Termux package can provide such data. It records the tested environment state.

## Historical aggregate

The original report printed:

```text
default             FAIL
tzdata_only         FAIL
termux_zoneinfo     FAIL
```

The runtime Python process exited normally in each scenario; the observed failure was inability to resolve IANA zone keys.

After the contract correction, only the default scenario is accepted as a directly established scenario result from that child. The other two labels await corrected execution.

## CPython data-source model

CPython `zoneinfo` searches configured `TZPATH` directories first and falls back to the first-party `tzdata` package. If neither source is available, `ZoneInfo` raises `ZoneInfoNotFoundError`.

The default observation is consistent with:

```text
configured TZPATH directories absent
    +
tzdata package not visible
    ->
ZoneInfoNotFoundError
```

An empty `PYTHONTZPATH` is the supported way to force package-only lookup, but a test of that behavior must not use `-I` or `-E`.

## Android boundary note

Android itself ships and updates timezone rule data for platform components, but Android's platform time-zone data path and format are not automatically exposed as the POSIX-style per-key TZif directory tree searched by CPython `zoneinfo`.

The Stage 3-A probe therefore treats Android platform timezone data and CPython `zoneinfo` data sourcing as separate integration domains.

## Architecture consequence

The valid Stage 3-A and follow-up evidence supports:

```text
native ELF closure              resolved
extension execution             PASS
CA trust source                 Termux host integration
default zoneinfo source         unavailable in tested base runtime
first-party tzdata fallback     PASS through uv ephemeral injection
explicit PYTHONTZPATH controls  pending corrected direct comparison
```

The distribution-stage question remains unchanged: compare and choose among bundled, declared Python-package, or host-integrated timezone data contracts.

## Corrected next experiment

Run the corrected candidate/frozen comparison:

```sh
bash \
  experiments/stage3b-target-validation/validate-promoted-boundaries.sh
```

The machine verifier checks the actual observed `PYTHONTZPATH` value in every scenario before accepting semantic equivalence.
