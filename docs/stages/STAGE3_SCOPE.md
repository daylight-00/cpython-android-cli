# Stage 3 Scope: From Validated Runtime to Reproducible Distribution Product

> **Status:** ACTIVE SCOPING
> **Start date:** 2026-07-10
> **Input:** Frozen Stage 2 architecture
> **Primary target:** Termux on Android arm64
> **Current Python baseline:** CPython 3.14.6

## 1. Stage 3 question

Stage 2 proved that the selected runtime architecture works:

```text
B0 PyConfig auto-discovery
        +
R2 conditional self re-exec
        +
Termux CA integration
        +
canonical build / transport / assembly workflow
```

Stage 3 asks a different question:

> How should this validated runtime become a reproducible, inspectable, relocatable distribution product without losing the behavior frozen in Stage 2?

Stage 3 is not primarily a launcher experiment.

The launcher is now a frozen input unless new evidence requires reopening Stage 2.

The new problem surface is:

```text
runtime closure
build reproducibility
dependency provenance
distribution layout
machine-readable metadata
license material
archive reproducibility
installation semantics
relocation validation
consumer integration
```

## 2. Why Stage 3 must begin with closure, not packaging

A tarball is not a distribution contract by itself.

Before defining archive names or installer commands, the project must know:

```text
which files are required at runtime
which files are build-only
which ELF objects depend on which SONAMEs
which dependencies are provided by Android
which dependencies are shipped in the runtime prefix
which host integrations remain external
which paths are relocatable
which metadata downstream consumers need
```

Therefore the first Stage 3 experiment is a runtime closure census.

## 3. Upstream reference model

Stage 3 should learn from four upstream/reference layers without copying any one project wholesale.

### 3.1 CPython Android

CPython's Android build flow already distinguishes:

```text
source tree
build Python
host Android Python
prefix
package output
```

Stage 3 should remain compatible with this provenance model rather than inventing a second CPython build system before measuring what the upstream build already provides.

### 3.2 uv

uv already supports explicit interpreter-path selection and treats external Python installations as system Python installations.

Therefore Stage 3 does not need uv-managed downloads as its first deliverable.

Managed-Python integration is a later consumer/distribution question.

### 3.3 python-build-standalone

Relevant architectural ideas:

```text
separate build artifacts from install-only artifacts
publish machine-readable distribution metadata
record target identity
record Python identity
record Python paths
record link mode
record extension-module loading capability
record licenses
separate full development artifacts from runtime-oriented archives
```

These are reference ideas, not a requirement to reproduce the exact project format.

### 3.4 BeeWare Android source dependencies

The BeeWare source-dependency project demonstrates a useful separation:

```text
CPython source
        !=
third-party native dependency build products
```

Stage 3 should make dependency versions and provenance explicit instead of treating the current prefix as an opaque directory.

## 4. Stage 3 decomposition

Stage 3 is split into four sub-stages.

```text
Stage 3-A
  Runtime closure census and manifest

Stage 3-B
  Reproducible build-input promotion

Stage 3-C
  Distribution archive and installation contract

Stage 3-D
  Consumer integration and optional managed-Python research
```

Only Stage 3-A is active now.

---

## 5. Stage 3-A: runtime closure census

### 5.1 Question

> What exactly is the runtime closure of the frozen Stage 2 interpreter, and which dependencies are internal, Android-provided, Termux-provided, or otherwise external?

### 5.2 Starting point

Input runtime:

```text
pristine CPython Android runtime prefix
        +
frozen Stage 2 launcher
```

Current assembly path:

```text
work/termux/stage2c/runtime/prefix
```

Stage 3-A must inspect the runtime as data.

### 5.3 Required inventories

#### File inventory

For every entry under the runtime prefix, record:

```text
relative path
file type
mode
size
SHA-256 for regular files
symlink target for symlinks
```

#### ELF inventory

For every ELF object, record:

```text
relative path
ELF class
machine
object type
program interpreter, if present
SONAME, if present
NEEDED entries
RPATH, if present
RUNPATH, if present
build ID, if present
```

#### Python identity inventory

Record at minimum:

```text
sys.version
sys.version_info
sys.implementation
sys.platform
sys.executable
sys.prefix
sys.base_prefix
sys.path
sysconfig.get_platform()
sysconfig.get_paths()
sysconfig.get_config_vars() selected stable subset
importlib.machinery.EXTENSION_SUFFIXES
SOABI
EXT_SUFFIX
MULTIARCH if present
```

#### Native module inventory

For extension modules under the stdlib and dynamic-load directories, record:

```text
module-relative file path
ELF NEEDED closure
resolved internal dependency candidates
unresolved dependency names
```

#### External-boundary inventory

Classify each dependency edge into one of:

```text
RUNTIME_INTERNAL
  resolved inside the distributed prefix

ANDROID_SYSTEM
  expected from Android/bionic system runtime

TERMUX_HOST_INTEGRATION
  currently consumed from Termux host environment

UNRESOLVED
  no accepted provider identified

BUILD_ONLY
  not required by the runtime artifact
```

This classification must be evidence-based and reviewable.

### 5.4 Stage 3-A outputs

Canonical outputs should be generated under:

```text
results/termux/stage3a-runtime-closure/
```

Selected evidence promoted to Git should live under:

```text
docs/evidence/
```

The first machine-readable outputs should include:

```text
files.tsv
elf-objects.tsv
elf-needed.tsv
symlinks.tsv
python-runtime.json
closure-classification.tsv
unresolved.tsv
```

The exact schema may evolve during Stage 3-A, but the raw observations must not be hidden inside prose-only documents.

### 5.5 Acceptance conditions

Stage 3-A is complete only when:

```text
[ ] every runtime-prefix path is inventoried
[ ] every ELF object is inventoried
[ ] every DT_NEEDED edge is represented
[ ] internal dependency resolution is explicit
[ ] Android-system dependencies are explicitly classified
[ ] Termux-host integration dependencies are explicitly classified
[ ] unresolved edges are either zero or intentionally documented
[ ] Python runtime identity is captured
[ ] Stage 2-C smoke still passes on the inventoried prefix
[ ] whole-prefix relocation is rechecked after inventory tooling is introduced
```

Stage 3-A does not yet require a final release tarball.

---

## 6. Stage 3-B: reproducible build-input promotion

Stage 3-B is deferred until Stage 3-A reveals the actual closure.

Question:

> Can the current development prefix and runtime prefix be regenerated from declared source, toolchain, and dependency inputs instead of being consumed from historical experiment paths?

The current development input is:

```text
experiments/bootstrap-android-build/android-python-work/prefix
```

This is accepted for frozen Stage 2 provenance, but it is not the desired final build-product boundary.

Stage 3-B should establish:

```text
CPython source identity
CPython tag/commit identity
Android SDK identity
Android NDK identity
API level
host build Python identity
third-party dependency names
third-party dependency versions
third-party dependency source identities
build command sequence
build options
output prefix identity
hashes of promoted build products
```

A likely conceptual split is:

```text
source inputs
    -> declared

toolchain inputs
    -> declared

native dependency build products
    -> declared and versioned

CPython Android host prefix
    -> reproducibly generated

launcher
    -> reproducibly generated against that prefix
```

Stage 3-B must not silently depend on `pristine-test` copies or old date-based directories.

---

## 7. Stage 3-C: distribution contract

Stage 3-C is responsible for turning a known closure into an installable artifact.

Question:

> What archive layout and metadata contract allow downstream users or tools to inspect, install, verify, and relocate the runtime without project-specific knowledge?

Candidate concepts:

```text
archive root
runtime install tree
machine-readable manifest
build/provenance metadata
license directory
checksums
optional debug/development material
```

A probable distinction is:

```text
runtime archive
  interpreter
  stdlib
  extension modules
  internal native libraries
  launcher
  runtime manifest
  licenses

full/development archive
  runtime archive contents
  headers
  libpython development files
  build metadata
  optional link information
```

Stage 3-C should decide this only after Stage 3-A and 3-B evidence exists.

Required tests should include:

```text
extract at A -> smoke PASS
move whole extracted runtime A -> B -> smoke PASS
fresh uv venv at A -> PASS
fresh uv venv at B -> PASS
uv run at A -> PASS
uv run at B -> PASS
archive checksum verification -> PASS
manifest/file inventory agreement -> PASS
```

---

## 8. Stage 3-D: consumer integration

Stage 3-D is intentionally last.

Questions may include:

```text
Can uv discover the installed interpreter naturally as a system Python?
What naming and install layout improve discovery?
Should a project-local installer expose python3.14/python3/python links?
What metadata would be required for managed-Python-style integration?
Can an Android distribution be represented without misleading Linux target assumptions?
```

The project must not begin by imitating uv-managed distribution metadata before the runtime artifact itself has a stable closure and distribution contract.

Explicit `--python /path/to/python` remains a valid frozen integration model.

---

## 9. Frozen Stage 2 invariants

Stage 3 may add build and distribution mechanisms, but it must preserve or intentionally reopen these frozen invariants:

```text
B0 PyConfig auto-discovery
R2 conditional self re-exec
clean top-level reexec -> direct behavior
ready-process direct entry
child redundant re-exec avoidance
self-location through actual executable path
exact-component loader-path normalization
separate CA repair from loader repair
venv sys.prefix / sys.base_prefix identity
uv explicit interpreter workflow
whole-prefix relocation behavior
canonical out/<target>/<profile>/ build artifact path
```

A Stage 3 optimization that breaks one of these is not automatically progress.

---

## 10. Non-goals for Stage 3-A

Do not add during Stage 3-A:

```text
new launcher bootstrap strategies
static CPython conversion
mass patchelf rewriting
custom Android linker internals
uv managed-Python download integration
multi-ABI matrix
PGO/LTO optimization work
release signing
SBOM generation
binary-size optimization
third-party wheel ecosystem redesign
```

Those may become later questions after the closure is understood.

## 11. First concrete action

The next implementation task is:

> Build a read-only Stage 3-A inventory harness that records the complete runtime file tree, symlink map, ELF metadata, DT_NEEDED dependency edges, Python runtime identity, and initial dependency classifications without modifying the runtime prefix.

The harness should operate against the already-validated assembled runtime first.

The first experiment directory should be:

```text
experiments/stage3a-runtime-closure/
```

The first result directory should be:

```text
results/termux/stage3a-runtime-closure/
```

The first Stage 3 implementation must be observational, not mutating.
