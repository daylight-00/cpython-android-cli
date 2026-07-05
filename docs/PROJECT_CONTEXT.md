# CPython Android CLI + uv: Project Context and Design Notes

> **Status:** Active experiment  
> **Current phase:** Stage 1-A baseline  
> **Primary target:** Termux on Android arm64 (`aarch64-linux-android`)  
> **Host build environment:** Separate Linux workstation  
> **Last context update:** 2026-07-04

## 0. Why this document exists

This document is an onboarding and continuity note for:

- the future version of the project author who has forgotten why earlier decisions were made,
- another developer reviewing or continuing the work,
- an AI coding agent that needs enough context to continue without rediscovering the entire design space.

The project is intentionally small and personal. It is open source, but it is not trying to present itself as a new general-purpose Python distribution or as a replacement for CPython, Termux Python, uv, Conda, or `python-build-standalone`.

The project preference is:

1. start from upstream or mainstream implementations where possible,
2. make custom behavior explicit and narrow,
3. preserve a clear reference chain for each non-obvious design decision,
4. separate experiments from the baseline,
5. optimize for understanding and reproducibility before portability tricks or aggressive static linking.

The long-term interest in portable or static builds is real, but it is deliberately deferred. The immediate goal is to finish a clean and explainable Android CLI adaptation based on the official CPython Android distribution, then integrate it with uv through an explicit interpreter path.

---

## 1. Executive summary

The project goal is:

> Use the official CPython Android runtime as a normal command-line Python interpreter in Termux, and use uv to create and manage virtual environments and project dependencies around that interpreter.

The key architectural fact is:

> uv does not require Python to have been built by Astral.

uv can use an already-installed or explicitly specified Python interpreter. `uv python install` uses uv-managed Python distributions, while an external interpreter can be selected by executable path with `--python` / `-p` or `UV_PYTHON`. The project therefore does **not** need to imitate Astral archive naming or uv's managed-Python download metadata in order to use uv successfully.

The current prototype is:

```text
Python.org official Android CPython artifact
        +
minimal CPython-style CLI frontend
        +
explicit runtime environment
        +
uv -p /absolute/path/to/python
```

The current prototype already demonstrates:

- the Android CPython runtime can be executed from Termux,
- uv can recognize the interpreter,
- uv can create a virtual environment from the explicit interpreter path.

The current known issue is not that SSL failed to build. `_ssl` exists, and the OpenSSL libraries exist. The current failure is a native library search-path issue:

```text
_ssl.cpython-314-aarch64-linux-android.so
    DT_NEEDED -> libssl_python.so

libssl_python.so
    exists at prefix/lib/libssl_python.so

but the Android dynamic linker does not find it
under the current direct-launch environment
```

Observed error:

```text
ImportError: dlopen failed: library "libssl_python.so" not found:
needed by .../lib-dynload/_ssl.cpython-314-aarch64-linux-android.so
in namespace (default)
```

This is an important design observation. It shows the difference between:

- an Android runtime packaged for app embedding, and
- a finished self-contained Unix-like CLI distribution.

For Stage 1-A, the correct response is **not** to immediately patch ELF files or redesign the runtime. The baseline should first reproduce the explicit runtime environment used by the upstream-adjacent references, then measure what works.

---

## 2. Project identity

A good current one-line description is:

> **An experimental CLI adaptation of the official CPython Android distribution for Termux, with uv integration.**

This wording is intentional.

The project is **not yet**:

- a new CPython fork,
- a full Android port of `python-build-standalone`,
- a uv-managed Python provider,
- a replacement for Termux's `python` package,
- a fully relocatable standalone Python distribution,
- a static Python distribution.

The project currently sits between four ecosystems:

```text
CPython upstream
    provides the Android runtime and reference initialization behavior

Android / NDK
    provides the target ABI and native loading environment

Termux
    provides the interactive CLI context on Android

uv
    provides environment and project management around an explicit interpreter
```

The project should remain an **adaptation layer** until evidence shows that a deeper fork or custom distribution build is necessary.

---

