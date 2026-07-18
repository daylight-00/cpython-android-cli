# Epoch 2 Research: CPython 3.14/3.15 Across Android API Levels 24 and 29–36

> **Status:** independently source-verified research conclusion  
> **Verified:** 2026-07-18  
> **CPython baselines:** 3.14.6 and 3.15.0b3  
> **Purpose:** identify API-floor changes that can materially affect an Android/Bionic standalone CPython experiment  
> **Non-purpose:** select or freeze an Epoch 3 release policy

## 1. Decision summary

The current upstream-derived product remains correctly anchored to the API level selected by the official CPython Android producer. For the frozen 3.14.6 product in this repository, that level is API 24.

Raising the compile-time Android API floor does **not** produce a uniform or automatic performance improvement. The meaningful thresholds found by this source audit are narrower:

| API floor | CPython 3.14 | CPython 3.15 | Research conclusion |
|---:|---|---|---|
| 24 | Current upstream baseline | Valid compatibility baseline | Preserve as the upstream-faithful control |
| 29 | Native ELF TLS instead of compiler emutls | Same | Strongest candidate for a broad low-level runtime improvement |
| 30 | `sem_clockwait()` becomes available; optional RELR-era linker capability | Same | Primarily timed-lock correctness/robustness; possible packaging/startup effects if separately enabled and measured |
| 31 | `os.pidfd_open()` can be exposed when detected | `Popen.wait(timeout)` can use pidfd + poll | Meaningful targeted improvement for timed subprocess waits in 3.15 |
| 32 | No relevant Bionic addition identified | Same | No separate CPython threshold identified |
| 33 | Bionic gains `backtrace*`, but CPython's non-Apple C-stack path also requires `dladdr1()` | Same | No confirmed core performance threshold |
| 34 | `close_range()` and `copy_file_range()` become build-visible | Same | Meaningful targeted subprocess and file-copy threshold |
| 35 | New Bionic APIs are not consumed by identified core 3.14/3.15 paths | Same | No confirmed broad benefit |
| 36 | New Bionic APIs are not consumed by identified core 3.14/3.15 paths | Same | Appropriate experimental ceiling, not a proven optimization target |

The most useful Epoch 2 comparison is therefore not “24 versus every higher number.” It is:

1. the exact upstream API-24 artifact;
2. a minimally changed API-29 or API-34/36 CPython build;
3. optionally, an all-components API-36 build if the minimal experiment shows a reason to continue.

## 2. Interpretation rules

Three different version boundaries must not be conflated:

- **compile-time API floor / `minSdkVersion`**: controls which Bionic declarations and compiler code-generation choices are available;
- **runtime Android release**: controls which dynamic linker and libc implementation is actually present;
- **runtime Linux kernel**: controls whether syscall wrappers such as `pidfd_open`, `close_range`, and `copy_file_range` succeed.

A build compiled for API 24 can run on a newer device and benefit from runtime-only linker or libc improvements. Conversely, compiling for API 34 only makes an API visible at build time; a syscall wrapper can still return `ENOSYS` if the device kernel lacks the underlying syscall.

For this reason, all API experiments must record both the compiler target and the real device/kernel identity.

## 3. API 24: upstream compatibility baseline

### Verified facts

The frozen product record identifies the input as an `upstream-cpython-android-package`, CPython 3.14.6, Android API 24, NDK 27.3.13750724, targeting `aarch64-linux-android`.

The official Python 3.14 Android documentation describes the python.org Android package as an application-embedding input containing `libpython`, external shared libraries, and the standard library. Python 3.14 is also the first release series for which python.org provides official Android binary releases.

### Conclusion

API 24 is important because it is the **upstream-selected product floor**, not because API 24 is intrinsically the highest-performance target. The upstream artifact must remain the control product even when higher-floor experiments are performed.

## 4. API 29: native ELF TLS

### Verified facts

Android supports ELF TLS starting at API 29. Since NDK r26, Clang automatically emits ELF TLS for a minimum API level of 29 or higher; lower minimum API levels continue to use compiler emulated TLS, backed by `pthread_key_create()`.

CPython 3.14 defines `_Py_thread_local` as C/C++ language TLS (`thread_local`, `_Thread_local`, or `__thread`) when supported. This mechanism is used in core interpreter state paths, including thread-state access.

### Expected effect

ELF TLS permits direct native TLS access instead of the emutls helper and pthread-key path. This is the clearest API-floor change with the potential to affect frequently executed core interpreter operations rather than one isolated module.

