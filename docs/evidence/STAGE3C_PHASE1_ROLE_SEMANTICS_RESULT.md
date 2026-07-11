# Stage 3-C Phase 1 Semantic Role Probe Result

> **Status:** PASS — component manifest policy selected, isolated variants pending
> **Machine verifier:** 38/38
> **Source mutation:** PASS
> **Input entries:** 3155

## Result

```text
failed_checks      []
missing_outputs    []
parse_errors       {}
pass               true
```

The canonical promoted tree remained unchanged:

```text
before/after fingerprint
  5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c
```

## Core/runtime observations

```text
venv                 PASS
ensurepip            PASS (observation, not frozen gate)
test                 PASS
test.support         PASS
__phello__           PASS
```

The internal regression-suite paths are present and importable. This proves they are a usable test payload, not that they belong in the default runtime artifact.

## Tk/GUI observations

```text
_tkinter             FAIL: ModuleNotFoundError
tkinter              FAIL: No module named '_tkinter'
Tcl interpreter      unavailable
turtle               FAIL: No module named '_tkinter'
idlelib              PASS
idlelib.pyshell      FAIL: SystemExit 1
turtledemo           PASS
DISPLAY              absent
```

The pure-Python Tkinter package is present, but the required `_tkinter` binary backend is absent. The current target therefore does not provide a working Tk/Tcl capability.

`idlelib` and `turtledemo` shallow imports do not establish usable GUI applications. `idlelib.pyshell` and `turtle` fail on the target, and the entire Tk-dependent source cluster is unsuitable for the default runtime artifact until a real `_tkinter`/Tcl/Tk backend exists.

Selected interpretation:

```text
lib/python3.14/tkinter
lib/python3.14/idlelib
lib/python3.14/turtledemo
lib/python3.14/turtle.py
lib/python3.14/turtle.cfg, if present

  -> UNSUPPORTED_GUI_SOURCE
  -> not distributed in the first product split
```

This is not a claim that the source is invalid upstream. It is a target-product decision based on the missing backend.

## Sysconfig observations

```text
sysconfig success                  true
configuration variable count      1098
all active paths under prefix      true
_sysconfigdata import              true
_sysconfig vars JSON count         1
build-details JSON parse           true
Makefile exists                    true
pyconfig.h exists                  true
```

Active installation paths:

```text
data
include
platinclude
platlib
platstdlib
purelib
scripts
stdlib
```

All resolved under the promoted prefix.

Selected metadata split:

```text
RUNTIME_METADATA
  lib/python3.14/_sysconfigdata__android_aarch64-linux-android.py
  lib/python3.14/_sysconfig_vars__android_aarch64-linux-android.json
  lib/python3.14/build-details.json

DEVELOPMENT_METADATA
  lib/python3.14/config-3.14-aarch64-linux-android/Makefile
  lib/python3.14/config-3.14-aarch64-linux-android/Setup
  lib/python3.14/config-3.14-aarch64-linux-android/Setup.local
  lib/python3.14/config-3.14-aarch64-linux-android/config.c
  lib/python3.14/config-3.14-aarch64-linux-android/python-config.py
```

The runtime metadata set supports active configuration-variable and installation-path services. The development metadata set supports native extension/build discovery and is tested again only after composing the development addon.

## Selected candidate components

```text
RUNTIME_BASE
RUNTIME_METADATA
DEVELOPMENT
DEVELOPMENT_METADATA
OPTIONAL_TEST_SUITE
OPTIONAL_TEST_DEMO
UNSUPPORTED_GUI_SOURCE
LICENSE
```

Candidate artifact compositions:

```text
runtime-base
  RUNTIME_BASE + RUNTIME_METADATA + LICENSE

development-addon
  DEVELOPMENT + DEVELOPMENT_METADATA

test-addon
  OPTIONAL_TEST_SUITE + OPTIONAL_TEST_DEMO

unsupported-gui-source
  UNSUPPORTED_GUI_SOURCE
  not distributed until a working Tk backend exists
```

## Claim boundary

Proved:

```text
canonical semantic observations are complete and non-mutating
Tk-dependent source is unusable on the current target
sysconfig runtime service is active and prefix-correct
runtime and development metadata have distinct consumers
```

Not proved:

```text
runtime-base passes after physical materialization
runtime-base plus development addon restores native-development surfaces
runtime-base plus test addon passes test imports and selected tests
selected variants preserve closure, relocation, HTTPS, uv and venv behavior
```

Those claims require isolated-copy validation. The canonical promoted tree remains untouched.
