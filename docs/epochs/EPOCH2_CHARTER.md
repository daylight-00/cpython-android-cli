# Epoch 2 Charter: Upstream Android adaptation research

> **Status:** ACTIVE — recalibrated 2026-07-19
> **Predecessor:** Epoch 1 frozen through Stage 3-F
> **Decision authority:** ADR-0006

## Mission

Epoch 2 is the Android/Bionic research and evidence phase. Its purpose is to remove the technical uncertainty required to create an upstream-derived, Astral-structured clean release in Epoch 3.

It is not the final release repository and it is not the full Astral-like source producer.

## Primary upstream policy

```text
CPython provider       Python.org / CPython Android release process
dependency provider    BeeWare artifacts selected by CPython
primary control        exact official upstream package and API policy
local responsibility   standalone launcher, bounded adaptation,
                       archive transformation, metadata, and qualification
```

The upstream package and dependency topology are trusted as the default product input. Existing producer reconstruction remains evidence and an Epoch 4 precursor; it is not repeated by default for every patch release.

## Product target under study

```text
product             Android/Bionic standalone CPython
canonical target    aarch64-linux-android
Android ABI         arm64-v8a
control API floor   official upstream floor, currently API 24 for CPython
libc                 bionic
primary profile      Termux CLI
additional contexts adb shell, root shell, later APK consumers
```

Termux is the first full interactive qualification profile, not the binary ABI provider. The core must not require Termux native libraries or hard-coded Termux installation paths.

## Required research program

Epoch 2 must finish evidence for:

1. direct standalone adaptation of the official Python.org package;
2. one bounded upstream patch-update rehearsal;
3. a Python 3.15 delta preview;
4. the controlled API comparison:
   - exact official control;
   - CPython/launcher API 36 with upstream dependencies retained;
   - complete same-source API 36 rebuild including BeeWare dependencies;
5. minimum-floor runtime qualification distinct from modern-device qualification;
6. 16 KiB page-size compatibility;
7. native-extension SDK and wheel-tag behavior;
8. relocation, loader, certificate, timezone, temporary, and writable-state boundaries;
9. differential Termux/ADB/root behavior where access permits;
10. exact license, source, binary, and local-mutation provenance;
11. the consumer contract required by Epoch 3 and uv-facing integration.

API 29 remains an important attribution point for native ELF TLS. API 36 is a mandatory modern-floor experiment, not an automatic release-floor decision.

## Existing authority

Epoch 1 and E2-P0 through E2-P3 remain preserved evidence. The accepted S22 Ultra qualification proves one real API 36 Termux profile. It does not prove minimum API compatibility, emulator coverage, or dual-device acceptance.

The Note9 API 29 package remains optional deferred evidence. Its execution may strengthen cross-device compatibility but does not block the recalibrated research sequence.

## Explicit exclusions

Epoch 2 does not finalize:

- the clean public release repository;
- public catalog and release governance;
- the full CPython/dependency source producer;
- final static/shared linkage policy independent of upstream;
- PGO/LTO production profiles;
- broad APK integration;
- exhaustive device coverage;
- a production installer lifecycle.

## Closure

Epoch 2 closes when its evidence export is sufficient to initialize Epoch 3 without reopening fundamental Android adaptation questions. Closure requires explicit unresolved-risk accounting; it does not require the optional Note9 run or a false emulator claim.
