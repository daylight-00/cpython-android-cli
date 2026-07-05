# Stage 1-A Freeze: Upstream Android CPython CLI Baseline for Termux + uv

> **Status:** Frozen baseline  
> **Stage:** 1-A — Minimal upstream-style CLI adaptation  
> **Target:** Android arm64 / `aarch64-linux-android` / Termux  
> **Python:** CPython 3.14.6  
> **Validation workspace:** `~/tmp/260704/stage1a/`  
> **Original packaged artifact:** `~/uv-base/cpython-3.14-aarch64-linux-android-for-uv.tar.gz`  
> **Freeze date:** 2026-07-05 KST

---

## 1. Purpose of this freeze

This document freezes the completed Stage 1-A baseline before beginning Stage 1-B.

The purpose of Stage 1-A was not to create a portable Python distribution and not to port `python-build-standalone` to Android.

The purpose was narrower:

> Determine the smallest explicit adaptation required to use an upstream-built CPython Android runtime as a normal CLI interpreter in Termux and to use that interpreter successfully with uv.

The completed Stage 1-A baseline proves that this is possible.

The final design uses:

- a CPython 3.14.6 Android build produced from upstream CPython sources and upstream Android build infrastructure,
- a minimal CPython-style CLI frontend based on `Py_BytesMain`,
- explicit Termux runtime integration for native library lookup and CA trust,
- uv with an explicit Python interpreter path.

Stage 1-A deliberately does **not** solve relocation, self-location, RUNPATH engineering, static linking, automatic uv-managed Python downloads, or PyConfig-based initialization.

Those topics belong to later stages.

---

## 2. Frozen project model

The final Stage 1-A architecture is:

```text
CPython 3.14.6 upstream source
        |
        v
CPython upstream Android build infrastructure
        |
        v
locally built aarch64-linux-android prefix
        |
        v
minimal Py_BytesMain CLI frontend
        |
        v
explicit Termux runtime adaptation
        |
        +-- LD_LIBRARY_PATH=<cpython-prefix>/lib
        |
        +-- SSL_CERT_FILE=<termux-prefix>/etc/tls/cert.pem
        |
        v
uv with explicit Python interpreter path
```

A concise project description for this stage is:

> **A CLI adaptation of an upstream CPython Android build for Termux, with uv integration.**

A slightly more descriptive version is:

> **An experiment in using an upstream-built CPython Android runtime as a Termux CLI interpreter managed through uv.**

---

## 3. What Stage 1-A is based on

Stage 1-A intentionally follows a reference chain rather than inventing a new runtime architecture.

### 3.1 CPython upstream Android build support

CPython provides Android-specific build infrastructure and documentation for producing Android runtime artifacts.

Reference:

- CPython Android documentation  
  https://docs.python.org/3/using/android.html

- CPython Android build README  
  https://github.com/python/cpython/blob/v3.14.6/Android/README.md

### 3.2 CPython's own minimal CLI frontend pattern

The Stage 1-A executable uses the same basic entry-point model as CPython's normal CLI frontend:

```c
#include <Python.h>

int main(int argc, char **argv) {
    return Py_BytesMain(argc, argv);
}
```

Reference:

- CPython `Programs/python.c`  
  https://github.com/python/cpython/blob/v3.14.6/Programs/python.c

This means the Stage 1-A CLI frontend is intentionally minimal. It does not attempt to reimplement Python initialization logic.

### 3.3 Astral uv Android integration direction

Astral's draft Android integration work also uses:

- an Android CPython runtime,
- a small `Py_BytesMain` frontend,
- explicit runtime environment variables,
- `uv venv`,
- `uv pip`,
- `uv run`.

Reference:

- uv Android integration draft PR  
  https://github.com/astral-sh/uv/pull/18302

This PR is used as a directional reference and validation precedent, not as a released stable contract.

### 3.4 uv external interpreter model

uv can work with an explicitly selected Python interpreter. Stage 1-A therefore does not require uv to build, download, or manage the base Android Python.

References:

- uv Python versions  
  https://docs.astral.sh/uv/concepts/python-versions/

