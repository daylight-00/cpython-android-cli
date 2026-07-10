# Stage 2-C End-to-End Smoke Summary

> **Status:** Selected evidence
> **Stage:** 2-C
> **Result:** PASS
> **Final marker:** `STAGE2C_SMOKE=PASS`

## Purpose

This summary freezes the end-to-end result of the cleaned Stage 2-C repository and deployment workflow.

The test asked:

> Does the selected R2 + B0 architecture still work when built through the canonical workstation workflow, transferred through the canonical `out/` tree, assembled under the Termux project workspace, and tested through the current smoke harness?

The answer was yes on the tested environment.

## Workflow under test

```text
Victor workstation
    |
    | scripts/build/build-launcher.sh
    v
out/aarch64-linux-android24/release/bin/python3.14
    |
    | artifact transport
    | successful topology: Termux-initiated rsync pull
    v
Termux repo out/aarch64-linux-android24/release/
    |
    | scripts/termux/prepare-runtime.sh
    v
work/termux/stage2c/runtime/prefix
    |
    | scripts/test/smoke-termux.sh
    v
base runtime + subprocess + uv venv + uv run
```

## Workstation build result

The canonical build script produced:

```text
out/aarch64-linux-android24/release/bin/python3.14
```

Observed ELF properties:

```text
ELF 64-bit LSB PIE executable
Machine: ARM aarch64
interpreter: /system/bin/linker64
RUNPATH: $ORIGIN/../lib
```

Observed direct dependencies:

```text
libpython3.14.so
libdl.so
libm.so
liblog.so
libc.so
```

The workstation build stage therefore passed.

## Artifact transport

Termux inbound connectivity was unavailable at the time of the test, so workstation-initiated push was not used.

The successful topology was:

```text
Termux
    |
    | outbound SSH / rsync pull
    v
Victor workstation artifact source
```

The artifact arrived under the same repo-relative path:

```text
out/aarch64-linux-android24/release/
```

The transport direction is not part of runtime semantics; the artifact identity and path model are unchanged.

## Runtime assembly result

The Termux assembly script produced the runtime under:

```text
work/termux/stage2c/runtime/prefix
```

The smoke test entered:

```text
work/termux/stage2c/runtime/prefix/bin/python
```

## Base runtime observations

Observed output:

```text
executable:
  /data/data/com.termux/files/home/projects/cpython-android-cli/work/termux/stage2c/runtime/prefix/bin/python

prefix:
  /data/data/com.termux/files/home/projects/cpython-android-cli/work/termux/stage2c/runtime/prefix

base_prefix:
  /data/data/com.termux/files/home/projects/cpython-android-cli/work/termux/stage2c/runtime/prefix

LD_LIBRARY_PATH:
  /data/data/com.termux/files/home/projects/cpython-android-cli/work/termux/stage2c/runtime/prefix/lib

SSL_CERT_FILE:
  /data/data/com.termux/files/usr/etc/tls/cert.pem

HTTPS status:
  200
```

Interpretation:

```text
base runtime identity                  correct
self-derived runtime libdir            correct
Termux CA bundle integration           correct
HTTPS                                  PASS
```

## Subprocess observation

The base-runtime smoke probe launched a child through `sys.executable`.

Observed child identity remained under:

```text
work/termux/stage2c/runtime/prefix
```

The subprocess test completed successfully.

Frozen result:

```text
subprocess re-entry: PASS
```

## uv venv observation

uv reported:

```text
Using CPython 3.14.6 interpreter at:
  work/termux/stage2c/runtime/prefix/bin/python
```

The created environment was:

```text
results/termux/stage2c/venv
```

Observed identity:

```text
sys.executable:
  /data/data/com.termux/files/home/projects/cpython-android-cli/results/termux/stage2c/venv/bin/python

sys.prefix:
  /data/data/com.termux/files/home/projects/cpython-android-cli/results/termux/stage2c/venv

sys.base_prefix:
  /data/data/com.termux/files/home/projects/cpython-android-cli/work/termux/stage2c/runtime/prefix
```

Frozen interpretation:

```text
uv explicit interpreter selection      PASS
venv creation                           PASS
venv identity                           PASS
assembled runtime preserved as base     PASS
```

## uv run observation

The test installed two packages and imported `anyio` successfully.

Observed ephemeral interpreter:

```text
/data/data/com.termux/files/home/.cache/uv/builds-v0/.tmp9fV6Pj/bin/python
```

Observed ephemeral prefix:

```text
/data/data/com.termux/files/home/.cache/uv/builds-v0/.tmp9fV6Pj
```

Observed base prefix:

```text
/data/data/com.termux/files/home/projects/cpython-android-cli/work/termux/stage2c/runtime/prefix
```

Frozen interpretation:

```text
uv run environment creation            PASS
package installation                    PASS
package import                           PASS
base runtime identity                    PASS
```

## uv hardlink warning

Observed warning:

```text
Failed to hardlink files; falling back to full copy
```

The warning was followed by successful installation:

```text
Installed 2 packages
```

and the test completed with:

```text
STAGE2C_SMOKE=PASS
```

Frozen interpretation:

```text
hardlink optimization:
  unavailable for tested cache/target filesystem arrangement

copy fallback:
  successful

functional impact:
  none observed
```

## Final Stage 2-C result matrix

```text
repo-relative configuration model      PASS
canonical workstation build            PASS
Android arm64 launcher ELF             PASS
canonical output path                  PASS
artifact transport                     PASS
Termux runtime assembly                PASS
base runtime                            PASS
native stdlib imports                  PASS
HTTPS                                  PASS
subprocess re-entry                    PASS
uv venv                                PASS
venv identity                          PASS
uv run                                 PASS
final marker                           STAGE2C_SMOKE=PASS
```

## Freeze consequence

This result closes the Stage 2-C synthesis question.

The cleaned repository workflow preserved the behavior selected and validated in Stage 2-B.

Therefore:

```text
Stage 2-C: PASS
Stage 2: FROZEN
```

This summary is evidence for `docs/stages/STAGE2_FINAL.md`.
