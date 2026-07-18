# E2-P3 Archive-Only Qualification Contract

> **Status:** Gate 1 design and harness frozen — Harness correction v1 frozen; target retry next
> **Contract version:** 1
> **Input:** frozen unqualified E2-P1 envelope from E2-P2

## Purpose

E2-P3 qualifies the exact frozen archive as a runnable Android/Bionic standalone product. It consumes the private E2-P2 envelope authority without rerunning the producer, materializer, façade build, or package operation.

The stable entry point is:

```text
components/standalone/bin/cpython-android-qualify
```

## Frozen input

```text
artifact id       cpython-3.14.6-aarch64-linux-android24-install_only_stripped
archive SHA-256   66c2a39b7164701d3a14cff538be298abcf30c696150f6abf7785e212c1b4727
release index     64825d3afabbda7c90992debfb11e771baeff5514f2b6e6d13584dc7ac6fcf85
private index     5fd8c03b53bcb749cfa221277e75f16b2392e6cec3a184b716f98e24d84fe0b5
manifest entries  1169
ELF objects       81
```

All acquisition, extraction, and runtime probes are read-only with respect to the frozen authority. Work happens in isolated disposable directories.

## Profiles

```text
static            host-independent authority, envelope, safety, and fidelity checks
termux-real       archive-only execution on a real Android/Termux device
termux-emulator   archive-only execution in Termux on an Android emulator
```

The two target profiles have the same exact 35-check matrix. Their host evidence differs: one must prove a real device and the other an emulator.

## Required target classes

The target matrix covers:

```text
authority and envelope identity
safe extraction and exact manifest fidelity
direct launcher execution at two unrelated locations
runtime, subprocess, SOABI, multiarch, sysconfig, and wheel-tag identity
81-object ELF inventory and exact 329-edge native closure
5/5 Android-system SONAME loadability
67/67 extension imports
HTTPS with default trust discovery
venv relocation
pip installation of a generated offline wheel
uv explicit-interpreter venv, install, and run workflows
before/after product fidelity and input immutability
```

No test package, producer tree, installed-prefix registry, or installer is used.

## Evidence and independent verification

Each profile writes canonical JSON evidence and one `qualification-result.json`. The independent result verifier requires the exact profile check set, exact evidence references, exact frozen input identities, coherent pass accounting, and `selectable=false`.

Individual profile results never make the product selectable. E2-P3 combined acceptance requires both target profiles to pass and be frozen. A later metadata-finalization gate must then create and independently verify an updated qualification sidecar and release index.

## Harness correction v1

The first `termux-real` execution produced 33/35 with all runtime, relocation, closure, extension, HTTPS, pip, uv, and product-fidelity classes otherwise passing. Two harness-only false negatives were corrected without changing the contract matrix or product:

- `venv_relocation` compares the reported venv executable and prefix lexically, because `venv/bin/python` is normally a symlink to the base interpreter. Resolved equality remains required for `base_prefix`.
- `wheel_tag_android24` obtains compatible tags from pip's vendored packaging in the newly created venv. The base `install_only_stripped` runtime remains intentionally pip-free.

The correction authorizes a retry only. It is not target qualification evidence.

## Claim boundary

Gate 1 freezes only the qualification contract, command, implementation, independent verifier, and regression behavior. It does not claim Android target execution, combined qualification, metadata finalization, selectability, publication, installer conversion, or transition behavior.
