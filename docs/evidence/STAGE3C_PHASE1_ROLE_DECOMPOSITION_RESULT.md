# Stage 3-C Phase 1 Role Decomposition Result

> **Status:** PASS — semantic capability probes pending
> **Input manifest:** `092ea87eed2a3c800053a0ef480abd8ef836bda8a8890549ce84370eae6e2a0f`
> **Machine checks:** 18/18
> **Claim:** exact role/rule/path decomposition, not archive omission safety

## Mechanical result

```text
entries                  3155
regular files            2934
directories               216
symlinks                    5
ELF objects                81
regular-file bytes  79,349,263
UNKNOWN                     0
```

The decomposition reproduced the accepted role counts, type counts, regular-file byte totals, ELF count, symlink count, and manifest hash exactly.

```text
failed_checks      []
pass               true
```

## Role overview

```text
role                 entries     regular bytes     byte share
RUNTIME                  711        38,775,506       48.8669%
DEBUG_OR_OPTIONAL       1986        35,466,620       44.6968%
DEVELOPMENT              449         4,737,164        5.9700%
METADATA                   8           356,169        0.4489%
LICENSE                    1            13,804        0.0174%
UNKNOWN                    0                 0        0.0000%
```

## Optional decomposition

```text
component       entries     regular bytes
lib/python3.14/test
  test             1785        33,476,596

lib/python3.14/idlelib
  idlelib           161         1,624,586

lib/python3.14/tkinter
  tkinter            14           303,444

lib/python3.14/turtledemo
  turtledemo         23            61,800

lib/python3.14/__phello__
  __phello__           3               194
```

The CPython regression-test tree accounts for approximately 94.4% of the optional regular-file bytes. It includes large Unicode normalization data, bundled wheel test data, archive fixtures, decimal test vectors, and the regression modules themselves.

## Development decomposition

```text
surface                                      entries     regular bytes
include/                                         434         4,701,144
lib/python3.14/config-*                            6            34,331
lib/pkgconfig/                                     9             1,689
```

The development role contains 427 installed header files, six pkg-config regular files with two compatibility symlinks, and five config-development regular files plus their directory.

## Runtime decomposition

```text
surface                       entries     regular bytes
stdlib and runtime data           622        12,362,626
lib-runtime                        16        12,950,104
lib-dynload                        68         7,630,224
libpython                           1         5,821,560
bin                                 4            10,992
```

All 81 ELF entries remain in the runtime role.

## Exact metadata rows

Runtime-root metadata candidates:

```text
lib/python3.14/_sysconfig_vars__android_aarch64-linux-android.json
lib/python3.14/_sysconfigdata__android_aarch64-linux-android.py
lib/python3.14/build-details.json
```

Installed config-tree metadata:

```text
lib/python3.14/config-3.14-aarch64-linux-android/Makefile
lib/python3.14/config-3.14-aarch64-linux-android/Setup
lib/python3.14/config-3.14-aarch64-linux-android/Setup.local
lib/python3.14/config-3.14-aarch64-linux-android/config.c
lib/python3.14/config-3.14-aarch64-linux-android/python-config.py
```

The current `METADATA` role is descriptive. It is not yet a final archive role. The root sysconfig/build-details files and the config-tree files have different likely consumers and must be separated by target behavior.

## Exact license row

```text
lib/python3.14/LICENSE.txt
sha256
  b0e25a78cffb43f4d92de8b61ccfa1f1f98ecbc22330b54b5251e7b6ba010231
size
  13804
```

Every archive redistributing covered CPython payload must preserve the selected license mapping; the final duplication/reference policy remains a later contract decision.

## Symlink boundary

Runtime:

```text
bin/python -> python3
bin/python3 -> python3.14
lib/libsqlite3.so.0 -> libsqlite3_python.so
```

Development:

```text
lib/pkgconfig/python3-embed.pc -> python-3.14-embed.pc
lib/pkgconfig/python3.pc -> python-3.14.pc
```

## Provisional policy classes

The decomposition supports the following hypotheses, not yet final archive decisions:

```text
lib/python3.14/test
  OPTIONAL_TEST_SUITE candidate

idlelib + turtledemo
  OPTIONAL_GUI_TOOLING candidates

tkinter
  OPTIONAL_GUI_RUNTIME candidate; requires target _tkinter/Tcl/Tk evidence

__phello__
  OPTIONAL_TEST_DEMO candidate

include + pkgconfig + config development rows
  DEVELOPMENT candidate

_sysconfigdata + _sysconfig_vars + build-details
  RUNTIME_METADATA candidate

config-tree Makefile/Setup/config/python-config rows
  DEVELOPMENT_METADATA candidate
```

## Required next evidence

Before materializing archive variants, probe the canonical target runtime for:

```text
_sysconfigdata import and active sysconfig paths
build-details parseability
Makefile and pyconfig.h discovery surfaces
venv and ensurepip imports
_tkinter presence and importability
tkinter import and Tcl interpreter creation
turtle import
idlelib and idlelib.pyshell import
turtledemo import
test and test.support import
__phello__ import
```

The probe is observational and non-mutating. Optional-module failure is evidence, not a probe failure.

## Claim boundary

Proved:

```text
accepted role inventory decomposes exactly by rule, type, path, and bytes
regression-test payload dominates the optional surface
development and runtime surfaces have explicit path-level boundaries
metadata requires consumer-based partitioning
```

Not proved:

```text
all optional paths can be omitted together
tkinter is usable on this target
removing development files preserves uv/venv workflows
removing config-tree metadata preserves sysconfig behavior
one combined or split archive model is selected
```