## 3. Mental model: four different problems that are easy to mix together

The phrase "build Python" hides several independent responsibilities.

A Python distribution has to solve at least:

```text
1. Compile CPython itself.

2. Provide native dependencies:
   OpenSSL
   SQLite
   libffi
   compression libraries
   and others.

3. Arrange Python runtime paths:
   sys.prefix
   stdlib
   lib-dynload
   site-packages
   sysconfig

4. Arrange native library loading:
   libpython
   libssl
   libcrypto
   libsqlite
   and dependency chains between shared objects.

5. Package the result for the target deployment model.

6. Define how virtual environments and package builds interact with it.
```

Different ecosystems solve these responsibilities in different places.

### 3.1 Distribution Linux Python

A Debian/Ubuntu-style Python is integrated with the operating system package graph.

Conceptually:

```text
OS package manager
├── Python
├── OpenSSL
├── SQLite
├── libffi
├── zlib
├── CA certificates
└── shared system paths
```

The operating system is part of the runtime environment.

This is a perfectly valid model, but it is not the same goal as a relocatable tarball.

### 3.2 Conda Python

Conda treats environments as first-class software environments, including non-Python binary dependencies.

Conceptually:

```text
Conda environment prefix
├── Python package
├── OpenSSL package
├── SQLite package
├── libffi package
├── other libraries
└── project packages
```

A Conda Python installation is best understood together with the environment and its dependency solver, not as a single magical self-contained `python` binary.

### 3.3 `python-build-standalone`

`python-build-standalone` is distribution engineering.

Its goal is to produce highly portable, self-contained Python distributions with controlled build inputs, dependency handling, archive layout, metadata, and portability work.

Its output archives can contain:

```text
python/
├── PYTHON.json
├── build/
└── install/
```

and its install-only artifacts expose the runnable installation without the whole build tree.

This is much more than:

```sh
./configure
make
make install
```

It is a build-and-distribution system.

### 3.4 Official CPython Android distribution

The official CPython Android documentation assumes an app-embedding model.

Conceptually:

```text
Android application
├── native application code
├── libpython
├── Python stdlib
├── native extension modules
├── native dependencies
└── application Python code
```

The official Android artifact provides a valid Android CPython runtime, but it is not presented as a conventional `/usr/bin/python`-style CLI installation.

This project starts from that official runtime and adds a CLI adaptation layer.

---

## 4. uv's role in this project

A central design principle:

> **uv is a consumer of the interpreter in this project, not the builder of the interpreter.**

uv distinguishes between Python versions it manages itself and external Python installations it can discover or use explicitly.

For this project, the important interface is:

```sh
uv venv -p /absolute/path/to/python .venv
```

or:

```sh
export UV_PYTHON=/absolute/path/to/python
```

Automatic Python downloads can be disabled when desired.

Therefore, the project does not need to reproduce:

- Astral release filenames,
- uv download metadata,
- uv's managed-Python installation directory,
- `python-build-standalone` full archive metadata,
- uv automatic platform matching.

Those may become future integration topics, but they are explicitly outside the current critical path.

The current success criterion is simpler:

```text
/path/to/python works correctly
        +
uv can inspect it
        +
uv can create a venv from it
        +
the venv interpreter behaves correctly
        +
uv workflows work around that environment
```

---

## 5. Why the tiny launcher is legitimate

The current CLI frontend is:

```c
#include <Python.h>

int main(int argc, char **argv) {
    return Py_BytesMain(argc, argv);
}
```

This is not an exotic custom invention.

The upstream CPython `Programs/python.c` is intentionally a minimal main program. On non-Windows platforms, it calls `Py_BytesMain(argc, argv)`.

That makes the current Stage 1-A frontend strongly grounded in CPython itself.

There is also a second important reference:

Astral's draft Android integration test for uv downloads the official CPython Android package, builds a small executable using the same `Py_BytesMain` pattern, and then exercises uv against that interpreter.

Therefore the project's minimal frontend is supported by two useful reference directions:

