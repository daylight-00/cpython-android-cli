# Stage 3-B Phase 1: Current Producer Provenance Reconstruction

> **Status:** ACTIVE
> **Parent scope:** `docs/stages/STAGE3B_SCOPE.md`
> **Input:** frozen Stage 3-A runtime closure and the current historical development prefix

## Question

> Which exact source, toolchain, dependency, generated metadata, command path, and historical build evidence can be recovered from the current producer state before attempting a clean replay?

## Principle

```text
observe current producer state
    -> classify evidence strength
    -> record unknowns explicitly
    -> only then attempt clean replay
```

This phase must not silently convert an available producer path into a claim about the exact historical command that produced the current prefix.

The probe distinguishes:

```text
OBSERVED_CURRENT
  directly read from current files, binaries, generated metadata, or tool probes

SNAPSHOT_PRODUCER
  build path exposed by the preserved Android producer tooling

HISTORICAL_HINT
  path or variable preserved in legacy project configuration

NOT_YET_PROVEN
  exact historical fact not established by the available evidence
```

## Preserved producer evidence already visible in the repository

The preserved Android snapshot exposes the upstream-style producer flow:

```text
configure-build
make-build
configure-host HOST
make-host HOST
```

and the one-shot equivalent:

```text
build HOST
```

The snapshot also declares the Android native dependency release tags used by its producer script and the NDK version selected by `android-env.sh`.

The current launcher workflow separately consumes:

```text
ANDROID_CC
CPYTHON_DEV_PREFIX/include/python3.14/Python.h
CPYTHON_DEV_PREFIX/include/python3.14/pyconfig.h
CPYTHON_DEV_PREFIX/lib/libpython3.14.so
```

Phase 1 records these producer and consumer boundaries without yet changing them.

## Run

Run on the Linux workstation, where `.local/env` defines the current compiler and development prefix:

```sh
git pull --ff-only

bash \
  experiments/stage3b-build-input-provenance/probe-current-provenance.sh
```

Optional explicit source identity:

```sh
CPYTHON_SRC=/path/to/cpython-source \
  bash experiments/stage3b-build-input-provenance/probe-current-provenance.sh
```

Optional runtime archive identity:

```sh
CPYTHON_RUNTIME_ARCHIVE=/path/to/runtime.tar.gz \
  bash experiments/stage3b-build-input-provenance/probe-current-provenance.sh
```

## Output root

```text
results/workstation/stage3b-build-input-provenance/
```

## Outputs

### `current-build-inputs.json`

Records:

```text
project Git identity
project defaults
target identity
current Android snapshot path
current development-prefix path
candidate CPython source path and Git identity
optional runtime archive identity
compiler path identity
selected sysconfig build-time variables
hashes of key producer and consumer artifacts
count of recoverable historical build-evidence files
```

The selected `_sysconfigdata` values include, when present:

```text
CONFIG_ARGS
AR
CC
CXX
CFLAGS
LDFLAGS
CONFIGURE_CFLAGS
CONFIGURE_LDFLAGS
PYTHON_FOR_BUILD
PYTHON_FOR_FREEZE
BUILD_GNU_TYPE
HOST_GNU_TYPE
prefix
exec_prefix
LIBDIR
INCLUDEPY
DESTSHARED
TZPATH
SOABI
EXT_SUFFIX
MULTIARCH
```

### `current-toolchain-identity.json`

Records:

```text
compiler path
compiler version output
compiler dumpmachine output
compiler SHA-256
NDK version derived from compiler path
NDK version declared by preserved android-env.sh
toolchain prebuilt host identity
host OS and architecture
host Python identity
make/pkg-config/curl/java/git probes
```

A mismatch between the NDK version derived from the active compiler path and the preserved snapshot declaration is evidence to investigate, not something the probe repairs.

### `current-dependency-provenance.tsv`

Parses the preserved Android producer script and records:

```text
name
version
recipe revision
release tag
source release base URL
expected target archive name
source script path
```

### `current-build-command-map.md`

Records:

```text
preserved Android producer command path
CONFIG_ARGS recovered from current sysconfigdata
current launcher compile/link command block
current Termux runtime assembly operations
remaining exact-command provenance gap
```

### `current-build-evidence-files.tsv`

Inventories recoverable files such as:

```text
config.log
config.status
Makefile
pybuilddir.txt
Setup.local
*.log
```

under the historical bootstrap experiment tree, with size and SHA-256.

### `provenance-summary.json`

Provides the first compact result summary.

## First interpretation rule

A successful probe run does not mean Stage 3-B is complete.

The first questions after the run are:

```text
Was a CPython source Git identity recovered?
Does the active compiler NDK version match the preserved snapshot declaration?
How many dependency release tags were recovered?
Was current sysconfigdata found?
What CONFIG_ARGS and toolchain paths does it retain?
Which config logs or Makefiles still exist?
Which parts of the historical producer chain remain NOT_YET_PROVEN?
```

Only after those questions are answered should Phase 2 attempt an upstream Android build replay.
