# Epoch 2 Charter: Android/Bionic Standalone CPython

> **Status:** ACTIVE — Phase 0 documentation foundation
> **Predecessor:** Epoch 1 frozen through Stage 3-F

## Motivation

The practical objective is not Android application embedding. It is running Python-distributed command-line software through `pip`, virtual environments, and uv on Android. Termux is the primary real user environment because it provides the mainstream Bionic-native interactive shell and package ecosystem without replacing Android with a glibc root filesystem.

Epoch 1 proved the runtime, lifecycle, transition, consumer, managed-root, publication, and acquisition pieces. Epoch 2 makes the standalone runtime artifact the primary lower-level product and makes the installer an explicit consumer of that artifact.

## Product identity

```text
product             Android/Bionic standalone CPython
canonical target    aarch64-linux-android
Android ABI         arm64-v8a
minimum API         24 initially
libc                 bionic
primary profile      termux-cli
primary workloads    pip, venv, uv run, uv tool, Python CLI packages
```

`aarch64-linux-android` is the compiler and platform target. `arm64-v8a` is the Android ABI. `bionic` is the libc/runtime family. `termux-cli` is an execution profile, not a separate ELF ABI.

## Termux-first, not Termux-bound

Termux-first means that interactive CLI behavior, CA discovery, terminal integration, writable home and temporary storage, and uv workflows are qualified on Termux first.

Termux-bound would mean the core runtime requires `/data/data/com.termux/...`, the `com.termux` package identity, or Termux package native libraries. That is not the target architecture. Termux-specific adaptation must remain a profile around a relocatable Android/Bionic core.

## Product topology

```text
standalone producer
  source, toolchain, dependencies, launcher, runtime assembly,
  archive flavors, metadata, checksums, licenses, qualification
        |
        v
canonical standalone release
        |
        v
installer / lifecycle manager
  acquisition, cache, transaction, registry, install, uninstall,
  version transition, Termux exposure, uv discovery integration
        |
        v
pip / venv / uv / Python CLI users
```

## Repository topology

The current repository is the Epoch 2 incubator and remains the complete engineering and evidence authority. Standalone and installer responsibilities are first separated logically behind an artifact-only boundary. The standalone component is promoted to a separate product repository only after its archive contract, metadata, independent build, qualification, and release workflow are stable.

Promotion must preserve relevant Git history. Copying files into a history-free release repository is not the default plan.

## Non-goals for the initial epoch

- redesigning the frozen launcher without a dedicated authority decision;
- treating Android application embedding as the primary user product;
- emulating a generic glibc Linux distribution;
- making Termux package paths part of the platform target identity;
- moving implementation files before component ownership and artifact contracts are accepted;
- claiming public releases or upstream uv support from documentation alone.

## Success criteria

Epoch 2 succeeds when:

1. one canonical standalone archive and metadata contract exists;
2. the standalone product can be built, packaged, and qualified independently;
3. the installer consumes only released archive, metadata, checksum, and installation policy inputs;
4. producer build trees and source checkouts are not installer dependencies;
5. prerelease assets can be generated reproducibly and validated on Android/Termux;
6. the standalone component can be promoted into a focused product repository with preserved history;
7. uv managed-Python integration can be pursued against that stable product contract.

## Governing rule

```text
logical boundary -> artifact contract -> independent verification
-> implementation migration -> release automation -> repository promotion
```

Repository movement follows product authority. Product authority does not follow directory movement.