```text
CPython CLI reference
    Programs/python.c
        -> Py_BytesMain

Astral uv Android integration reference
    Android Python artifact
        + minimal launcher
        + explicit runtime environment
        + uv venv / uv pip / uv run tests
```

The word "launcher" is convenient in project conversation, but technically "CLI frontend executable" may be less confusing, because `launcher` can also refer to tools such as Windows `py.exe`.

---

## 6. Reference hierarchy

When making a design decision, use references in this order.

### Reference 1: CPython upstream Android

Use for:

- supported Android build process,
- Android package layout,
- embedding assumptions,
- CPython Android runtime behavior,
- testbed behavior.

Primary references:

- CPython Android documentation,
- CPython `Android/README.md`,
- CPython Android testbed,
- Python.org Android release artifacts.

### Reference 2: CPython CLI frontend

Use for:

- CLI entry-point semantics,
- argument forwarding,
- minimal frontend behavior.

Primary reference:

- `Programs/python.c`.

### Reference 3: Astral uv Android integration work

Use for:

- how uv is tested with Android Python,
- minimal launcher precedent,
- explicit environment variables,
- uv workflow validation.

Primary reference:

- `astral-sh/uv` PR #18302, currently a draft reference rather than a stable API contract.

Important: this PR is useful evidence of direction and testing practice, but it should not be treated as released product behavior until merged and released.

### Reference 4: CPython Android source dependencies / BeeWare

Use when investigating:

- OpenSSL,
- SQLite,
- libffi,
- bzip2,
- xz,
- zstd,
- Android-specific native dependency builds.

The BeeWare `cpython-android-source-deps` project contains scripts and prebuilt releases for libraries needed to compile CPython for Android and is directly relevant to understanding the dependency layer behind the Android runtime.

### Reference 5: `python-build-standalone`

Use primarily in Stage 3 for:

- distribution engineering,
- controlled dependency closure,
- portability strategy,
- archive design,
- metadata,
- relocation,
- optimization profiles,
- static/shared linkage trade-offs.

Do not prematurely copy `python-build-standalone` internals into Stage 1. Stage 1 is about understanding the official Android runtime and adapting it with minimal intervention.

---

## 7. Current implementation: what was actually built

It is important to describe the current work accurately.

The current experiment did **not** compile all of CPython from source.

The current implementation is approximately:

```text
official CPython Android aarch64 package
        +
NDK-compiled minimal CLI frontend
        +
python/python3 symlinks
        +
repackaging
        +
Termux deployment
```

The frontend was cross-compiled on a Linux workstation with an Android NDK compiler similar to:

```text
aarch64-linux-android24-clang
```

The installation layout is approximately:

```text
prefix/
├── bin/
│   ├── python
│   ├── python3
│   └── python3.14
├── include/
│   └── python3.14/
└── lib/
    ├── libpython3.14.so
    ├── libssl_python.so
    ├── libcrypto_python.so
    ├── libssl.so
    ├── libcrypto.so
    └── python3.14/
        ├── ssl.py
        └── lib-dynload/
            └── _ssl.cpython-314-aarch64-linux-android.so
```

The current frontend was linked with a launcher-level RUNPATH similar to:

```text
$ORIGIN/../lib
```

That is enough to help the executable find libraries directly needed from `prefix/lib`, but it does not automatically make every later-loaded extension module dependency resolve from that directory.

This distinction became visible through the `_ssl` failure.

---

## 8. The current `_ssl` observation

Observed runtime behavior:

```text
_ssl FAILED:
ImportError(
    'dlopen failed: library "libssl_python.so" not found:
     needed by .../_ssl.cpython-314-aarch64-linux-android.so
     in namespace (default)'
)
```

Inspection showed:

```text
_ssl extension:
prefix/lib/python3.14/lib-dynload/
    _ssl.cpython-314-aarch64-linux-android.so

required OpenSSL libraries:
prefix/lib/libssl_python.so
prefix/lib/libcrypto_python.so
```

The important conclusion is:

> The SSL extension and its dependency libraries are present. The missing piece is the runtime native-library search contract.

Do not summarize this as:

```text
"SSL was not built."
```

That would be wrong.

A better model is:

```text
python frontend starts
    |
    +--> libpython loads

later:
Python imports _ssl
    |
    +--> Android linker loads _ssl.so
              |
              +--> _ssl.so requires libssl_python.so
                       |
                       +--> library exists in prefix/lib
                            but the current loader search context
                            does not find it
```

This is exactly the kind of gap expected when adapting an app-oriented embedded runtime into a Unix-like CLI deployment model.

For Stage 1-A, the baseline response is:

1. establish the explicit environment contract,
2. test the runtime under that contract,
3. document the result,
4. only then consider removing or replacing environment variables.

---

# 9. The three-stage project architecture

The project heart is a three-stage progression.

```text
Stage 1
Upstream Android Runtime + CLI Adaptation

Stage 2
Self-locating Native CLI Runtime

Stage 3
Portable / Standalone Distribution Engineering
```

Stage 1 contains two related implementation tracks:

```text
Stage 1-A
Minimal upstream-style CLI baseline

Stage 1-B
PyConfig-based adaptation experiment
```

The distinction matters.

```text
Stage 1-A = baseline
Stage 1-B = experiment
Stage 2   = synthesis
Stage 3   = distribution engineering
```

---

## 10. Stage 1-A: minimal baseline

### Goal

Use the official CPython Android distribution as a Termux CLI interpreter with the smallest possible adaptation layer.

### Architecture

```text
official CPython Android artifact
        +
minimal Py_BytesMain frontend
        +
explicit runtime environment
        +
uv with explicit interpreter path
```

### Runtime model

```text
env.sh
├── PYTHONHOME
├── PYTHONPATH
└── LD_LIBRARY_PATH
        |
        v
prefix/bin/python
        |
        v
Py_BytesMain(argc, argv)
```

### Why this should be the baseline

This approach is deliberately boring.

Its advantages are:

- very small custom C code,
- direct relationship to CPython's own frontend,
- close relationship to Astral's Android integration test direction,
- clear separation between runtime setup and interpreter behavior,
- easy debugging,
- low risk of hiding a problem behind clever bootstrapping logic.

### Stage 1-A runtime contract

The baseline should explicitly support an environment setup similar to:

```sh
PYTHON_HOME=/absolute/path/to/prefix

export PYTHONHOME="$PYTHON_HOME"
export PYTHONPATH="$PYTHON_HOME/lib/python3.14"
export LD_LIBRARY_PATH="$PYTHON_HOME/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
```

The exact minimum variables should be measured, not assumed.

For example, it may turn out that:

- `PYTHONHOME` is required,
- `PYTHONPATH` is redundant,
- `LD_LIBRARY_PATH` is required for native extension dependencies.

That should be determined experimentally.

Stage 1-A should not hide these facts.

### Stage 1-A completion criteria

The baseline is complete when all of the following are reproducible from scripts.

#### Interpreter basics

```text
python -V
sys.executable
sys.prefix
sys.base_prefix
sys.path
sysconfig.get_platform()
```

#### Native stdlib imports

At minimum:

```python
import ssl
import hashlib
import sqlite3
import ctypes
import bz2
import lzma
import zlib
```

#### Networking

At minimum:

```text
Python HTTPS request succeeds
CA certificate behavior is understood and documented
```

#### venv

At minimum:

```text
python -m venv works, or its Android-specific limitation is documented

uv venv -p /path/to/base/python .venv works

.venv/bin/python works

native stdlib imports also work inside the venv
```

#### uv workflow

At minimum:

```text
uv recognizes the interpreter
uv creates the venv
uv installs a pure-Python package
uv run works
uv pip install works
```

Later tests may include packages with native extensions, but Stage 1-A should not confuse Android wheel ecosystem limitations with interpreter correctness.

---

## 11. Stage 1-B: PyConfig adaptation experiment

### Goal

Explore whether a native Android-aware frontend can remove Python-level environment setup while staying close to CPython upstream patterns.

The upstream CPython Android testbed uses explicit initialization with `PyConfig`, including:

