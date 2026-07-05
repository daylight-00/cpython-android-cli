# Stage 1-B Freeze: PyConfig Frontend Selection

> **Status:** Frozen  
> **Stage:** 1-B — PyConfig frontend experiment  
> **Target:** Android arm64 / `aarch64-linux-android` / Termux  
> **Python:** CPython 3.14.6  
> **Validation date:** 2026-07-05 KST  
> **Baseline:** Stage 1-A frozen runtime contract

---

## 1. Purpose of Stage 1-B

Stage 1-B asked a narrow question:

> Can a PyConfig-based frontend replace the Stage 1-A `Py_BytesMain` frontend while preserving the tested CLI, runtime, venv, subprocess, and uv behavior?

The answer is:

> **Yes.**

Two PyConfig variants were tested:

- **B0 / auto-discovery**
  - uses PyConfig initialization,
  - does not set `config.home`,
  - relies on normal executable/layout-based path discovery.

- **B1 / explicit home**
  - uses the same PyConfig initialization path,
  - additionally sets `config.home`,
  - obtains the value from a project-specific `CPYTHON_HOME` environment variable.

Both variants passed the broad functional comparison.

However, only B0 is selected for the next stage.

The final Stage 1-B decision is:

> **Use the B0 PyConfig frontend as the preferred next-stage foundation.**

B1 remains a reference experiment.

---

## 2. Relationship to Stage 1-A

Stage 1-A proved that an upstream-built CPython Android runtime could be used as a practical Termux CLI interpreter with uv.

Stage 1-A used:

```text
frontend:
  Py_BytesMain

runtime contract:
  LD_LIBRARY_PATH=<cpython-prefix>/lib
  SSL_CERT_FILE=<termux-prefix>/etc/tls/cert.pem
```

Stage 1-B did **not** attempt to remove or redesign that runtime contract.

The only intended change was:

```text
Stage 1-A frontend
    Py_BytesMain

        ↓

Stage 1-B frontend
    PyConfig initialization
```

The runtime integration remained unchanged:

```text
LD_LIBRARY_PATH=<cpython-prefix>/lib
SSL_CERT_FILE=<termux-prefix>/etc/tls/cert.pem
```

Therefore Stage 1-B is a frontend-initialization experiment, not a native-linker or CA-trust redesign.

---

## 3. Reference initialization model

The selected B0 frontend follows this structure:

```c
PyConfig config;
PyStatus status;

PyConfig_InitPythonConfig(&config);

status = PyConfig_SetBytesArgv(
    &config,
    argc,
    argv
);

status = Py_InitializeFromConfig(&config);

PyConfig_Clear(&config);

return Py_RunMain();
```

The B1 experiment used the same flow, with one additional step:

```c
status = PyConfig_SetBytesString(
    &config,
    &config.home,
    home
);
```

The intended ordering was:

```text
PyConfig_InitPythonConfig
        ↓
PyConfig_SetBytesArgv
        ↓
optional config.home assignment
        ↓
Py_InitializeFromConfig
        ↓
PyConfig_Clear
        ↓
Py_RunMain
```

Stage 1-B intentionally did not configure:

```text
config.program_name
config.executable
config.module_search_paths
config.prefix
config.base_prefix
```

The purpose was to preserve the automatic path discovery already validated in Stage 1-A.

---

## 4. Build provenance

The Stage 1-B launchers were cross-compiled with the Android NDK toolchain:

```text
aarch64-linux-android24-clang
```

The development headers and `libpython3.14.so` were taken from:

```text
~/tmp/260703/android-python-work/prefix
```

A second candidate prefix was also checked:

```text
~/tmp/260703/cptmp/prefix
```

The following files were compared and found to be identical between the two prefixes:

```text
include/python3.14/pyconfig.h
lib/libpython3.14.so
```

The chosen Stage 1-B build inputs therefore had confirmed matching provenance.

The built launchers were:

```text
python-pyconfig-auto
python-pyconfig-home
```

