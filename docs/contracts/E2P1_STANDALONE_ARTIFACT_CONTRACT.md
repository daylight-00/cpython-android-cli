# E2-P1 Canonical Standalone Artifact Contract

> **Status:** FROZEN — repository contract and deterministic fixture verification complete
> **Contract version:** 1
> **Primary flavor:** `install_only_stripped`
> **Predecessor:** Epoch 1 frozen through Stage 3-F

## Purpose

E2-P1 defines the machine boundary between the standalone producer and every downstream consumer. It does not refactor the producer or installer. It freezes what a future producer must emit and what an installer may trust after verification.

The exact product authority is not a workspace or an installed prefix. It is:

```text
immutable archive bytes
+ versioned artifact metadata
+ exact path manifest
+ provenance
+ qualification result
+ license inventory
+ SHA256SUMS
+ release index body digest
```

## Canonical identity

```text
artifact id        cpython-<version>-aarch64-linux-android<api>-<flavor>
target triple      aarch64-linux-android
Android ABI        arm64-v8a
minimum API        24 initially
libc               bionic
wheel platform     android_24_arm64_v8a
primary profile    termux-cli
```

The target triple, Android ABI, libc, API floor, wheel tag, and execution profile are separate fields. `termux-cli` is not an ELF ABI. A uv catalog key such as `cpython-3.14.6-linux-aarch64-none` is a consumer mapping and never canonical product identity.

## Primary archive

The first required artifact flavor is:

```text
install_only_stripped
```

Its archive contract is:

```text
filename       <artifact-id>.tar.zst
format         POSIX pax tar compressed with zstd
single root    python/
install root   python/
entry point    python/bin/python3.14
payload        runtime + development
excluded       tests + build workspace + external debug symbols
direct use     extraction followed by python/bin/python3.14
```

Runtime and development payloads are combined because the primary workload includes pip and uv tooling, including source builds that require headers and development metadata. Tests, producer build objects, and detached symbols are separate future artifacts.

The names `install_only`, `full`, and `symbols` remain reserved. Their exact layouts are not frozen by E2-P1.

## Archive serialization

A conforming producer must emit deterministic tar members:

```text
member order       lexicographic POSIX path
mtime              0
uid/gid            0/0
uname/gname        empty
hardlinks          forbidden
special entries    forbidden
symlinks           relative and non-escaping
PAX headers        path/linkpath only when required
```

The exact zstd implementation, version, level, thread count, and frame-checksum policy are recorded in provenance. Compatibility does not depend on a compression level, but byte reproducibility for one producer authority does.

## Metadata sidecars

Each archive has five same-prefix JSON sidecars:

```text
<artifact-id>.artifact.json
<artifact-id>.manifest.json
<artifact-id>.provenance.json
<artifact-id>.qualification.json
<artifact-id>.licenses.json
```

A release also contains:

```text
SHA256SUMS
release-index.json
```

All JSON uses UTF-8, LF, sorted keys, two-space indentation, and one trailing newline. Schema version `1` is fail-closed. Unknown versions are rejected. Future optional data belongs under a namespaced `extensions` object rather than unversioned top-level fields.

## Artifact metadata

`artifact.json` carries:

- Python implementation, version, Python/ABI tags, SOABI, and multiarch;
- Android target triple, ABI, API floor, Bionic identity, wheel tag, and sysconfig platform;
- archive filename, size, SHA-256, flavor, build options, and payload classes;
- direct-extraction layout and whole-prefix relocation model;
- qualified execution profiles and whether Termux is part of binary identity;
- consumer mappings that are explicitly non-canonical.

The core artifact must not encode `/data/data/com.termux`, `/data/user/0/com.termux`, the `com.termux` package identity, or Termux package libraries as required binary identity.

## Payload manifest and ownership

`manifest.json` lists every archive member with exact POSIX path, type, mode, and payload class. Regular files also carry size and SHA-256; symlinks carry a relative, non-escaping target.

Installer ownership remains compatible with the frozen Epoch 1 lifecycle model:

```text
ownership unit              exact manifest path
unowned descendants         preserve
owned directory removal     only when empty
installer repacking         forbidden
```

The installer verifies archive and sidecars before extraction, extracts into staging, and passes the verified manifest to its transaction engine. It must not regenerate, reorder, strip, or repackage the artifact.

## Provenance

`provenance.json` identifies:

- exact CPython version, tag, and source commit;
- NDK version, target compiler, and Android API;
- repository commit/tree and build options;
- archive serialization tools and parameters;
- frozen Epoch 1 predecessor identities.

A real release may add dependency source identities, build workflow identity, reproducibility comparisons, and attestations under versioned fields or `extensions`.

## Qualification and selectability

`qualification.json` separates static, emulator, and real Termux checks. A release row is selectable only when:

```text
qualification status       passed
qualification selectable   true
release product selectable true
release selectable         true
all referenced bytes       present and hash-exact
```

API level and ABI matching are necessary but not sufficient. Native closure, relocation, extension imports, HTTPS, venv, pip, uv workflows, wheel tags, and product fidelity are qualified in E2-P3.

The E2-P1 fixture is deliberately `not-qualified` and unselectable. Its tiny archive verifies serialization and metadata linkage only and is not Python.

## License inventory

`licenses.json` maps every distributed component to license identity, archive path, size, and SHA-256. A stable or prerelease product must mark the inventory complete for the published payload. E2-P1's fixture uses a placeholder and remains incomplete and unselectable.

## Release index

`release-index.json` is the release-envelope authority. It contains exact archive and sidecar file references and a SHA-256 over the canonical `release` body. `SHA256SUMS` lists the archive and sidecars, but excludes itself and `release-index.json` to avoid a checksum cycle.

Publication endpoints and GitHub release URLs are mutable locators, not product identity. Stage 3-F's fail-closed acquisition and content-addressed cache model remains the predecessor for future implementation.

## Compatibility and evolution

A version-1 consumer must reject:

- unknown schema versions;
- missing or hash-mismatched sidecars;
- unsafe archive paths, hardlinks, special files, or escaping symlinks;
- target, ABI, API, libc, archive-root, or flavor mismatches;
- selectable releases without passed qualification;
- Termux absolute paths used as canonical binary identity.

New fields require a schema revision unless carried under `extensions`. A breaking change requires a new contract version and explicit installer support.

## External standards and references

- Android NDK ABI names: https://developer.android.com/ndk/guides/abis
- Android wheel platform tags: https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/#android
- CPython Android distribution model: https://docs.python.org/3.14/using/android.html
- Standalone distribution reference model: https://github.com/astral-sh/python-build-standalone/blob/main/docs/distributions.rst

## Claim boundary

E2-P1 proves a repository-level contract, schemas, deterministic fixture archive, metadata linkage, negative-fixture regression behavior, and a bounded installer input model.

It does not prove a real standalone CPython build, zstd reproducibility across tool versions, Android execution, Termux behavior, release publication, installer conversion, GitHub Actions, or upstream uv integration.