- uv environments and explicit Python selection  
  https://docs.astral.sh/uv/pip/environments/

---

## 4. Provenance of the frozen baseline

The Stage 1-A runtime under test is based on:

```text
CPython 3.14.6 source
+
upstream Android build tooling
+
aarch64-linux-android target
+
local build output prefix
+
minimal CLI frontend
+
packaging into a tar.gz artifact
```

The original packaged artifact used for the final pristine validation is:

```text
~/uv-base/cpython-3.14-aarch64-linux-android-for-uv.tar.gz
```

The final validation did **not** use the already-installed prefix as the source of truth.

That distinction matters because the installed prefix had previously been modified during an exploratory `patchelf` experiment.

---

## 5. Important separation: pristine baseline vs earlier RUNPATH experiment

Before the final pristine validation, the installed prefix had been modified with:

```sh
CPY="$HOME/opt/cpython-3.14/prefix"
LIBDIR="$(dirname "$(find "$CPY" -name 'libssl_python.so' | head -1)")"

for m in \
    "$CPY"/lib/python3.14/lib-dynload/_ssl*.so \
    "$CPY"/lib/python3.14/lib-dynload/_hashlib*.so
do
    patchelf --add-rpath "$LIBDIR" "$m" 2>/dev/null \
        || patchelf --set-rpath "$LIBDIR" "$m"
done
```

This caused `_ssl` and `_hashlib` to contain an absolute RUNPATH pointing to the installed prefix:

```text
/data/data/com.termux/files/home/opt/cpython-3.14/prefix/lib
```

As a result:

```text
_ssl      worked without LD_LIBRARY_PATH
_hashlib  worked without LD_LIBRARY_PATH
_sqlite3  still failed without LD_LIBRARY_PATH
```

The ELF inspection explained the difference:

```text
_ssl.so
    RUNPATH -> installed prefix/lib

_hashlib.so
    RUNPATH -> installed prefix/lib

_sqlite3.so
    no equivalent RUNPATH
```

Therefore the installed prefix was not suitable as a pristine Stage 1-A baseline.

The final validation extracted the original tarball to a new directory and tested that fresh prefix instead.

The earlier absolute RUNPATH experiment is retained only as a historical experiment and a possible Stage 2 design note.

It is **not** part of Stage 1-A.

---

## 6. Final runtime contract

The frozen Stage 1-A runtime contract is:

```sh
CPYTHON_PREFIX="$HOME/opt/cpython-3.14/prefix"

export LD_LIBRARY_PATH="$CPYTHON_PREFIX/lib"
export SSL_CERT_FILE="$PREFIX/etc/tls/cert.pem"
```

The Python interpreter is then passed explicitly to uv:

```sh
uv venv \
    --no-python-downloads \
    --python "$CPYTHON_PREFIX/bin/python" \
    .venv
```

### Required

```text
LD_LIBRARY_PATH=<cpython-prefix>/lib
SSL_CERT_FILE=<termux-prefix>/etc/tls/cert.pem
```

### Not required

```text
PYTHONHOME
PYTHONPATH
```

This is a major Stage 1-A result.

The built CPython runtime successfully discovers:

- its base prefix,
- the standard library,
- `sys.prefix`,
- `sys.base_prefix`,
- Android platform identity,
- venv identity,

without explicit `PYTHONHOME` or `PYTHONPATH`.

---

## 7. Why two runtime variables are needed

The final contract has two separate responsibilities.

### 7.1 Native shared-library lookup

Some CPython Android extension modules depend on companion native libraries in the Python prefix.

Examples:

```text
_ssl.so
    -> libssl_python.so
    -> libcrypto_python.so

_hashlib.so
    -> libcrypto_python.so

_sqlite3.so
    -> libsqlite3_python.so
```

In the pristine artifact, a clean environment does not resolve these libraries from `prefix/lib`.

Therefore Stage 1-A uses:

```sh
LD_LIBRARY_PATH="$CPYTHON_PREFIX/lib"
```

This is an explicit native runtime contract.