Both were:

```text
ELF 64-bit
ARM aarch64
PIE executable
interpreter: /system/bin/linker64
```

Both contained:

```text
NEEDED:
  libpython3.14.so
  libdl.so
  libm.so
  liblog.so
  libc.so

RUNPATH:
  $ORIGIN/../lib
```

The launcher-level `$ORIGIN/../lib` RUNPATH was only used to locate `libpython3.14.so`.

It did not replace the Stage 1-A native-extension runtime contract.

---

## 5. Comparison variants

Three frontend variants were compared.

### Stage 1-A baseline

```text
binary:
  python

frontend:
  Py_BytesMain
```

### B0 / auto-discovery

```text
binary:
  python-pyconfig-auto

frontend:
  PyConfig

config.home:
  not set
```

### B1 / explicit home

```text
binary:
  python-pyconfig-home

frontend:
  PyConfig

config.home:
  set from CPYTHON_HOME
```

All variants were tested inside the same pristine runtime tree.

The comparison prefix was prepared from the original Stage 1-A tarball and then only the two Stage 1-B launcher binaries were added.

---

## 6. Broad functional comparison

The first Stage 1-B comparison covered:

```text
-V
-c
-m
script.py args

native stdlib imports
HTTPS

uv venv
venv identity
uv pip
package import
uv run
```

Final result:

```text
VARIANT_RESULT[stage1a]=PASS
VARIANT_RESULT[b0-auto]=PASS
VARIANT_RESULT[b1-home]=PASS
```

This established broad functional parity.

---

## 7. Base prefix discovery

Manual smoke tests showed that all three variants discovered the same runtime prefix.

### Stage 1-A

```text
executable:
  .../prefix/bin/python

prefix:
  .../prefix

base_prefix:
  .../prefix
```

### B0

```text
executable:
  .../prefix/bin/python-pyconfig-auto

prefix:
  .../prefix

base_prefix:
  .../prefix
```

### B1

```text
executable:
  .../prefix/bin/python-pyconfig-home

prefix:
  .../prefix

base_prefix:
  .../prefix
```

Therefore B0 preserved the successful automatic path discovery behavior already seen in Stage 1-A.

---

## 8. Semantic differential validation

After the broad comparison passed, a narrower semantic differential test was run.

The goal was to detect observable CLI or configuration differences between:

```text
Stage 1-A
B0
B1
```

The tested areas were:

```text
default mode
-I
-E
-S
-B
-X utf8

sys.argv
sys.orig_argv
sys.flags
sys._xoptions
sys.path

PYTHONPATH behavior

subprocess sys.executable round trip

SystemExit exit codes
invalid option handling
--help exit code

venv launcher linkage
pyvenv.cfg

B1 wrong-home negative control
```

No semantic regression was observed for B0 in the tested surface.

---

## 9. Command-line flag parity

The following options produced matching observable behavior across Stage 1-A, B0, and B1.

### `-I`

All variants reported:

```text
isolated = 1
ignore_environment = 1
no_user_site = 1
safe_path = true
```

The resulting `sys.path` also removed the empty current-directory entry.

### `-E`

All variants reported:

```text
ignore_environment = 1
```

### `-S`

All variants reported:

```text
no_site = 1
```

The `site-packages` path was absent from the resulting `sys.path`.

### `-B`

All variants reported:

```text
dont_write_bytecode = 1
```

### `-X utf8`

All variants reported:

```text
utf8_mode = 1
```

and:

```text
sys._xoptions["utf8"] = True
```

This provides strong evidence that B0 preserved the tested command-line configuration semantics.

---

## 10. `sys.orig_argv` behavior

All variants preserved full original command-line arguments in `sys.orig_argv`.

The only expected difference was the executable path.

Example:

```text
Stage 1-A:
  .../bin/python

B0:
  .../bin/python-pyconfig-auto

B1:
  .../bin/python-pyconfig-home
```