```text
PyConfig_InitPythonConfig
PyConfig_SetBytesArgv
config.home
Py_InitializeFromConfig
Py_RunMain
```

This makes `PyConfig` a strong reference for a more explicit Android-oriented frontend.

### Experimental architecture

```text
prefix/bin/python
        |
        +--> determine executable location
        |
        +--> derive prefix
        |
        +--> configure Python home with PyConfig
        |
        +--> preserve CLI argv semantics
        |
        v
Py_InitializeFromConfig
        |
        v
Py_RunMain
```

### Important limitation

`PyConfig` is a Python runtime configuration mechanism.

It does **not** automatically solve:

```text
_ssl.so
    ->
libssl_python.so
```

native linker lookup.

Therefore Stage 1-B must keep these as separate concerns:

```text
Python path configuration
    -> PyConfig

Native library resolution
    -> Android linker behavior
       LD_LIBRARY_PATH
       RUNPATH
       bootstrap strategy
       or another native loading design
```

### Why keep Stage 1-A while experimenting with 1-B

The baseline is the control group.

```text
A works, B fails
    -> investigate frontend / PyConfig behavior

A fails, B fails
    -> investigate artifact, environment, or Android runtime behavior
```

Do not replace the Stage 1-A baseline with a cleverer Stage 1-B implementation before the comparison is understood.

---

## 12. Stage 2: self-locating native CLI runtime

Stage 2 is not merely "use PyConfig."

Stage 2 begins after Stage 1-B has produced enough evidence to choose a stable runtime design.

### Goal

Provide a CLI Python that can be invoked by absolute path without requiring the user to manually source a runtime environment file.

Desired user experience:

```sh
uv venv -p ~/opt/cpython-android/prefix/bin/python .venv
```

with no manual runtime setup.

### Stage 2 responsibilities

A real Stage 2 design must solve:

```text
1. executable self-location
2. prefix discovery
3. Python home configuration
4. stdlib discovery
5. native dependency lookup
6. venv interpreter behavior
7. relocation semantics
8. subprocess behavior where Android allows it
```

### Native library strategy candidates

Do not choose prematurely.

Candidates include:

```text
A. Keep LD_LIBRARY_PATH, but bootstrap it automatically.

B. Add ELF RUNPATH rules.

C. Use a bootstrap + re-exec model.

D. Investigate Android linker APIs.

E. Re-layout or relink the dependency graph.
```

The selected design should be based on measurements from Stage 1, not aesthetic preference alone.

### Stage 2 output

Stage 2 should result in a supported runtime contract and a small architecture document explaining:

- how prefix discovery works,
- how Python path configuration works,
- how native library lookup works,
- how venvs refer back to the base runtime,
- what relocation guarantees are made.

---

## 13. Stage 3: portable / standalone distribution engineering

This stage is deliberately deferred.

### Goal

Move from "CLI adaptation of the official Android runtime" toward a deliberately engineered portable distribution.

This is where `python-build-standalone` becomes a primary architectural reference.

Potential topics:

```text
controlled dependency builds
reproducible build pipeline
dependency closure
RUNPATH design
relocation
archive layout
stripping
debug artifacts
metadata
PGO
LTO
static vs shared linkage
extension-module loading
license aggregation
SBOM / provenance
multiple Android API levels
multiple architectures
```

### Why not start here

Starting here would mix too many unknowns:

```text
CPython Android behavior
+
cross compilation
+
native dependency builds
+
dynamic linker behavior
+
archive design
+
uv behavior
+
venv behavior
+
package build behavior
```

The staged approach keeps responsibility boundaries understandable.

### Static build preference

Portable and static builds are an explicit area of interest, but a static build is not automatically better.

Potential complications include:

- dynamically loaded Python extension modules,
- native wheels,
- symbol visibility,
- libc / bionic constraints,
- OpenSSL and other dependency policies,
- Android linker behavior.

Therefore:

> Static or aggressively portable builds are a Stage 3 research topic, not a requirement for Stage 1 success.

---