### 7.2 Termux CA trust-store integration

With native libraries resolvable, Python SSL imports and initializes correctly, but HTTPS verification still fails in a clean environment because the Android CPython OpenSSL configuration does not automatically use the Termux CA bundle.

Stage 1-A integrates the host trust store with:

```sh
SSL_CERT_FILE="$PREFIX/etc/tls/cert.pem"
```

This makes the architecture explicitly layered:

```text
runtime adaptation
|
+-- native linker integration
|     LD_LIBRARY_PATH
|
+-- host trust-store integration
      SSL_CERT_FILE
```

This separation should be preserved in later stages.

---

## 8. Final validation profiles

The final validator used four profiles.

### 8.1 `clean`

```text
PYTHONHOME       unset
PYTHONPATH       unset
LD_LIBRARY_PATH  unset
SSL_CERT_FILE    unset
SSL_CERT_DIR     unset
```

Purpose:

> Measure the behavior of the pristine artifact without Termux adaptation.

Result:

```text
FAIL
```

Expected failures included native dependency lookup and HTTPS trust.

This profile is not expected to be production-usable in Stage 1-A.

---

### 8.2 `native`

```text
PYTHONHOME       unset
PYTHONPATH       unset
LD_LIBRARY_PATH  <cpython-prefix>/lib
SSL_CERT_FILE    unset
SSL_CERT_DIR     unset
```

Purpose:

> Isolate native shared-library resolution from CA trust integration.

Result:

```text
FAIL overall
```

But:

```text
native stdlib imports  PASS
uv venv                PASS
venv identity          PASS
uv pip                 PASS
uv run                 PASS
HTTPS verification     FAIL
```

This profile proved that native loader integration and CA trust are separate concerns.

---

### 8.3 `termux`

```text
PYTHONHOME       unset
PYTHONPATH       unset
LD_LIBRARY_PATH  <cpython-prefix>/lib
SSL_CERT_FILE    <termux-prefix>/etc/tls/cert.pem
SSL_CERT_DIR     unset
```

Purpose:

> Test the intended Stage 1-A runtime contract.

Result:

```text
PASS
```

All required probes passed.

This is the frozen Stage 1-A baseline.

---

### 8.4 `fullenv-reference`

```text
PYTHONHOME       <cpython-prefix>
PYTHONPATH       <cpython-prefix>/lib/python3.14
LD_LIBRARY_PATH  <cpython-prefix>/lib
SSL_CERT_FILE    <termux-prefix>/etc/tls/cert.pem
```

Purpose:

> Compare against a more explicit environment style similar to Android integration references.

Result:

```text
PASS
```

However, because the smaller `termux` profile also passed, Stage 1-A does not include `PYTHONHOME` or `PYTHONPATH`.

---

## 9. Validation coverage

The final Stage 1-A validation covered all of the following.

### 9.1 Interpreter identity

The validator recorded and checked:

```text
sys.executable
sys.prefix
sys.base_prefix
sys.exec_prefix
sys.base_exec_prefix
sys.platform
sysconfig.get_platform()
```

The runtime identified itself as Android and preserved normal venv identity behavior.

---

### 9.2 Native standard-library modules

The base interpreter was tested with:

```python
import _ssl
import ssl

import _hashlib
import hashlib

import _sqlite3
import sqlite3

import _ctypes
import ctypes

import _bz2
import bz2

import _lzma
import lzma

import zlib
```

The `termux` profile passed all required imports.

---

### 9.3 HTTPS

The validator performed a real HTTPS request to PyPI using Python's standard library.

The `termux` profile passed with a successful HTTPS response.

This confirms the complete path:

```text
_ssl extension
    ->
OpenSSL libraries
    ->
CA trust configuration
    ->
certificate verification
    ->
HTTPS request
```

---

### 9.4 uv virtual environment creation

The validator ran:

```sh
uv venv \
    --no-python-downloads \
    --python "$CPYTHON_BIN" \
    <venv-path>
```

Result:

```text
PASS
```

---

### 9.5 venv identity

The created venv was validated using:

```python
sys.prefix != sys.base_prefix
```

Result:

```text
PASS
```

The venv interpreter also successfully imported the tested native standard-library modules.

---

### 9.6 uv pip

The validator installed a pure-Python dependency into the explicit venv using uv.

Result:

```text
PASS
```

The installed package was successfully imported from the venv.

---

### 9.7 uv run

The validator also exercised uv's execution environment workflow with an explicitly selected Python.

Result:

```text
PASS
```

This confirms that Stage 1-A is not limited to manually created venvs.

---

## 10. Artifact integrity validation

The pristine tarball was extracted into a fresh test directory.

The first integrity test initially reported a failure because Python generated normal bytecode caches:

```text
__pycache__/
*.cpython-314.pyc
```

This was not a mutation of Python binaries, shared libraries, or source files.

The corrected pristine validation used:

```text
PYTHONPYCACHEPREFIX=<external-cache-directory>
```

so Python bytecode caches were generated outside the extracted prefix.

Final result:

```text
Artifact integrity: PASS
The extracted CPython prefix was not modified.
```

During validation, 266 `.pyc` files were generated outside the prefix.

Final paths:

```text
Prefix:
~/tmp/260704/stage1a/pristine-v2/extracted/prefix

Results:
~/tmp/260704/stage1a/pristine-v2/results

Pycache:
~/tmp/260704/stage1a/pristine-v2/pycache
```

This establishes that the final validation used a pristine runtime tree and did not modify it.

---

## 11. Stage 1-A completion criteria

The Stage 1-A completion checklist is now:

```text
[PASS] base interpreter executes
[PASS] prefix discovery is correct
[PASS] Android platform identity is correct
[PASS] ssl works
[PASS] hashlib works
[PASS] sqlite3 works
[PASS] ctypes works
[PASS] bz2 works
[PASS] lzma works
[PASS] zlib works
[PASS] Python HTTPS works
[PASS] uv accepts the explicit interpreter
[PASS] uv venv succeeds
[PASS] venv identity is correct
[PASS] native stdlib works inside the venv
[PASS] uv pip install works
[PASS] installed dependency imports correctly
[PASS] uv run works
[PASS] minimum runtime environment is documented
[PASS] pristine artifact integrity is preserved
```

Stage 1-A is therefore complete.

---

## 12. Frozen Stage 1-A usage example

A minimal Termux runtime helper may be:

```sh
CPYTHON_PREFIX="$HOME/opt/cpython-3.14/prefix"
CPYTHON_BIN="$CPYTHON_PREFIX/bin/python"

export LD_LIBRARY_PATH="$CPYTHON_PREFIX/lib"
export SSL_CERT_FILE="$PREFIX/etc/tls/cert.pem"
```

Use with uv:

```sh
uv venv \
    --no-python-downloads \
    --python "$CPYTHON_BIN" \
    .venv
```

Install into the venv:

```sh
uv pip install \
    --python .venv/bin/python \
    anyio
```

Run:

```sh
uv run \
    --no-python-downloads \
    --python "$CPYTHON_BIN" \
    python -V
```

A stricter wrapper may scope the runtime environment to a single command:

```sh
cpython_runtime() {
    env \
        -u PYTHONHOME \
        -u PYTHONPATH \
        LD_LIBRARY_PATH="$CPYTHON_PREFIX/lib" \
        SSL_CERT_FILE="$PREFIX/etc/tls/cert.pem" \
        "$@"
}
```

Example:

```sh
cpython_runtime \
    uv venv \
    --no-python-downloads \
    --python "$CPYTHON_BIN" \
    .venv
```

---

## 13. What Stage 1-A deliberately does not solve

The following are explicitly outside the frozen Stage 1-A scope.

### No self-location

The runtime does not automatically derive its prefix from the executable location.

### No relocation guarantee

The Stage 1-A contract does not promise arbitrary movement of the prefix.

### No RUNPATH engineering

No relative `$ORIGIN` RUNPATH design is part of the baseline.

### No `patchelf` requirement

The earlier absolute RUNPATH experiment is excluded from the baseline.

