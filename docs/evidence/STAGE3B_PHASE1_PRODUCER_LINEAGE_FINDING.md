# Stage 3-B Phase 1 Producer Lineage Finding

> **Status:** Selected interim evidence
> **Stage:** 3-B Phase 1
> **Evidence basis:** current development-prefix `_sysconfigdata`, preserved Android producer snapshot, dependency release-tag census

## Finding

The current launcher development prefix carries build metadata from a macOS producer environment, not from the current Victor Linux workstation build context.

Observed build metadata includes:

```text
BUILD_GNU_TYPE=aarch64-apple-darwin24.6.0

CC=/Users/runner/Library/Android/sdk/ndk/27.3.13750724/
   toolchains/llvm/prebuilt/darwin-x86_64/bin/
   aarch64-linux-android24-clang

AR=/Users/runner/Library/Android/sdk/ndk/27.3.13750724/
   toolchains/llvm/prebuilt/darwin-x86_64/bin/llvm-ar

build workspace:
  /Users/runner/work/release-tools/release-tools/cross-build/...
```

Frozen interim interpretation:

> The currently consumed development prefix was produced in a macOS build environment and later consumed on Victor. It is not a prefix freshly produced by the current Linux launcher-build workstation state.

The exact workflow run, source commit, and artifact transfer chain are not yet proven.

## Structural alignment with the preserved Android producer snapshot

The current prefix `CONFIG_ARGS` contains:

```text
--host=aarch64-linux-android
--with-build-python=<cross-build>/build/python.exe
--without-ensurepip
--enable-shared
--without-static-libpython
--with-openssl=<cross-build>/aarch64-linux-android/prefix
```

The preserved `android.py` producer snapshot constructs the same host-configuration structure:

```text
--host=<host>
--build=<build GNU type>
--with-build-python=<cross-build>/build/python(.exe)
--without-ensurepip
--enable-shared
--without-static-libpython
--with-openssl=<target prefix>
```

The current prefix also records environment-derived inputs matching the preserved `android-env.sh` model:

```text
CC=<NDK clang driver with API suffix>
CFLAGS=-D__BIONIC_NO_PAGE_SIZE_MACRO -I<target-prefix>/include
LDFLAGS=
  -Wl,--build-id=sha1
  -Wl,--no-rosegment
  -Wl,-z,max-page-size=16384
  -Wl,--no-undefined
  -lm
  -L<target-prefix>/lib

PKG_CONFIG=pkg-config --define-prefix
PKG_CONFIG_LIBDIR=<target-prefix>/lib/pkgconfig
```

Interim conclusion:

> The embedded `CONFIG_ARGS` and compiler/linker flags are structurally consistent with the preserved Android producer script and environment model.

This establishes a strong producer-model match, but not yet an exact historical invocation transcript.

## Dependency provenance alignment

The dependency release-tag census recovered exactly six entries from the preserved producer snapshot:

```text
bzip2   1.0.8   recipe revision 3
libffi  3.4.4   recipe revision 3
openssl 3.5.7   recipe revision 0
sqlite  3.50.4  recipe revision 0
xz      5.4.6   recipe revision 1
zstd    1.5.7   recipe revision 2
```

Target archive form:

```text
<release-tag>-aarch64-linux-android.tar.gz
```

Source release base:

```text
https://github.com/beeware/cpython-android-source-deps/releases/download
```

Interim conclusion:

> The preserved Android producer snapshot fully identifies the dependency release tags expected by its build graph.

What remains unproven is whether the exact bytes currently present in the development prefix came from those exact release archives. That requires archive/hash or produced-file equivalence evidence, not only matching producer declarations.

## Metadata residue interpretation

The Stage 3-A sysconfig residue now has a clearer provenance explanation.

Examples:

```text
/usr/local
  configure-time default install prefix metadata

/Users/runner/work/release-tools/...
  producer workspace residue

/Users/runner/Library/Android/sdk/ndk/27.3.13750724/...
  producer toolchain residue
```

These paths are evidence of the producer environment.

They should not be mass-rewritten before the producer replay is understood.

## What is proven

```text
current dev prefix contains macOS producer metadata
NDK version recorded in prefix metadata is 27.3.13750724
target compiler driver is aarch64-linux-android24-clang
target host is aarch64-linux-android
preserved producer script structure matches current CONFIG_ARGS structure
preserved producer snapshot declares six dependency release tags
Stage 3-A runtime execution remained relocation-aware despite stale producer metadata
```

## What is not yet proven

```text
exact CPython source commit used by the current prefix
exact release-tools repository commit
exact workflow run or job identity
exact historical shell command transcript
exact hashes of downloaded dependency archives
byte equivalence between current prefix dependency files and declared source-deps archives
byte equivalence between the current runtime archive and any upstream release artifact
whether a Linux replay is byte-reproducible
whether a Linux replay is behaviorally/closure equivalent despite metadata differences
```

## Stage 3-B consequence

The next objective is not to reproduce the macOS path strings.

The next objective is:

> Replay the same declared producer graph on the Linux workstation, then compare runtime closure, extension surface, active runtime paths, and behavior against the frozen Stage 3-A constraints.

Expected producer-host differences such as:

```text
BUILD_GNU_TYPE
absolute build workspace paths
NDK prebuilt host path
host build-Python path
```

must be treated as expected metadata deltas unless they change the produced runtime closure or behavior.

The exact source identity and active toolchain identity still need to be closed before Phase 2 build replay begins.
