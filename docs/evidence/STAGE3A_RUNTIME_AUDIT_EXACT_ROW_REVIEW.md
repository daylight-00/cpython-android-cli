# Stage 3-A Runtime Audit Exact-Row Review

> **Status:** Selected evidence
> **Stage:** 3-A
> **Result:** Exact observed paths and special events classified; no new unknown boundary remains in this probe

## Purpose

This note closes the direct review of the exact rows produced by the representative Python audit-hook boundary probe.

The aggregate summary had observed:

```text
DEVFS            1 unique path
HOME_STATE       1 unique path
RESULT_OUTPUT    8 unique paths
RUNTIME_PREFIX  13 unique paths
TERMUX_TEMP      1 unique path
```

and five special events.

## DEVFS

Exact path:

```text
/dev/null
```

Interpretation:

> `/dev/null` is a normal device boundary used by subprocess machinery and is not a packaged runtime data dependency.

## HOME_STATE label review

Exact path:

```text
/data/data/com.termux/files/home/projects/cpython-android-cli/experiments/stage3a-runtime-closure
```

This is the repository experiment directory from which the probe script was executed.

It was classified as `HOME_STATE` only because the project repository itself is located under the Termux home directory.

Frozen interpretation:

> This observed path is probe-code location, not generic user-home runtime state.

Therefore the `HOME_STATE` aggregate label in this run should not be interpreted as evidence that the base runtime depends on arbitrary files under `$HOME`.

## RESULT_OUTPUT

The eight unique paths were generated under:

```text
results/termux/stage3a-runtime-closure/pycache-runtime-audit/...
```

They were `PYTHONPYCACHEPREFIX` destinations corresponding to stdlib modules imported during the probe, including:

```text
encodings/idna.py
importlib/resources/*.py
selectors.py
stringprep.py
subprocess.py
```

The paths were absent after the workload because the audit hook observed attempted cache-path activity while the probe intentionally redirected pycache state into the results tree.

Frozen interpretation:

> These are experiment-output paths created by the probe environment, not runtime product dependencies.

## RUNTIME_PREFIX

Observed paths were confined to expected runtime locations such as:

```text
lib/python3.14
lib/python3.14/*.py
lib/python3.14/importlib/resources
lib/python3.14/lib-dynload
lib/python3.14/site-packages
lib/python314.zip
```

`lib/python314.zip` was absent, but it appeared as an import-search candidate rather than a successful file dependency.

Frozen interpretation:

> The observed runtime-prefix paths are consistent with normal Python import and stdlib discovery behavior.

## TERMUX_TEMP

Exact observed path:

```text
/data/data/com.termux/files/usr/tmp/<random-name>
```

The path was absent after the workload.

Frozen interpretation:

> The representative `tempfile` workload selected Termux `$PREFIX/tmp` as its temporary-file boundary and cleaned the tested temporary path afterward.

This is host temporary-storage integration, not runtime-prefix content.

## Special events

Observed:

```text
ctypes.dlopen     'libc.so'
ctypes.dlopen     'libc.so'
socket.connect    <PyPI HTTPS endpoint>:443
subprocess.Popen  file -b <runtime-prefix>/bin/python3.14
subprocess.Popen  uname -p
```

### ctypes.dlopen

`libc.so` is consistent with the already-characterized Android system/native boundary.

No new SONAME appeared beyond the native closure work.

### socket.connect

The network event corresponds to the deliberate HTTPS PyPI workload.

It is a workload network boundary, not an unexpected filesystem dependency.

### `file` and `uname -p`

These subprocesses were induced by the explicit `platform.platform()` workload.

CPython 3.14's `platform` module uses:

```text
file -b <target>
```

for executable architecture/linkage identification and falls back to:

```text
uname -p
```

for processor identification when needed.

Frozen interpretation:

> `file` and `uname` are optional host-command dependencies of the tested `platform()` information path. They are not required for interpreter startup, import of the tested native extension surface, HTTPS, subprocess re-entry, uv venv creation, or uv run behavior already validated elsewhere.

## Closed boundary model for this probe

Exact-row review reduces the observed external classes to:

```text
/dev/null
    normal device boundary

project experiment directory
    probe-code location, not generic home-state dependency

$PREFIX/tmp
    temporary-storage integration

libc.so
    already-characterized Android native boundary

network :443
    deliberate HTTPS workload

file / uname
    optional platform-information helper commands
```

No exact row remains semantically unknown in this audit probe.

## Limitation

This remains a Python audit-hook observation pass, not a complete syscall trace or proof over all possible workloads.

The exact claim is:

> Every exact path and special event observed in the tested representative audit workload has now been classified, and no new unknown runtime dependency boundary remains in that observed set.

## Next step

Proceed to:

```text
1. production-shape Stage 2-C smoke reconfirmation;
2. production-shape whole-prefix relocation reconfirmation;
3. Stage 3-A freeze review.
```