### No PyConfig frontend

Stage 1-A uses the minimal `Py_BytesMain` frontend.

### No bootstrap or re-exec logic

The frontend does not rewrite its own environment and execute itself again.

### No static build goal

Static linking remains a later research topic.

### No uv-managed Python integration

Stage 1-A does not add Android Python to uv's automatic Python download system.

The base Python is selected explicitly by path.

---

## 14. Stage 1-A design decisions

### Decision 1: keep the CLI frontend minimal

Reason:

- strongest relationship to CPython's own CLI frontend,
- minimal custom code,
- easy comparison with upstream behavior,
- easy debugging.

### Decision 2: use explicit runtime adaptation

Reason:

- Stage 1-A is a baseline,
- requirements should be visible rather than hidden,
- native linker integration and CA trust can be measured independently.

### Decision 3: do not use `PYTHONHOME` or `PYTHONPATH`

Reason:

- the runtime successfully discovers Python paths without them,
- the smaller environment is sufficient,
- fewer environment overrides improve clarity.

### Decision 4: keep the earlier `patchelf` experiment outside the baseline

Reason:

- it changed observed runtime behavior,
- it used an absolute installed path,
- it obscured the behavior of the pristine artifact,
- it belongs to later native-path research.

### Decision 5: use the pristine tarball as the source of truth

Reason:

- installed prefixes may have experimental modifications,
- extracted test prefixes are reproducible,
- before/after hashing can validate artifact integrity.

---

## 15. Transition to Stage 1-B

Stage 1-B should begin from the frozen Stage 1-A evidence, not from the earlier patched installation.

The first Stage 1-B question is:

> Can a PyConfig-based frontend provide a cleaner upstream-style foundation for future self-location while preserving normal CLI behavior, uv integration, and venv semantics?

However, Stage 1-A already established an important constraint:

```text
Python-level path discovery:
    already works

native shared-library discovery:
    separate problem

CA trust integration:
    separate problem
```

Therefore PyConfig should not be treated as a solution to all remaining problems.

Stage 1-B should investigate Python initialization structure and future self-location only.

Native linker behavior must remain a separately measured layer.

---

## 16. Transition to later stages

The project stages remain:

```text
Stage 1-A
    baseline:
    minimal CLI frontend
    explicit runtime environment

Stage 1-B
    experiment:
    PyConfig-based frontend

Stage 2
    synthesis:
    self-locating native CLI runtime

Stage 3
    distribution engineering:
    portability
    relocation
    dependency closure
    RUNPATH design
    possible static-linking research
    possible python-build-standalone Android work
```

Stage 1-A is now frozen and should remain unchanged except for bug fixes to documentation or test tooling.

---

## 17. Handoff summary

For a future developer or AI agent:

1. Stage 1-A is complete.
2. Do not add RUNPATH patches to the Stage 1-A baseline.
3. Do not assume `PYTHONHOME` or `PYTHONPATH` are required.
4. The required baseline runtime contract is:

   ```text
   LD_LIBRARY_PATH=<cpython-prefix>/lib
   SSL_CERT_FILE=<termux-prefix>/etc/tls/cert.pem
   ```

5. The original tarball is the pristine source of truth:

   ```text
   ~/uv-base/cpython-3.14-aarch64-linux-android-for-uv.tar.gz
   ```

6. The installed prefix may contain an old absolute-RUNPATH experiment.
7. Preserve the pristine validation methodology.
8. Stage 1-B should compare against this baseline using the same validation matrix.
9. Keep Python initialization, native linker behavior, and CA trust as separate layers.
10. Any new custom mechanism must explain exactly which Stage 1-A limitation it is intended to remove.

---

## 18. Final statement

Stage 1-A successfully demonstrated that:

> An upstream-built CPython Android runtime can be adapted into a practical Termux CLI interpreter with a minimal CPython-style frontend and a small explicit runtime contract, and that uv can successfully create environments, install packages, and run code using that interpreter without managing or downloading the base Python itself.

That result is now the frozen baseline for the next stage of the project.
