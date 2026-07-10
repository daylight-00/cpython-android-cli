# Stage 2-B Relocation Summary

> **Status:** Selected evidence
> **Stage:** 2-B
> **Result:** PASS

## Purpose

This summary freezes the decision-bearing results of the whole-prefix relocation experiment.

The test asked:

> If the complete prepared runtime prefix is moved to a different absolute path, does R2 derive the new runtime location correctly and preserve the validated runtime surface?

## Test shape

```text
prepare runtime prefix
        |
copy to location A
        |
validate A
        |
move entire prefix A -> B
        |
validate B
```

At each location the test exercised:

```text
base runtime probe
native stdlib imports
HTTPS
subprocess re-entry
uv venv creation
clean venv launch
uv run
```

## Location A

Results:

```text
RELOCATION_PROBE[A]=0
RELOCATION_UV_VENV[A]=0
RELOCATION_VENV_RUN[A]=0
RELOCATION_UV_RUN[A]=0
```

Observed runtime identity was based on the location-A prefix.

This included:

```text
sys.executable
sys.prefix
sys.base_prefix
LD_LIBRARY_PATH
```

using A-based paths.

## Move

The entire prefix was moved:

```text
location A
    ->
location B
```

The test did not patch runtime paths between A and B.

## Location B

Results:

```text
RELOCATION_PROBE[B]=0
RELOCATION_UV_VENV[B]=0
RELOCATION_VENV_RUN[B]=0
RELOCATION_UV_RUN[B]=0
```

Observed runtime identity changed to B-based paths.

This included:

```text
sys.executable
sys.prefix
sys.base_prefix
LD_LIBRARY_PATH
uv-selected base interpreter
new venv sys.base_prefix
uv-run ephemeral environment sys.base_prefix
```

No stale A path was accepted as the active runtime identity after the move.

## What this proves

Frozen claim:

> The tested runtime prefix can be relocated as a unit, and the R2 launcher re-derives its native runtime path from the actual executable location.

The result supports the `/proc/self/exe`-based design:

```text
actual executable
    -> derive prefix
    -> derive prefix/lib
    -> prepare loader environment
```

rather than:

```text
build-time absolute prefix
argv[0]-relative assumption
current-working-directory assumption
```

## What this does not prove

The relocation experiment did not test this sequence:

```text
create external venv against base runtime at A
        |
move only base runtime A -> B
        |
execute the already-created external venv
```

Therefore the project does not claim:

> A previously-created external venv remains usable after its base runtime is moved.

That is a separate future experiment.

## uv hardlink warning

A hardlink fallback warning may appear when uv cache and target paths are on different filesystems.

In the observed relocation runs, this was non-fatal and package operations completed through copy fallback.

## Frozen result matrix

```text
location A base probe             PASS
location A native imports         PASS
location A HTTPS                  PASS
location A subprocess             PASS
location A uv venv                PASS
location A clean venv launch      PASS
location A uv run                 PASS

whole-prefix move A -> B          DONE

location B base probe             PASS
location B native imports         PASS
location B HTTPS                  PASS
location B subprocess             PASS
location B uv venv                PASS
location B clean venv launch      PASS
location B uv run                 PASS
```

This summary is evidence for `docs/stages/STAGE2_FINAL.md`.