The remainder of the argument vector, including options and code payload, was preserved consistently.

This indicates that the `PyConfig_SetBytesArgv` path reproduced the expected argument-processing behavior for the tested modes.

---

## 11. PYTHONPATH behavior

A sentinel `PYTHONPATH` directory was injected.

All three variants included the sentinel path in `sys.path` in the same position.

Observed pattern:

```text
''
<sentinel PYTHONPATH directory>
<prefix>/lib/python314.zip
<prefix>/lib/python3.14
<prefix>/lib/python3.14/lib-dynload
<prefix>/lib/python3.14/site-packages
```

Therefore B0 did not introduce an observable PYTHONPATH handling difference in the tested configuration.

---

## 12. Subprocess round-trip behavior

Each frontend was tested by launching a child Python process through:

```python
subprocess.run(
    [sys.executable, ...]
)
```

Results:

### Stage 1-A

```text
parent:
  .../bin/python

child:
  .../bin/python
```

### B0

```text
parent:
  .../bin/python-pyconfig-auto

child:
  .../bin/python-pyconfig-auto
```

### B1

```text
parent:
  .../bin/python-pyconfig-home

child:
  .../bin/python-pyconfig-home
```

All child processes reported the correct base prefix.

Result:

```text
SUBPROCESS[stage1a]=PASS
SUBPROCESS[b0-auto]=PASS
SUBPROCESS[b1-home]=PASS
```

This is an important Stage 1-B result because future launcher work must preserve process re-entry through `sys.executable`.

---

## 13. Exit-code parity

All three variants produced the same tested exit codes.

```text
SystemExit(7)     -> 7
invalid option    -> 2
--help            -> 0
```

Results:

```text
                 Stage 1-A   B0   B1
SystemExit(7)         7       7    7
invalid option        2       2    2
--help                0       0    0
```

This confirms that the Stage 1-B PyStatus handling correctly preserved the tested CLI exit behavior.

---

## 14. uv venv linkage

uv created venv interpreter links that pointed to the selected frontend binary.

### Stage 1-A

```text
venv/bin/python
  ->
<prefix>/bin/python
```

### B0

```text
venv/bin/python
  ->
<prefix>/bin/python-pyconfig-auto
```

### B1

```text
venv/bin/python
  ->
<prefix>/bin/python-pyconfig-home
```

The generated `pyvenv.cfg` files were equivalent in structure:

```text
home = <prefix>/bin
implementation = CPython
uv = 0.11.26
version_info = 3.14.6
include-system-site-packages = false
```

Earlier functional comparison also verified:

```text
sys.prefix != sys.base_prefix
```

inside the created venvs.

Therefore all tested frontends preserved correct venv identity.

---

## 15. B1 negative control

The most important distinguishing experiment was the B1 wrong-home test.

B1 normally runs with:

```text
CPYTHON_HOME=<correct prefix>
```

and passes.

The negative control used:

```text
CPYTHON_HOME=<nonexistent path>
```

Result:

```text
B1_WRONG_HOME_RC=1
```

Error:

```text
Fatal Python error: Failed to import encodings module

ModuleNotFoundError:
No module named 'encodings'
```

This demonstrates that B1's `config.home` setting is not decorative.

It creates a real dependency on the correctness of the external home value.

Therefore B1 has this runtime contract:

```text
PyConfig frontend
+
correct CPYTHON_HOME
```

B0 does not have that dependency.

---

## 16. Final Stage 1-B decision

### Selected

```text
B0 / PyConfig auto-discovery frontend
```

Initialization model:

```text
PyConfig_InitPythonConfig
PyConfig_SetBytesArgv
Py_InitializeFromConfig
PyConfig_Clear
Py_RunMain
```

### Not selected

```text
B1 / explicit config.home frontend
```

### Reason

B1 was functional but introduced a meaningful external dependency:

```text
CPYTHON_HOME
```

A wrong value caused hard startup failure.