## 14. Why Android differs from conventional Linux for this project

Android uses the Linux kernel, but this project should not treat Android as "just another glibc Linux distribution."

The important practical differences are at the deployment and userspace level.

### Conventional Linux CLI model

Conceptually:

```text
/usr/bin/python
        |
        +--> system loader
        |
        +--> system libraries
        |
        +--> standard filesystem paths
        |
        +--> distribution package manager
```

### Official Android Python model

Conceptually:

```text
Android app
        |
        +--> app native libraries
        |
        +--> embedded libpython
        |
        +--> packaged stdlib
        |
        +--> packaged extension modules
        |
        +--> app-private native dependencies
```

### This project

```text
Android / Termux shell
        |
        +--> custom CLI frontend
        |
        +--> official Android CPython runtime
        |
        +--> adapted runtime environment
        |
        +--> uv as external environment manager
```

This third model is unusual, but it is not inherently invalid.

It is best described as:

> Standard upstream components used for a non-standard deployment target.

---

## 15. Proposed repository structure

A modest repository layout:

```text
project/
├── README.md
├── LICENSE
├── docs/
│   ├── PROJECT_CONTEXT.md
│   ├── design-notes.md
│   └── decisions/
│       ├── 0001-upstream-android-artifact.md
│       ├── 0002-stage-1a-baseline.md
│       └── 0003-pyconfig-experiment.md
├── runtime/
│   ├── python-launcher.c
│   └── env.sh
├── scripts/
│   ├── fetch-python.sh
│   ├── build-launcher.sh
│   ├── package.sh
│   └── deploy-termux.sh
└── tests/
    ├── smoke.sh
    ├── stdlib-native.sh
    ├── network.sh
    ├── venv.sh
    └── uv.sh
```

This should stay proportional to a personal project.

The goal is not bureaucracy. The goal is to preserve:

```text
baseline
hypothesis
experiment
decision
result
```

A short decision note is enough when a non-obvious choice is made.

---

## 16. Recommended immediate work plan

The current project should continue in this order.

### Step 1: finish Stage 1-A environment contract

Create a reproducible `env.sh`.

Start from the explicit environment used by the Astral Android integration test:

```sh
PYTHON_HOME=/absolute/path/to/prefix

export PYTHONHOME="$PYTHON_HOME"
export PYTHONPATH="$PYTHON_HOME/lib/python3.14"
export LD_LIBRARY_PATH="$PYTHON_HOME/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
```

Then test whether each variable is truly required.

Do not optimize before measuring.

### Step 2: verify `_ssl` under the Stage 1-A contract

Run:

```sh
python - <<'PY'
import _ssl
import ssl

print(_ssl.__file__)
print(ssl.OPENSSL_VERSION)
print(ssl.get_default_verify_paths())
PY
```

Then test real HTTPS.

If library loading works but certificate verification fails, treat CA configuration as a separate issue.

### Step 3: audit native stdlib modules

Run at least:

```python
import ssl
import hashlib
import sqlite3
import ctypes
import bz2
import lzma
import zlib
```

Record:

- success,
- missing module,
- loader failure,
- missing dependency,
- unsupported Android behavior.

### Step 4: verify uv and venv behavior

Test:

```sh
uv venv --no-python-downloads -p "$PYTHON_BIN" .venv
```

Then:

```sh
.venv/bin/python -V
.venv/bin/python -c 'import ssl, sqlite3, ctypes'
```

Then:

```sh
uv pip install -p .venv/bin/python anyio
uv run -p .venv/bin/python python -c 'import anyio; print(anyio.__name__)'
```

Use a pure-Python package first so interpreter correctness is not mixed with Android native-wheel availability.

### Step 5: inspect interpreter identity and packaging tags

Capture:

```python
import sys
import sysconfig

print(sys.platform)
print(sys.executable)
print(sys.prefix)
print(sys.base_prefix)
print(sysconfig.get_platform())
```

Also inspect Python packaging tags from an environment with `packaging` available.

This will matter later for Android wheel compatibility.

### Step 6: freeze Stage 1-A as the baseline