This is still a hypothesis to benchmark. The source evidence establishes a different code-generation model, not a guaranteed end-to-end speedup for every Python workload.

### Conclusion

API 29 is the first high-value experimental threshold. If Epoch 2 performs only one performance-oriented intermediate-floor experiment, API 29 is more informative than arbitrary API 30–33 builds.

## 5. API 30: monotonic semaphore waits and linker-era changes

### Verified facts

Bionic adds `sem_clockwait()` and related clock-specific pthread wait functions at API 30.

When `HAVE_SEM_CLOCKWAIT` is available, CPython's pthread lock implementation uses `sem_clockwait(..., CLOCK_MONOTONIC, ...)` with an absolute monotonic deadline. Without it, CPython uses `sem_timedwait()` with wall-clock time and may need to recompute a deadline after interruption.

Android 11/API 30 is also the release boundary at which standardized RELR dynamic relocations are available. RELR use depends on linker flags and the produced ELF; CPython does not gain it merely because the API number changes.

### Expected effect

- timed lock waits become more robust against wall-clock changes;
- interrupted waits avoid some deadline recomputation;
- RELR can reduce relocation metadata and potentially improve size/load behavior only if deliberately enabled and verified.

These are not broad bytecode-execution optimizations.

### Conclusion

API 30 is a valid correctness and packaging research point, but it should not be maintained as a separate product profile unless measurement reveals a concrete advantage.

## 6. API 31: pidfd availability and Python 3.15 subprocess waits

### Verified facts

Bionic adds `pidfd_open()` and related pidfd wrappers at API 31.

Python has exposed `os.pidfd_open()` since earlier desktop releases when the function is detected. The version-specific change is in Python 3.15: `subprocess.Popen.wait(timeout=...)` first attempts an event-driven `pidfd_open()` plus `poll()` path on Linux 5.3 or newer, then falls back to the traditional `waitpid(WNOHANG)` sleep loop when unavailable or blocked.

Python 3.14 does not contain this new `Popen.wait(timeout)` behavior.

### Expected effect

For Python 3.15, API 31+ can avoid repeated polling and sleeps for timed subprocess waits, subject to kernel and security-policy support. This is relevant to process-heavy CLI tools but does not improve ordinary interpreter execution.

### Conclusion

API 31 is a real **Python 3.15-specific functional/performance threshold**. It should be included in the API-36 experiment's behavioral probes even if no separate API-31 artifact is retained.

## 7. API 32: no identified CPython threshold

The Bionic API change audit found no API-32 libc addition that creates a distinct CPython 3.14 or 3.15 code path relevant to this project.

### Conclusion

Do not create an API-32 profile merely because it is numerically between other levels.

## 8. API 33: C backtrace support is incomplete for CPython's path

### Verified facts

Bionic adds `backtrace`, `backtrace_symbols`, and `backtrace_symbols_fd` at API 33.

CPython's non-Apple C-stack implementation is enabled only when it has `execinfo.h`, `backtrace()`, and `dladdr1()`. Android provides `dladdr()` but does not provide the glibc-specific `dladdr1()` interface used by that CPython path.

### Conclusion

API 33 does not, by itself, enable CPython's full native C-stack dump path. No meaningful core performance threshold was identified. It may still be useful for custom diagnostics outside the upstream CPython path, but that would be project-owned adaptation and should require a separate experiment question.

## 9. API 34: `close_range()` and `copy_file_range()`

### Verified facts

Bionic adds `close_range()` and `copy_file_range()` at API 34.

CPython's `_posixsubprocess` implementation uses `close_range()` when configure detects it and falls back to enumerating or closing file descriptors when it is unavailable or fails. CPython also exposes `os.copy_file_range()` when detected.

### Expected effect

- `close_range()` can reduce child-process setup work, especially when many file descriptors must be closed;
- `copy_file_range()` can perform in-kernel file copying for callers that use `os.copy_file_range()`;
- both remain subject to kernel support and fallback behavior.

### Conclusion

API 34 is the strongest targeted threshold after API 29. It is especially relevant to CLI distributions because subprocess-heavy tools and environment managers are common workloads.

## 10. API 35 and API 36: no confirmed broad CPython benefit

### Verified facts

Bionic API 35 adds `_Fork`, `timespec_getres`, timezone-object APIs, `epoll_pwait2`, and other interfaces. API 36 adds `qsort_r`, `sig2str`/`str2sig`, `lchmod`, and `mseal`.

