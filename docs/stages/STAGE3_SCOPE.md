# Stage 3 Scope: From Validated Runtime to Reproducible Distribution Product

> **Status:** ACTIVE
> **Start date:** 2026-07-10
> **Input:** Frozen Stage 2 architecture
> **Primary target:** Termux on Android arm64
> **Current Python baseline:** CPython 3.14.6
> **Current active sub-stage:** Stage 3-B

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

Stage 3 asks:

> How should this validated runtime become a reproducible, inspectable, relocatable distribution product without losing the behavior frozen in Stage 2?

Stage 3 is not primarily a launcher experiment.

The launcher remains a frozen input unless new evidence requires reopening Stage 2.

The Stage 3 problem surface is:

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

## 2. Stage decomposition

```text
Stage 3-A
  Runtime closure census and boundary model
  FROZEN

Stage 3-B
  Reproducible build-input promotion
  ACTIVE

Stage 3-C
  Distribution archive and installation contract
  DEFERRED

Stage 3-D
  Consumer integration and optional managed-Python research
  DEFERRED
```

Authoritative sub-stage documents:

```text
docs/stages/STAGE3A_FINAL.md
docs/stages/STAGE3B_SCOPE.md
```

## 3. Why Stage 3 began with closure

A tarball is not a distribution contract by itself.

Before defining archive names or installer commands, the project needed to know:

```text
which files are required at runtime
which native dependencies are internal
which dependencies are Android-provided
which host integrations remain external
which paths relocate correctly
which metadata remains build-host-specific
which runtime data sources are absent or external
```

Stage 3-A answered those questions for the tested target before packaging work began.

## 4. Stage 3-A frozen result

Stage 3-A is frozen.

Input runtime:

```text
work/termux/stage2c/runtime/prefix
```

The stage performed:

```text
complete file inventory
symlink inventory
ELF object inventory
DT_NEEDED edge inventory
provider classification
Android SONAME loadability probes
extension import sweep
sysconfig path census and classification
timezone-data boundary probes
CA trust boundary probes
representative runtime audit
canonical smoke reconfirmation
production-shape relocation reconfirmation
```

### 4.1 Runtime inventory

Observed:

```text
file entries             3280
symlinks                    5
ELF objects                 81
DT_NEEDED edges            329
inspection errors            0
mutation check            PASS
```

### 4.2 Native closure

Observed:

```text
9 unique needed SONAMEs
  4 RUNTIME_INTERNAL
  5 ANDROID_SYSTEM

RUNTIME_INTERNAL edges    80
ANDROID_SYSTEM edges     249
TERMUX native edges        0
UNRESOLVED edges            0
```

The five unique Android-system SONAMEs passed fresh-process loadability probes on the tested target.

### 4.3 Extension surface

Observed:

```text
67 extension candidates
67 isolated imports PASS
0 import FAIL
```

### 4.4 Runtime paths and build metadata

Stage 3-A established:

```text
active runtime paths
  relocation-aware

build/development metadata
  partially stale
```

Concrete residue included:

```text
/usr/local build-prefix paths
upstream build-workspace paths
macOS NDK toolchain paths
host build-tool paths
```

The missing absolute-path set was classified completely with:

```text
UNKNOWN=0
```

### 4.5 Non-ELF boundaries

CA trust:

```text
Termux host CA integration confirmed
unset path repair PASS
missing path repair PASS
explicit Termux CA PASS
existing unusable regular file preserved -> HTTPS FAIL
```

Frozen semantic clarification:

```text
launcher performs path-level CA repair
launcher does not validate trust-store contents
```

Timezone data:

```text
base runtime source absent
first-party tzdata package fallback PASS
```

Temporary storage:

```text
Termux $PREFIX/tmp observed
```

Representative audit:

```text
all exact observed rows classified
no new unknown broad boundary in observed set
```

### 4.6 Final reconfirmation

Observed:

```text
STAGE2C_SMOKE=PASS

LOCATION_RECONFIRM[A]=PASS
LOCATION_RECONFIRM[B]=PASS
STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS
STAGE3A_PRODUCTION_RELOCATION_RECONFIRM=PASS
```

Stage 3-A acceptance result:

```text
STAGE3A=FROZEN
```

See:

```text
docs/stages/STAGE3A_FINAL.md
docs/evidence/STAGE3A_FINAL_RECONFIRMATION_SUMMARY.md
```

## 5. Stage 3-B: reproducible build-input promotion

Stage 3-B is active.

Question:

> Can the current launcher development input and Android runtime prefix be regenerated from declared source, toolchain, dependency, and command inputs instead of being consumed from historical experiment paths?

The current development input is:

```text
experiments/bootstrap-android-build/android-python-work/prefix
```

This is accepted provenance for frozen Stage 2 and Stage 3-A, but it is not the desired final build-product boundary.

Stage 3-B must establish at minimum:

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

Desired conceptual pipeline:

```text
source inputs
    -> declared

toolchain inputs
    -> declared

native dependency sources
    -> reproducible dependency products

CPython Android build
    -> reproducible Android prefix

launcher build
    -> reproducible production launcher

runtime assembly
    -> Stage 3-A-equivalent runtime closure
```

Stage 3-B must not begin by mass-rewriting sysconfig metadata.

It must reconstruct and replay the producer model first.

See:

```text
docs/stages/STAGE3B_SCOPE.md
```

## 6. Stage 3-C: distribution archive and installation contract

Stage 3-C is deferred until Stage 3-B establishes reproducible producer inputs.

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

A likely distinction remains:

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
  development metadata
  optional link information
```

Stage 3-A strengthened the evidence for this distinction because runtime execution paths were relocation-aware while development metadata remained partially stale.

Required later validation should include:

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

## 7. Stage 3-D: consumer integration

Stage 3-D remains deferred.

Questions may include:

```text
Can uv discover the installed interpreter naturally as a system Python?
What naming and install layout improve discovery?
Should an installer expose python3.14/python3/python links?
What metadata would be required for managed-Python-style integration?
Can an Android distribution be represented without misleading Linux target assumptions?
```

Explicit interpreter selection remains a valid frozen integration model:

```text
uv ... --python /absolute/path/to/python
```

The project must not imitate uv-managed distribution metadata before the runtime artifact and producer model are stable.

## 8. Frozen Stage 2 and Stage 3-A invariants

Future work must preserve or intentionally reopen:

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
Stage 3-A native closure constraints
Stage 3-A non-ELF boundary understanding
Stage 3-A production relocation result
```

A Stage 3 optimization that breaks one of these is not automatically progress.

## 9. Current first action

The next implementation task is Stage 3-B Phase 1:

> Reconstruct the current producer chain as data before attempting a clean rebuild.

The first experiment should inventory:

```text
CPython source identity
SDK/NDK identity
API level
host build Python
third-party native dependency sources and products
configure/build commands
launcher development inputs
current hidden historical path dependencies
```

Only after that map exists should the project attempt a clean replay.