Once reproducible:

- tag or commit the baseline,
- document the runtime contract,
- keep the minimal launcher unchanged,
- preserve tests.

### Step 7: start Stage 1-B separately

Build a PyConfig-based frontend as an experiment.

Compare it against the baseline with the same test suite.

Measure exactly which external environment variables can be removed.

---

## 17. Suggested validation matrix

| Area | Stage 1-A | Stage 1-B | Stage 2 | Stage 3 |
|---|---:|---:|---:|---:|
| CPython Android artifact | official | official | official or derived | custom build possible |
| Minimal CLI execution | required | required | required | required |
| uv interpreter recognition | required | required | required | required |
| uv venv | required | required | required | required |
| Native stdlib imports | required | required | required | required |
| Explicit env file | allowed | compare | no user setup | no user setup |
| Self-location | no | experiment | required | required |
| Native loader strategy | explicit env | experiment | designed | engineered |
| Relocation guarantee | none/minimal | experimental | documented | strong goal |
| Static build | no | no | optional research | possible focus |
| Reproducible dependency builds | no | no | optional | expected |

---

## 18. Decision log so far

### Decision A: use uv as the environment manager, not as the Python builder

Reason:

- uv can use an explicit Python executable path,
- automatic uv-managed Python download is not required,
- this keeps Android runtime work separate from uv's download system.

### Decision B: start from the official CPython Android artifact

Reason:

- upstream preference,
- avoids solving CPython Android cross-compilation and dependency builds before the CLI adaptation problem is understood,
- creates a clear responsibility boundary.

### Decision C: use a minimal `Py_BytesMain` frontend as Stage 1-A

Reason:

- matches CPython's minimal Unix CLI entry-point pattern,
- matches the direction used in Astral's draft Android integration test,
- smallest custom surface area.

### Decision D: treat explicit environment variables as a valid Stage 1-A baseline

Reason:

- baseline should expose runtime requirements rather than hide them,
- Astral's Android integration work uses explicit `PYTHONHOME`, `PYTHONPATH`, and `LD_LIBRARY_PATH`,
- the current `_ssl` failure demonstrates that native loader setup is part of the runtime contract.

### Decision E: investigate PyConfig separately as Stage 1-B

Reason:

- CPython's Android testbed provides a strong upstream reference,
- it may remove Python-level environment setup,
- it must not be confused with native dynamic linker configuration.

### Decision F: defer portability and static linking to Stage 3

Reason:

- first establish correctness,
- avoid mixing runtime adaptation with full distribution engineering,
- preserve `python-build-standalone` as a later architectural reference rather than prematurely copying it.

---

## 19. Open questions

These are intentionally unresolved.

### Stage 1-A

1. Which of `PYTHONHOME`, `PYTHONPATH`, and `LD_LIBRARY_PATH` are actually required?
2. Does `_ssl` work under the explicit environment?
3. What CA certificate configuration is required in Termux?
4. Which native stdlib modules work without modification?
5. Does `python -m venv` work independently of uv?
6. How does uv-created venv Python refer to the base interpreter?
7. What is the exact Android platform tag exposed by this runtime?
8. Which package installation failures are interpreter problems versus Android wheel availability problems?

### Stage 1-B

1. Can `PyConfig.home` replace `PYTHONHOME`?
2. Is explicit `PYTHONPATH` unnecessary once `PyConfig` is correct?
3. What is the safest executable self-location method on Android/Termux?
4. How should symlinks and venv entry points affect prefix discovery?
5. What should remain external to Python initialization because it belongs to the native linker?

### Stage 2

1. RUNPATH versus bootstrap/re-exec versus another linker strategy?
2. What relocation guarantee is realistic?
3. Can a single prefix be moved arbitrarily?
4. How should native extension dependencies be validated automatically?
5. How should venvs behave if the base prefix moves?

### Stage 3

1. Is a `python-build-standalone` Android target worth pursuing?
2. Should dependencies be rebuilt from the BeeWare/CPython source-deps reference chain?
3. What should be static, and what should remain dynamically loadable?
4. What archive layout and metadata are actually useful?
5. Is uv-managed automatic download desirable later, or is explicit-path use sufficient?

