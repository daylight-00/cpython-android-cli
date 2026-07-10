# CPython Android CLI + uv: Project Context

> **Status:** Active research project
> **Current architecture state:** Stage 2 frozen
> **Next phase:** Stage 3 scoping, not started
> **Primary target:** Termux on Android arm64 (`aarch64-linux-android`)
> **Host build environment:** Separate Linux workstation
> **Python baseline:** CPython 3.14.6
> **Last context update:** 2026-07-10

## 1. Purpose

This document is the current onboarding and handoff context for the project author, reviewers, and AI coding agents.

The project investigates how an upstream-built CPython Android runtime can be adapted into a normal CLI interpreter under Termux and used explicitly by uv.

A good project description is:

> **A CLI adaptation of an upstream CPython Android build for Termux, with uv integration.**

The project is intentionally narrow. It is not currently:

- a CPython fork,
- a replacement for Termux Python,
- a uv-managed Python provider,
- a general Android distribution system,
- an Android port of `python-build-standalone`,
- a static Python distribution.

The working principle is:

```text
understand -> reproduce -> measure -> compare -> design -> optimize
```

not:

```text
patch -> patch more -> accidentally invent a distribution
```

## 2. Provenance

The frozen baseline lineage is:

```text
CPython 3.14.6 upstream source
        +
upstream CPython Android build infrastructure
        +
locally built aarch64-linux-android prefix
        +
minimal Android CLI frontend experiments
        +
Termux packaging and validation
        +
uv explicit interpreter selection
```

The runtime should not be described as merely an unpacked generic Python.org artifact. The relevant provenance is an upstream CPython Android build path and a locally built Android prefix.

## 3. Responsibility boundaries

The project treats these layers separately:

```text
Python CLI semantics
    argv processing
    exit codes
    command/module/script modes

Python runtime initialization
    Py_BytesMain baseline
    B0 PyConfig selected frontend

Python path discovery
    sys.prefix
    sys.base_prefix
    sys.path
    venv identity

native dependency lookup
    launcher -> libpython
    extension modules
    transitive native dependencies

host trust-store integration
    SSL_CERT_FILE
    Termux CA bundle

external environment management
    uv explicit interpreter path
    uv venv
    uv run

project workflow
    workstation build
    canonical out tree
    artifact transport
    Termux runtime assembly
    smoke validation
```

A solution for one layer must not be assumed to solve the others.

## 4. Frozen stage status

```text
Stage 1-A  explicit runtime baseline                    FROZEN
Stage 1-B  PyConfig frontend comparison                 FROZEN
Stage 2-A  bootstrap strategy comparison                COMPLETE
Stage 2-B  conditional re-exec and relocation           COMPLETE
Stage 2-C  synthesis and project workflow               COMPLETE
Stage 2    native bootstrap and workflow architecture   FROZEN
Stage 3    standalone distribution engineering          NOT STARTED
```

The authoritative low-level Stage 2 freeze is:

```text
docs/stages/STAGE2_FINAL.md
```

Selected evidence summaries:

```text
docs/evidence/STAGE2B_VALIDATION_SUMMARY.md
docs/evidence/STAGE2B_RELOCATION_SUMMARY.md
docs/evidence/STAGE2C_E2E_SMOKE_SUMMARY.md
```

## 5. Stage 1-A frozen baseline

Stage 1-A asked:

> Can the Android CPython runtime work as a practical Termux CLI interpreter with uv when the runtime contract is made explicit?

Frontend:

```text
Py_BytesMain
```

Frozen external runtime contract:

```text
LD_LIBRARY_PATH=<cpython-prefix>/lib
SSL_CERT_FILE=<termux-prefix>/etc/tls/cert.pem
```

Not required:

```text
PYTHONHOME
PYTHONPATH
```

Validated areas:

```text
basic CLI execution
native stdlib imports
HTTPS
uv venv
venv identity
native stdlib in venv
uv pip / package import
uv run
```

See:

```text
docs/stages/STAGE1A_BASELINE.md
```

## 6. Stage 1-B frozen frontend

Stage 1-B compared:

