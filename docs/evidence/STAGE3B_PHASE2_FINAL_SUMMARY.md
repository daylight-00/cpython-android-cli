# Stage 3-B Phase 2 Final Summary

> **Status:** FROZEN
> **Stage:** 3-B Phase 2
> **Result:** PASS — controlled Linux producer replay completed

## Result

The exact CPython source identity recovered in Phase 1 was replayed successfully on Victor Linux through the preserved Android producer model.

Final marker:

```text
STAGE3B_UPSTREAM_REPLAY=PASS
```

Producer identity:

```text
CPython source commit   c63aec69bd59c55314c06c23f4c22c03de76fe45
CPython version         3.14.6
target                  aarch64-linux-android
Android API             24
NDK                     27.3.13750724
driver Python           3.13.3
producer scripts        preserved snapshot match
```

## Successful command graph

The replay established that the minimal single-target producer graph is:

```text
Android/android.py build build
    -> configure and make native build Python

Android/android.py build aarch64-linux-android
    -> unpack declared dependency archives
    -> configure and make Android host Python
    -> install Android prefix

Android/android.py package aarch64-linux-android
    -> create release archive
```

Using `build all` was intentionally avoided because it would build every declared Android ABI rather than the selected target.

## Product evidence

Build result:

```text
build_returncode          0
package_returncode        0
expected_prefix_exists    true
package_archive_exists    true
```

Package:

```text
python-3.14.6-aarch64-linux-android.tar.gz
size     22,346,066 bytes
sha256   a16e0433b6f7e69c4634b52ce582d4d387447fbcfed797425f669ac224631f4f
```

Replay prefix inventory:

```text
files              8631
symlinks              46
ELF objects           88
total file bytes  288157138
```

Key products were present:

```text
include/python3.14/Python.h
include/python3.14/pyconfig.h
lib/libpython3.14.so
lib/libpython3.so
lib/python3.14/_sysconfigdata__android_aarch64-linux-android.py
```

## Harness findings

Two failed attempts were valid replay-harness findings, not evidence of a CPython source or Android toolchain failure.

### Finding 1: implicit driver Python

The initial invocation used the workstation system `python3`, which could not parse the producer script's `except*` syntax.

This exposed an unmodeled input:

```text
host-side producer driver Python >= 3.11
```

The harness now captures the resolved executable and version during preparation and verifies them during replay.

### Finding 2: implicit build-Python predecessor

The first corrected invocation called:

```text
Android/android.py build aarch64-linux-android
```

after starting with an empty cross-build directory.

The upstream implementation selects only the requested target in that form and therefore expected `cross-build/build/python` to exist already. The replay stopped before host configuration.

The harness now executes the build-Python target first and fails fast before entering the host step if it fails.

## Interpretation

Phase 2 proves:

> The recovered CPython source commit can be rebuilt on Victor Linux with the matched NDK, declared dependency release archives, preserved producer scripts, explicit driver Python, and an isolated command graph.

Phase 2 does not prove Stage 3-A runtime equivalence.

The replay prefix is larger than the frozen Stage 3-A runtime-shaped prefix:

```text
                         Stage 3-A     Phase 2 replay
files                         3280              8631
symlinks                         5                46
ELF objects                     81                88
```

This difference is not classified as failure here. The two trees currently represent different product boundaries: a complete upstream build/install prefix versus a previously assembled runtime-shaped prefix.

No file-count normalization, deletion, metadata rewriting, or runtime pruning is authorized by this result.

## Frozen conclusion

```text
STAGE3B_PHASE2=FROZEN
STAGE3B_PHASE3=READY
```

The next step is dependency product promotion: capture and promote immutable identities for the six dependency archives consumed by the successful replay before designing the CPython development/runtime product boundary.