---

## 20. Handoff notes for a future AI agent

Before making code changes:

1. Read this document.
2. Do not assume the goal is to port `python-build-standalone` immediately.
3. Do not assume the current `_ssl` error means OpenSSL is missing.
4. Preserve Stage 1-A as a baseline.
5. Keep Python runtime configuration separate from native dynamic linker configuration.
6. Prefer upstream CPython and official Astral references over invented mechanisms.
7. When proposing a custom mechanism, explain:
   - what upstream behavior it replaces,
   - why the upstream mechanism is insufficient,
   - which stage the change belongs to,
   - how it will be tested against the baseline.
8. Avoid changing multiple layers in one experiment.
9. Use the same validation suite for Stage 1-A and Stage 1-B.
10. Treat Astral PR #18302 as a useful draft reference, not a stable released contract.

A good next task for an agent is:

> Implement and document the Stage 1-A runtime environment contract, then run the native stdlib and uv validation matrix without introducing ELF patching or self-location logic.

---

## 21. Reference map

### CPython upstream

1. **Using Python on Android**  
   https://docs.python.org/3/using/android.html

2. **CPython 3.14.6 Android build README**  
   https://github.com/python/cpython/blob/v3.14.6/Android/README.md

3. **CPython 3.14.6 minimal CLI frontend**  
   https://github.com/python/cpython/blob/v3.14.6/Programs/python.c

4. **CPython 3.14.6 Android testbed native initialization**  
   https://github.com/python/cpython/blob/v3.14.6/Android/testbed/app/src/main/c/main_activity.c

5. **Python.org Android downloads**  
   https://www.python.org/downloads/android/

6. **Python initialization configuration C API**  
   https://docs.python.org/3/c-api/init_config.html

### uv / Astral

7. **uv Python versions**  
   https://docs.astral.sh/uv/concepts/python-versions/

8. **uv Python installation guide**  
   https://docs.astral.sh/uv/guides/install-python/

9. **uv environment variables (`UV_PYTHON`)**  
   https://docs.astral.sh/uv/reference/environment/

10. **uv Android integration test draft PR #18302**  
    https://github.com/astral-sh/uv/pull/18302

### Python distribution engineering

11. **python-build-standalone documentation**  
    https://gregoryszorc.com/docs/python-build-standalone/main/

12. **python-build-standalone distribution archive format**  
    https://gregoryszorc.com/docs/python-build-standalone/main/distributions.html

### Android CPython native dependencies

13. **BeeWare CPython Android source dependencies**  
    https://github.com/beeware/cpython-android-source-deps

### Comparison references

14. **Conda documentation**  
    https://docs.conda.io/

15. **Conda repository and environment model**  
    https://github.com/conda/conda

16. **Debian Python Policy**  
    https://www.debian.org/doc/packaging-manuals/python-policy/

---

## 22. Final project principle

The project should advance in this order:

```text
understand
    ->
reproduce
    ->
measure
    ->
compare
    ->
design
    ->
optimize
```

Not:

```text
patch
    ->
patch more
    ->
accidentally invent a distribution
```

The intended reference chain is:

```text
official CPython Android artifact
        |
        +--> CPython Programs/python.c
        |       for CLI semantics
        |
        +--> CPython Android testbed
        |       for Android initialization semantics
        |
        +--> CPython Android source-deps / BeeWare
        |       for native dependency understanding
        |
        +--> Astral uv Android integration work
        |       for uv compatibility testing
        |
        +--> python-build-standalone
                later, for portable distribution engineering
```

That chain is the project's architectural center.

The immediate task is to complete **Stage 1-A** cleanly, preserve it as a baseline, and only then use **Stage 1-B** to explore a better native frontend. Stage 2 should synthesize proven ideas into a self-locating runtime. Stage 3 can then pursue the author's longer-term interest in portability, relocation, and possibly static build techniques without losing the upstream-grounded foundation of the project.
