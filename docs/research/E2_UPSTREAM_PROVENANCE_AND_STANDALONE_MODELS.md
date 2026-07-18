# Epoch 2 Research: Upstream Provenance and Standalone Models

> **Status:** independently source-verified research conclusion  
> **Verified:** 2026-07-18  
> **Scope:** CPython/Python.org, BeeWare Android dependency artifacts, this repository, Astral `python-build-standalone`, and uv

## 1. Conclusion

This project has an official Android runtime upstream:

```text
CPython/Python.org Android package
  -> built with BeeWare-produced Android dependency archives
  -> consumed by this project
  -> adapted into a relocatable command-line product
```

The future main distribution should preserve that chain. This project should normally own the standalone launcher, relocation, packaging, qualification, and consumer integration, while delegating CPython, dependency, toolchain, and API-floor policy to upstream.

Astral has a different responsibility boundary. `python-build-standalone` builds CPython and its dependencies from source and is itself the standalone binary upstream used by uv. Astral is therefore the best reference for distribution shape and consumer experience, but it is not an Android binary upstream for this project.

## 2. The official CPython Android package

Python 3.14 provides official Android binary releases. The official Android documentation describes the package as an embedding input with a top-level `prefix`. The prefix includes:

- shared `libpython`;
- the standard library;
- native extension modules;
- external native libraries, including OpenSSL-related libraries.

The package is **embedding-oriented**, but it is not dependency-free or interpreter-only. Embedding describes the expected host application and launch path.

The frozen product record in this repository identifies the source product as:

| Field | Value |
|---|---|
| Product kind | `upstream-cpython-android-package` |
| Python | 3.14.6 |
| Target | `aarch64-linux-android` |
| Android API | 24 |
| NDK | 27.3.13750724 |
| Archive | `python-3.14.6-aarch64-linux-android.tar.gz` |
| SHA-256 | `517f4b0d113c4c1cf6931c230b6b517bee7a2b7f8b4f0f099a148260fa3ac8e7` |

### Confirmed conclusion

The official package is the correct control input for the future main product. The missing layer is a directly executable, relocatable standalone contract, not a replacement CPython producer.

## 3. BeeWare dependency production

The CPython Android producer obtains prebuilt dependency archives from BeeWare's `cpython-android-source-deps` releases.

“Prebuilt” means that CPython consumes already compiled Android prefixes. BeeWare creates those prefixes from source:

```text
dependency source release
  -> BeeWare build recipe and Android patches
  -> Android NDK compilation
  -> installed prefix archive
  -> CPython Android build input
```

For example, the BeeWare OpenSSL recipe downloads OpenSSL source, applies its Android-specific patches, configures an Android build, and installs the compiled result. The zstd recipe follows the same source-to-binary-producer model.

The common BeeWare Android build environment defaults to API 21. The zstd recipe explicitly selects API 24 because zstd entered CPython in Python 3.14, whose Android minimum is API 24, and because its 32-bit build requires APIs available at that level.

The exact dependency products frozen by this repository are:

| Dependency | Version/revision | API policy |
|---|---|---:|
| bzip2 | 1.0.8-3 | common API 21 |
| libffi | 3.4.4-3 | common API 21 |
| OpenSSL | 3.5.7-0 | common API 21 |
| SQLite | 3.50.4-0 | common API 21 |
| xz | 5.4.6-1 | common API 21 |
| zstd | 1.5.7-2 | explicit API 24 |

CPython and the project launcher use API 24, so the complete product floor is API 24.

### Confirmed conclusion

The mixed API-21/API-24 dependency set is an upstream production result, not a local project decision. This project should inherit it for its upstream-faithful product.

## 4. Decision authority

| Decision | Practical authority |
|---|---|
| CPython Android package and minimum floor | CPython project/Python.org |
| Dependency source recipes, patches, and default floor | BeeWare |
| zstd API-24 override | BeeWare recipe aligned with CPython 3.14 |
| Final official package composition | CPython project |
| Standalone CLI behavior and qualification | This project |

A precise statement is:

> The CPython project is the final authority for the official Android package. It adopts dependency products whose detailed Android build policies are maintained by BeeWare. This project inherits that upstream combination.

## 5. Product consumption versus producer reconstruction

This repository has explored two related paths:

1. consuming and adapting the completed official Android package;
2. reconstructing the producer inputs and build path to understand provenance, reproducibility, and fallback feasibility.

Both were useful research. They do not have to become the same release policy.

### Confirmed conclusion

The future main release path should consume the official package. Source reconstruction should remain experimental evidence and a fallback capability, not a mandatory step for every release.

## 6. Astral `python-build-standalone`