B0 passed the same broad functional and semantic validation without requiring that additional runtime input.

Therefore B0 is simpler and is the preferred next-stage foundation.

---

## 17. What Stage 1-B proved

Stage 1-B proved that, within the tested surface:

> A PyConfig-based frontend can replace the Stage 1-A `Py_BytesMain` frontend without observable regression in CLI execution modes, common command-line flags, path discovery, PYTHONPATH handling, subprocess re-entry, exit codes, native stdlib imports, HTTPS, uv venv creation, venv identity, uv pip workflows, and uv run workflows.

Stage 1-B also proved that:

> Explicitly forcing `config.home` is functional when correct, but introduces a real external dependency and is unnecessary for the current layout.

---

## 18. What Stage 1-B did not prove

Stage 1-B does not claim complete equivalence for every CPython behavior.

Not exhaustively tested:

```text
all command-line flags
all warning configurations
all audit-hook interactions
all subinterpreter behavior
all multiprocessing start modes
all signal edge cases
all debugger/profiler integrations
all embedding API combinations
all locale configurations
all pycache configurations
all import-system edge cases
```

Therefore the correct claim is:

> **B0 preserved the tested Stage 1-A behavior.**

Not:

> **B0 is proven identical to `Py_BytesMain` in all possible situations.**

---

## 19. Frozen Stage 1-B frontend

The selected Stage 1-B frontend is conceptually:

```c
#include <Python.h>

int
main(int argc, char **argv)
{
    PyConfig config;
    PyStatus status;

    PyConfig_InitPythonConfig(&config);

    status = PyConfig_SetBytesArgv(
        &config,
        argc,
        argv
    );

    if (PyStatus_Exception(status)) {
        goto exception;
    }

    status = Py_InitializeFromConfig(&config);

    if (PyStatus_Exception(status)) {
        goto exception;
    }

    PyConfig_Clear(&config);

    return Py_RunMain();

exception:
    PyConfig_Clear(&config);

    if (PyStatus_IsExit(status)) {
        return status.exitcode;
    }

    Py_ExitStatusException(status);
}
```

This is the preferred frontend foundation for the next stage.

---

## 20. Frozen runtime contract

Stage 1-B does not change the Stage 1-A runtime contract.

Required:

```text
LD_LIBRARY_PATH=<cpython-prefix>/lib
SSL_CERT_FILE=<termux-prefix>/etc/tls/cert.pem
```

Still not required:

```text
PYTHONHOME
PYTHONPATH
```

B0 also does not require:

```text
CPYTHON_HOME
```

The full Stage 1-B runtime model is therefore:

```text
B0 PyConfig frontend
        |
        v
automatic Python path discovery
        |
        +-- LD_LIBRARY_PATH=<prefix>/lib
        |
        +-- SSL_CERT_FILE=<termux-prefix>/etc/tls/cert.pem
        |
        v
uv explicit interpreter selection
```

---

## 21. Stage 1-A vs Stage 1-B

### Stage 1-A

Question:

> Can an upstream-built CPython Android runtime operate as a Termux CLI interpreter with uv?

Answer:

```text
Yes.
```

Frontend:

```text
Py_BytesMain
```

Runtime contract:

```text
LD_LIBRARY_PATH
SSL_CERT_FILE
```

### Stage 1-B

Question:

> Can an explicit PyConfig-based frontend preserve the validated Stage 1-A behavior?

Answer:

```text
Yes.
```

Selected frontend:

```text
B0 / PyConfig auto-discovery
```

Runtime contract:

```text
unchanged from Stage 1-A
```

---

## 22. Why B0 matters for Stage 2

The value of Stage 1-B is not that it solved a current failure.

Stage 1-A already worked.

The value is that B0 provides a structured initialization point where future Stage 2 behavior can be added deliberately.

Potential Stage 2 work may need to:

```text
discover executable location
derive prefix
prepare native library lookup
prepare trust-store integration
possibly configure selected PyConfig fields
preserve CLI semantics
preserve venv semantics
preserve subprocess re-entry
preserve uv behavior
```

