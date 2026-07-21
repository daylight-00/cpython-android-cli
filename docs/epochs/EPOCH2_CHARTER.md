# Epoch 2 Charter: Upstream Android adaptation research

> **Status:** CLOSED — producer-independent evidence export frozen 2026-07-21
> **Predecessor:** Epoch 1 frozen through Stage 3-F
> **Decision authorities:** ADR-0006 and ADR-0007
> **Detailed plan:** [`EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md`](../roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md)

## Mission

Epoch 2 is the Android/Bionic research and evidence phase. Its purpose is to remove the technical uncertainty required to create an upstream-derived, Astral-structured clean release in Epoch 3.

It is not the final release repository and it is not the full Astral-like source producer.

Epoch 2 proves feasibility and boundaries. It does not automatically select the Epoch 3 feature set.

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

## Evidence and selection boundary

Every material experiment receives one Epoch 2 evidence disposition:

```text
pass
bounded-pass
fail
unavailable
```

A passing experiment proves feasibility only within its stated boundary.

Epoch 3 separately assigns one product disposition to every selectable item:

```text
adopt
adopt-with-redesign
exclude
defer-to-epoch4
```

External pip may pass in Epoch 2 and still be excluded from the Epoch 3 base product. The same rule applies to bundled CA or timezone data, multiprocessing, SDK modes, command wrappers, optional artifact flavors, uv integration details, and API-36-derived inputs.

## Required research program

Epoch 2 must finish evidence for:

1. direct standalone adaptation of the official Python.org package;
2. truthful Astral-compatible full, install-only, stripped, and `PYTHON.json` semantics;
3. replacement of project-required `LD_LIBRARY_PATH` and loader-bootstrap self re-execution with accepted relative native lookup;
4. the stock `getpath`, symlink, launcher, and relocation boundary;
5. portable sysconfig and a real Android native-extension wheel;
6. CA, timezone, writable-state, and host-neutrality policies;
7. complete subprocess, venv, pip, uv, and multiprocessing capability inputs;
8. minimum-floor runtime qualification distinct from modern-device qualification;
9. 16 KiB page-size compatibility;
10. one bounded upstream patch-update rehearsal;
11. a Python 3.15 delta preview;
12. the controlled API comparison:
    - exact official control;
    - same-source CPython/launcher API 36 with official dependencies retained;
    - complete same-source and same-recipe API 36 rebuild including BeeWare dependencies;
13. differential Termux/ADB/root behavior where access permits;
14. exact license, source, binary, and local-mutation provenance;
15. the producer-independent evidence export and selection inputs required by Epoch 3.

API 29 remains an important attribution point for native ELF TLS. API 36 is mandatory Epoch 2 research because the project uses the same upstream-published sources, patches, and recipes while changing the compile API as the controlled variable. It is not an automatic Epoch 3 release-floor or producer decision.

## Existing authority

Epoch 1 and E2-P0 through E2-P3 remain preserved evidence. The accepted S22 Ultra qualification proves one real API 36 Termux profile. It does not prove minimum API compatibility, emulator coverage, or dual-device acceptance.

The Note9 API 29 package remains optional deferred evidence. Its execution may strengthen cross-device compatibility but does not block the recalibrated research sequence.

## Explicit exclusions

Epoch 2 does not finalize:

- the clean public release repository;
- public catalog and release governance;
- the Epoch 3 feature-selection register;
- the full CPython/dependency source producer;
- final static/shared linkage policy independent of upstream;
- PGO/LTO production profiles;
- broad APK integration;
- exhaustive device coverage;
- a production installer lifecycle.

## Closure

Epoch 2 closes when E2-G1 through E2-G8 in the detailed plan are resolved and a content-addressed, producer-independent evidence export is sufficient to initialize Epoch 3 without reopening fundamental Android adaptation questions.

Closure requires explicit unresolved-risk accounting and selection inputs. It does not require the optional Note9 run, a false emulator claim, or adoption of every experimentally successful feature.