Astral's technical notes describe a producer that builds a controlled toolchain, builds dependencies such as OpenSSL and SQLite, builds CPython, controls extension linking, and emits redistributable archives.

Astral owns decisions that this Android project can normally delegate:

- compiler and toolchain construction;
- dependency versions and source builds;
- CPython patches and upgrade adaptation;
- static/shared linking policy;
- PGO/LTO profiles;
- distribution metadata and archive variants.

Astral's canonical archive is rooted at `python/` and includes machine-readable `PYTHON.json`. It also produces install-only archives for direct consumers.

### Confirmed conclusion

Astral is a downstream CPython source builder and an upstream standalone binary producer. Its maintenance burden is evidence for why this project should avoid taking ownership of upstream Android build policy unless an experiment proves that doing so is necessary.

## 7. uv's upstream

uv's official documentation states that general-purpose official distributable CPython binaries are not available for its supported desktop matrix, so uv uses Astral `python-build-standalone` distributions for managed CPython installations.

```text
CPython and dependency source projects
  -> Astral python-build-standalone
  -> uv managed Python catalog and installation
```

For uv, Astral is the binary upstream. For Astral, CPython and each dependency project are source upstreams.

## 8. Comparison

| Responsibility | Astral | Recommended Android main path |
|---|---|---|
| CPython build | owned | delegated to official CPython Android producer |
| Dependency builds | owned | delegated to BeeWare/CPython chain |
| Toolchain and API floor | owned | inherited from upstream |
| Standalone executable | produced | added by this project |
| Relocation | produced and qualified | project-owned Android adaptation |
| Archive and metadata | producer-owned | project-owned, informed by Astral |
| uv integration | consumed by uv | future integration target |

### Confirmed conclusion

This project can deliver an Astral-like distribution while being much thinner than Astral's producer.

## 9. Main and experimental policies

### Main upstream-faithful path

- consume the official CPython Android package;
- verify its identity and digest;
- preserve upstream runtime and dependency choices;
- apply only the minimum standalone adaptation;
- qualify relocation, native closure, HTTPS, venv, pip, subprocess, and uv workflows;
- record the exact project-owned delta.

The current API 24 floor is an upstream result, not a permanent project identity.

### API-36 Epoch 2 experiment

Epoch 2 may separately test:

1. CPython and launcher rebuilt at API 36 while retaining upstream dependency binaries;
2. all native components rebuilt at API 36 using upstream sources and BeeWare recipes.

The second variant should only continue if the first leaves a concrete unanswered question.

## 10. Delegation policy

The main product should delegate:

- CPython Android patches and module policy;
- minimum API and NDK selection;
- dependency versions, patches, and recipes;
- upstream security maintenance.

This project should own:

- the relocatable CLI launcher;
- Android/Termux runtime adaptation;
- standalone archive and consumer metadata;
- native and behavioral qualification;
- uv discovery or managed-Python mapping;
- provenance for the small local delta.

## 11. Final Epoch 2 conclusion

The project's strongest property is the existence of a recognized upstream production chain. The main product should be an **upstream-derived standalone adaptation**.

Astral defines the reference product form. CPython/Python.org and BeeWare define the Android runtime production policy. API 36 remains a bounded research profile so that modern Android behavior can be studied without transferring permanent producer ownership to this project.

## References

### CPython/Python.org

- [Python 3.14: Using Python on Android](https://docs.python.org/3.14/using/android.html)
- [Python 3.14 build changes](https://docs.python.org/3.14/whatsnew/3.14.html#build-changes)
- [CPython Android producer and dependency acquisition](https://github.com/python/cpython/blob/main/Platforms/Android/__main__.py)

### BeeWare

- [Common Android build environment](https://github.com/beeware/cpython-android-source-deps/blob/main/android-env.sh)
- [zstd recipe and API-24 override](https://github.com/beeware/cpython-android-source-deps/blob/main/zstd/build.sh)
- [OpenSSL source-build recipe](https://github.com/beeware/cpython-android-source-deps/blob/main/openssl/build.sh)
- [Dependency release archives](https://github.com/beeware/cpython-android-source-deps/releases)

### Astral and uv

- [Astral technical notes](https://github.com/astral-sh/python-build-standalone/blob/main/docs/technotes.rst)
- [Astral distribution archives](https://github.com/astral-sh/python-build-standalone/blob/main/docs/distributions.rst)
- [uv managed Python distribution model](https://docs.astral.sh/uv/concepts/python-versions/)

### This repository

- [Frozen CPython 3.14.6 product lock](../../config/products/cpython-3.14.6-aarch64-linux-android.lock.json)
- [Frozen dependency archive lock](../../config/dependencies/android-source-deps-aarch64-linux-android.lock.json)
- [Epoch 2 charter](../epochs/EPOCH2_CHARTER.md)
