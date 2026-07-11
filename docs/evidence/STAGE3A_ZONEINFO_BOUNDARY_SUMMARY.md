# Stage 3-A Zoneinfo Boundary Summary

> **Status:** Selected historical evidence with corrected follow-up confirmation
> **Stage:** 3-A, corrected during Stage 3-B Phase 5
> **Result:** Base-runtime timezone sources unavailable; first-party `tzdata` fallback PASS

## Purpose

This document records both:

```text
1. the original Stage 3-A timezone-data observation
2. the corrected Stage 3-B follow-up that repaired the original direct-scenario control
```

Representative keys:

```text
UTC
Asia/Seoul
America/New_York
```

## Original probe-contract defect

The original fresh-process child used:

```text
python -I -c ...
```

while two scenarios attempted to control:

```text
PYTHONTZPATH=""
PYTHONTZPATH=$PREFIX/share/zoneinfo
```

CPython isolated mode ignores `PYTHON*` environment variables. Therefore the original child could not prove that those two `PYTHONTZPATH` values were consumed.

The historical output still established:

```text
default lookup failed for all representative keys
default configured TZPATH directories were absent
no first-party tzdata package was visible
$PREFIX/share/zoneinfo was absent at the outer filesystem check
```

The direct environment-input claims were temporarily reopened rather than silently retained.

## Corrected child contract

Stage 3-B Phase 5 repaired the probe to:

```text
sanitize ambient PYTHON* variables
set PYTHONNOUSERSITE=1
apply only the scenario-specific PYTHONTZPATH value
run python -B -P -s -c ...
```

The child records:

```text
actual PYTHONTZPATH value
zoneinfo.TZPATH
path existence
first-party tzdata visibility
interpreter flags
per-key results
```

Corrected evidence:

```text
docs/evidence/STAGE3B_PHASE5_BOUNDARY_PROBE_REASSESSMENT.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_BOUNDARIES.md
```

## Corrected frozen-runtime result

The corrected workflow reran every scenario against the frozen Stage 2-C runtime and the promoted candidate under the same Termux host state.

Machine checks confirmed:

```text
frozen_zone_input_default             true
frozen_zone_input_tzdata_only         true
frozen_zone_input_termux_zoneinfo     true
frozen_zone_flags_default             true
frozen_zone_flags_tzdata_only         true
frozen_zone_flags_termux_zoneinfo     true
zone_child_contract                   true
zone_semantic_equivalence             true
```

The promoted candidate matched the frozen runtime exactly.

## Default scenario

Observed input:

```text
PYTHONTZPATH unset
```

Observed search path:

```text
/usr/share/zoneinfo
/usr/lib/zoneinfo
/usr/share/lib/zoneinfo
/etc/zoneinfo
```

All four paths were absent.

Observed:

```text
tzdata_spec_found=false
UTC                  FAIL
Asia/Seoul           FAIL
America/New_York     FAIL
```

Conclusion:

> The tested base runtime has configured POSIX-style timezone search paths, but none exists on the tested device and no first-party `tzdata` package is included in the base environment.

## Package-only scenario

Observed input:

```text
PYTHONTZPATH=""
```

Observed:

```text
zoneinfo.TZPATH=[]
tzdata_spec_found=false
UTC                  FAIL
Asia/Seoul           FAIL
America/New_York     FAIL
```

The corrected child explicitly recorded the empty environment value and empty `zoneinfo.TZPATH`.

Conclusion:

> Package-only lookup is correctly selected, but the base runtime does not include the first-party `tzdata` package.

## Explicit Termux-path scenario

Observed input:

```text
PYTHONTZPATH=/data/data/com.termux/files/usr/share/zoneinfo
```

Observed:

```text
zoneinfo.TZPATH=
  /data/data/com.termux/files/usr/share/zoneinfo

termux_zoneinfo_exists=false
UTC                  FAIL
Asia/Seoul           FAIL
America/New_York     FAIL
```

The corrected child explicitly recorded the requested path.

Conclusion:

> The tested Termux host did not expose a POSIX-style TZif tree at `$PREFIX/share/zoneinfo`.

This does not claim that no Termux package can provide such a directory. It records the tested host state.

## First-party tzdata fallback

A uv ephemeral environment supplied:

```text
tzdata 2026.3
PYTHONTZPATH=""
```

For both frozen and promoted runtimes:

```text
tzdata package found
zoneinfo.TZPATH=[]
UTC                  PASS
Asia/Seoul           PASS
America/New_York     PASS
all_keys_pass=true
```

The ephemeral environment preserved the expected runtime as `sys.base_prefix` and did not install data into the base runtime prefix.

Conclusion:

> CPython's first-party `tzdata` package fallback solves the tested timezone-data gap without modifying the runtime product.

## CPython data-source model

The observed corrected behavior matches the CPython model:

```text
search configured zoneinfo.TZPATH directories
    -> if unresolved
fall back to first-party tzdata package
    -> if unavailable
raise ZoneInfoNotFoundError
```

An empty `PYTHONTZPATH` forces package-only lookup, but a probe of that input must not use `-I` or `-E`.

## Android boundary note

Android ships timezone data for platform components, but that data is not automatically exposed as the POSIX-style per-key TZif directory tree searched by CPython `zoneinfo`.

Android platform timezone data and CPython `zoneinfo` data sourcing therefore remain separate integration domains.

## Final boundary model

```text
native ELF closure              resolved
extension execution             PASS
CA trust source                 Termux host integration
default zoneinfo source         unavailable in tested runtime/host state
base first-party tzdata         absent
uv first-party tzdata fallback  PASS
explicit PYTHONTZPATH controls  corrected and confirmed
```

## Distribution implication

The later distribution stage must choose among:

```text
bundle first-party tzdata
declare first-party tzdata as a dependency
integrate a host TZif tree
support multiple explicit policies
```

Stage 3-A and Stage 3-B Phase 5 characterize and preserve the boundary; they do not select the Stage 3-C distribution policy.