```text
Stage 1-A baseline
    Py_BytesMain

B0
    PyConfig_InitPythonConfig
    PyConfig_SetBytesArgv
    Py_InitializeFromConfig
    PyConfig_Clear
    Py_RunMain
    no config.home override

B1
    same PyConfig flow
    config.home supplied from CPYTHON_HOME
```

B0 preserved the tested functional and semantic surface.

B1 passed with a correct home, but an incorrect home failed at startup because Python could not import `encodings`. That negative control proved that explicit `config.home` was a real additional dependency.

Frozen decision:

```text
selected:
  B0 / PyConfig auto-discovery

not selected:
  B1 / explicit config.home
```

See:

```text
docs/stages/STAGE1B_PYCONFIG.md
```

## 7. Stage 2-A bootstrap comparison

Starting point:

```text
B0 PyConfig frontend
+
external LD_LIBRARY_PATH
+
external SSL_CERT_FILE
```

Three strategies were compared.

### S2-E: setenv-only

Observed:

```text
current process native imports: FAIL
subprocess inheriting prepared environment: PASS
```

Interpretation:

Updating environment state was useful for future execs but did not restart or retroactively reconfigure the current process dynamic loader.

### S2-U: linker-update experiment

The experiment attempted to resolve `android_update_LD_LIBRARY_PATH` through the tested `RTLD_DEFAULT` path.

Observed:

```text
symbol unavailable through tested resolution path
```

This strategy was not selected.

### S2-R: self re-exec

Model:

```text
derive runtime path
set environment
execv(self, original argv)
fresh process starts with prepared loader environment
enter B0 PyConfig
```

Observed comparison result:

```text
native stdlib        PASS
HTTPS                PASS
subprocess           PASS
uv venv              PASS
venv native imports  PASS
uv run               PASS
```

S2-R was selected for refinement.

## 8. Stage 2-B frozen R2 design

Stage 2-B removed a private recursion guard and used the actual environment state as the re-exec fixed point.

Frozen state machine:

```text
read /proc/self/exe
        |
derive prefix
        |
derive prefix/lib
        |
normalize LD_LIBRARY_PATH
        |
        +-- required libdir absent at process start
        |       configure CA
        |       set environment
        |       execv(actual executable, original argv)
        |
        +-- required libdir present
                remove duplicate exact required components
                repair/discover CA if needed
                enter B0 PyConfig directly
```

Expected clean trace:

```text
reexec
direct
```

Expected child trace after inheritance:

```text
direct
```

The final main validation passed:

```text
clean                 PASS
ready                 PASS
wrong-ld              PASS
wrong-ca              PASS
duplicate             PASS
unrelated cwd         PASS
external symlink      PASS
subprocess             PASS
uv venv                PASS
clean venv launch      PASS
venv identity          PASS
uv run                 PASS
```

The whole-prefix relocation test also passed at location A and after moving the prefix to location B.

Exact relocation claim:

> The tested runtime prefix can be relocated as a unit, and the R2 launcher re-derives its native runtime path from the actual executable location.

Not tested:

> An already-created external venv after moving its base runtime.

## 9. Frozen Stage 2 architecture

```text
shell / uv / venv entry point
        |
        v
launcher
        |
        +-- RUNPATH $ORIGIN/../lib for direct libpython lookup
        |
        +-- read /proc/self/exe
        +-- derive actual prefix
        +-- derive <prefix>/lib
        +-- normalize LD_LIBRARY_PATH
        +-- preserve valid SSL_CERT_FILE
        +-- otherwise discover Termux CA bundle
        |
        +-- required libdir absent at process start
        |       -> execv(actual executable, original argv)
        |
        +-- required libdir already present
                -> B0 PyConfig
                -> Py_RunMain
```

The launcher-level RUNPATH and the broader extension dependency bootstrap are separate concerns.

## 10. Stage 2-C repository and workflow model

Tracked state:

```text
src/
scripts/
config/
docs/
experiments/
```

Machine-local configuration:

```text
.local/env
```

Generated state:

```text
out/
work/
results/
dist/
cache/
```

Repo-local external toolchain/upstream working trees:

```text
tools/
```

Canonical cross-build output:

```text
out/<target>/<profile>/
```

Current target:

```text
out/aarch64-linux-android24/release/
├── bin/
│   └── python3.14
└── metadata/
    └── build-info.txt
```