B0 is a better experimental foundation for that work because initialization is explicit and observable.

However, Stage 2 must not assume PyConfig can solve every remaining problem.

Stage 1-A and Stage 1-B established that the remaining external contract contains at least two separate layers:

```text
native shared-library lookup
    LD_LIBRARY_PATH

CA trust integration
    SSL_CERT_FILE
```

PyConfig addresses Python runtime initialization.

It does not automatically solve Android native linker policy or Termux trust-store discovery.

Those remain separate Stage 2 design problems.

---

## 23. Stage 2 entry condition

Stage 2 should start from:

```text
B0 PyConfig frontend
+
LD_LIBRARY_PATH external
+
SSL_CERT_FILE external
```

The Stage 2 question is:

> How can the B0 frontend discover and establish the remaining runtime integration automatically, without breaking the validated CLI, venv, subprocess, and uv behavior?

The most important Stage 2 constraint is:

> Any mechanism that reduces the external runtime contract must preserve the Stage 1-B validation surface.

That includes:

```text
CLI modes
CLI flags
sys.orig_argv
sys.path
subprocess via sys.executable
exit codes
native stdlib
HTTPS
uv venv
venv identity
uv pip
uv run
```

---

## 24. Stage 1-B completion checklist

```text
[PASS] PyConfig launcher builds for Android arm64
[PASS] B0 base runtime works
[PASS] B1 base runtime works
[PASS] base prefix discovery matches Stage 1-A
[PASS] -V works
[PASS] -c works
[PASS] -m works
[PASS] script mode works
[PASS] -I behavior matches
[PASS] -E behavior matches
[PASS] -S behavior matches
[PASS] -B behavior matches
[PASS] -X utf8 behavior matches
[PASS] sys.orig_argv behavior matches
[PASS] sys._xoptions behavior matches
[PASS] PYTHONPATH behavior matches
[PASS] subprocess sys.executable round trip works
[PASS] exit codes match tested baseline
[PASS] native stdlib works
[PASS] HTTPS works
[PASS] uv venv works
[PASS] venv identity is correct
[PASS] uv pip works
[PASS] package import works
[PASS] uv run works
[PASS] B1 wrong-home negative control behaves as expected
[PASS] preferred frontend selected
```

Stage 1-B is complete.

---

## 25. Handoff summary

For a future developer or AI agent:

1. Stage 1-A is frozen.
2. Stage 1-B is frozen.
3. The selected Stage 1-B frontend is B0.
4. B0 uses PyConfig without setting `config.home`.
5. B1 remains a reference experiment only.
6. Do not add `CPYTHON_HOME` to the selected runtime contract.
7. Preserve the Stage 1-A runtime contract until Stage 2 deliberately changes it.
8. The remaining external contract is:

   ```text
   LD_LIBRARY_PATH=<cpython-prefix>/lib
   SSL_CERT_FILE=<termux-prefix>/etc/tls/cert.pem
   ```

9. Any Stage 2 change must be compared against the Stage 1-B semantic validation surface.
10. Do not conflate Python initialization, native library lookup, and CA trust integration.
11. Preserve subprocess re-entry through `sys.executable`.
12. Preserve uv-created venv identity.
13. Treat wrong-path negative tests as required evidence for future self-location logic.
14. Prefer measured behavior over assumptions about Android or CPython internals.

---

## 26. Final statement

Stage 1-B successfully demonstrated that:

> A PyConfig-based frontend can preserve the tested Stage 1-A behavior for CPython 3.14.6 on Android arm64 under Termux, including CLI execution modes, common command-line flags, Python path discovery, subprocess re-entry, exit codes, venv semantics, HTTPS, and uv workflows.

The selected next-stage foundation is:

> **B0 — PyConfig initialization with automatic Python path discovery and no forced `config.home`.**

This is now the frozen frontend baseline for Stage 2.