A source audit of the CPython 3.14.6 and 3.15.0b3 trees did not identify core paths that use these additions in a way that would create a broad runtime advantage for this product. Some functions may expand a small `os` surface if configure detects them, but that is different from a general interpreter optimization.

### Conclusion

API 36 is justified as an **experimental modern-floor profile**, because it allows one controlled build against the latest available platform surface and can reveal adaptation problems early. It is not currently justified as the main distribution policy or as a known performance build.

## 11. Python 3.14 versus 3.15

The Android API-floor findings mostly apply to both versions because they arise from Bionic and compiler capabilities. The major verified version-specific difference is Python 3.15's event-driven timed subprocess wait.

Python 3.15 is still a prerelease baseline in this research. Its findings must not be promoted into a stable product claim until the final 3.15 source and official Android artifacts are available and rechecked.

## 12. Epoch 2 experiment design

The recommended matrix is:

| Variant | CPython | Launcher | Dependencies | Purpose |
|---|---:|---:|---:|---|
| A: upstream control | upstream API 24 | upstream-matched API 24 | upstream prebuilt API 21/24 mixture | product-faithful reference |
| B: minimal modern floor | API 36 | API 36 | unchanged upstream dependency binaries | isolate CPython/launcher floor effects with minimal maintenance |
| C: all API 36 | API 36 | API 36 | all rebuilt at API 36 | determine whether dependency-floor unification adds measurable value |

Variant C should only follow Variant B if a concrete question remains. Every variant should run the same relocation, native closure, extension import, HTTPS, venv, pip, uv, subprocess, and file-copy probes.

Required measurements should include:

- source and patch delta from upstream;
- build success and warnings;
- ELF/API symbol closure;
- startup latency;
- TLS-sensitive microbenchmarks and representative Python workloads;
- `Popen.wait(timeout)` behavior on Python 3.15;
- high-file-descriptor subprocess setup;
- `os.copy_file_range()` availability and behavior;
- archive and installed size;
- kernel/Android/device identity;
- maintenance work required to repeat the build.

## 13. Final Epoch 2 conclusion

The main distribution policy should remain upstream-faithful. API 36 belongs in Epoch 2 as a bounded research profile whose purpose is to discover Android adaptation requirements and measure whether a modern floor is worth any continuing maintenance.

The present evidence does not support replacing the upstream API floor with API 36. It supports performing a controlled experiment and preserving the result for a later Epoch 3 design decision.

## References

### Android/Bionic

- [Android linker changes for NDK developers: ELF TLS available from API 29](https://android.googlesource.com/platform/bionic/+/HEAD/android-changes-for-ndk-developers.md#elf-tls-available-for-api-level-29)
- [Android ELF TLS design notes](https://android.googlesource.com/platform/bionic/+/HEAD/docs/elf-tls.md)
- [Bionic status: functions added by Android API level](https://android.googlesource.com/platform/bionic/+/HEAD/docs/status.md)
- [Android 10 features: NDK builds with minimum API 29 can use ELF TLS](https://developer.android.com/about/versions/10/features#elf-tls)

### CPython 3.14.6

- [CPython 3.14.6 `_Py_thread_local` selection](https://github.com/python/cpython/blob/v3.14.6/Include/pyport.h)
- [CPython 3.14.6 pthread timed-lock implementation](https://github.com/python/cpython/blob/v3.14.6/Python/thread_pthread.h)
- [CPython 3.14.6 `close_range()` subprocess path](https://github.com/python/cpython/blob/v3.14.6/Modules/_posixsubprocess.c)
- [CPython 3.14.6 POSIX APIs including `copy_file_range`](https://github.com/python/cpython/blob/v3.14.6/Modules/posixmodule.c)
- [CPython 3.14.6 C-stack implementation requirements](https://github.com/python/cpython/blob/v3.14.6/Python/traceback.c)
- [Python 3.14 Android usage and official package model](https://docs.python.org/3.14/using/android.html)
- [Python 3.14 build changes: official Android binary releases](https://docs.python.org/3.14/whatsnew/3.14.html#build-changes)

### CPython 3.15.0b3

- [Python 3.15 `Popen.wait(timeout)` change](https://docs.python.org/3.15/whatsnew/3.15.html#subprocess)
- [CPython 3.15.0b3 subprocess implementation](https://github.com/python/cpython/blob/v3.15.0b3/Lib/subprocess.py)

### This repository

- [Frozen CPython 3.14.6 product lock](../../config/products/cpython-3.14.6-aarch64-linux-android.lock.json)
- [Current Epoch 2 context](../CURRENT_CONTEXT.md)