## 11. Current development build input

The current Stage 2-C launcher build uses:

```text
experiments/bootstrap-android-build/android-python-work/prefix
```

as `CPYTHON_DEV_PREFIX`.

The build requires:

```text
include/python3.14/Python.h
include/python3.14/pyconfig.h
lib/libpython3.14.so
```

This is the current canonical development input by provenance and actual use.

Its location under `experiments/` is recognized as structurally awkward. Promoting the CPython build dependency into a reproducible build-product model is deferred to a later phase; Stage 2 does not silently substitute validation copies under `pristine-test/` as canonical inputs.

## 12. Artifact transport topology

Source, scripts, docs, and experiment history use Git.

Generated launcher artifacts use rsync.

Supported helpers:

```text
scripts/sync/push-out.sh
    workstation initiates connection to Termux

scripts/sync/pull-out.sh
    Termux initiates connection to workstation
```

The successful Stage 2-C end-to-end validation used Termux-initiated pull because Termux inbound connectivity was unavailable.

The transport initiator does not change artifact semantics. Both sides use the same repo-relative target/profile output path.

## 13. Stage 2-C end-to-end result

The successful workflow was:

```text
Victor workstation
    |
canonical launcher build
    |
out/aarch64-linux-android24/release/bin/python3.14
    |
Termux-initiated artifact pull
    |
Termux runtime assembly
    |
work/termux/stage2c/runtime/prefix
    |
smoke validation
```

Observed base runtime state:

```text
sys.executable:
  work/termux/stage2c/runtime/prefix/bin/python

sys.prefix:
  work/termux/stage2c/runtime/prefix

sys.base_prefix:
  work/termux/stage2c/runtime/prefix

LD_LIBRARY_PATH:
  work/termux/stage2c/runtime/prefix/lib

SSL_CERT_FILE:
  /data/data/com.termux/files/usr/etc/tls/cert.pem

HTTPS:
  200
```

uv venv preserved:

```text
sys.prefix:
  results/termux/stage2c/venv

sys.base_prefix:
  work/termux/stage2c/runtime/prefix
```

uv run preserved the assembled runtime as the base prefix of the ephemeral environment.

Final marker:

```text
STAGE2C_SMOKE=PASS
```

Therefore:

```text
Stage 2-C: PASS
Stage 2: FROZEN
```

## 14. uv's role

uv is a consumer of the interpreter, not the builder of the interpreter.

The supported integration model is explicit interpreter selection, for example:

```sh
uv venv \
  --no-python-downloads \
  --python /absolute/path/to/python \
  .venv
```

The project does not currently imitate uv-managed Python archive metadata or provide automatic uv Python downloads.

## 15. Invariants for future work

Future work must preserve or intentionally re-evaluate:

```text
normal tested CPython CLI semantics
B0 PyConfig auto-discovery unless evidence requires change
clean top-level loader activation
no unnecessary child re-exec with inherited ready environment
separate native-loader and CA concerns
venv prefix/base_prefix identity
uv explicit interpreter workflow
whole-prefix self-location behavior
repo-relative current script paths
canonical out/<target>/<profile>/ artifact layout
```

## 16. Deferred questions

Stage 2 deliberately does not answer:

```text
How should the CPython development prefix be rebuilt reproducibly?
How should a release artifact bundle the runtime prefix?
Should host CA integration remain external or be packaged differently?
How should native dependency closure be described and verified?
How should multi-ABI and multi-API-level builds be represented?
Can uv-managed automatic Python downloads be integrated cleanly?
How should release provenance, manifests, signatures, and SBOMs work?
What happens to an existing external venv after moving its base runtime?
```

These belong to a new Stage 3 scope rather than an implicit extension of Stage 2.

## 17. Reading order

Recommended order:

```text
README.md
    |
docs/PROJECT_CONTEXT.md
    |
docs/stages/STAGE2_FINAL.md
    |
docs/evidence/
    |
experiments/stage2a-bootstrap-strategies/
experiments/stage2b-conditional-reexec/
    |
src/launcher/python.c
```

The next action should be to define the Stage 3 research question before changing the frozen Stage 2 architecture.
