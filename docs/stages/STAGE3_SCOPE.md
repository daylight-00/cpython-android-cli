# Stage 3 Scope: From Validated Runtime to Reproducible Distribution Product

> **Status:** ACTIVE
> **Start date:** 2026-07-10
> **Input:** frozen Stage 2 architecture
> **Primary target:** Termux on Android arm64
> **Current Python baseline:** CPython 3.14.6
> **Current active sub-stage:** Stage 3-C contract design

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

Stage 3 is not primarily a launcher experiment. The launcher remains a frozen input unless new evidence requires reopening Stage 2.

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
  FROZEN

Stage 3-C
  Distribution archive and installation contract
  ACTIVE — contract design

Stage 3-D
  Consumer integration and optional managed-Python research
  DEFERRED
```

Authoritative sub-stage documents:

```text
docs/stages/STAGE3A_FINAL.md
docs/stages/STAGE3B_FINAL.md
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

## 4. Frozen Stage 3-A result

Input runtime:

```text
work/termux/stage2c/runtime/prefix
```

Observed:

```text
file entries             3280
symlinks                    5
ELF objects                 81
DT_NEEDED edges            329
RUNTIME_INTERNAL edges      80
ANDROID_SYSTEM edges       249
UNRESOLVED edges              0
inspection errors             0
```

Extension surface:

```text
67 extension candidates
67 isolated imports PASS
0 import FAIL
```

Boundary model:

```text
Termux host CA integration confirmed
base timezone source absent on tested host
first-party tzdata fallback PASS
Termux $PREFIX/tmp observed
```

Final markers:

```text
STAGE2C_SMOKE=PASS
LOCATION_RECONFIRM[A]=PASS
LOCATION_RECONFIRM[B]=PASS
STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS
STAGE3A_PRODUCTION_RELOCATION_RECONFIRM=PASS
STAGE3A=FROZEN
```

See:

```text
docs/stages/STAGE3A_FINAL.md
docs/evidence/STAGE3A_FINAL_RECONFIRMATION_SUMMARY.md
```

## 5. Frozen Stage 3-B result

Stage 3-B reconstructed and replayed the producer model, promoted explicit dependency and CPython products, assembled the promoted runtime on Termux, and validated it against the frozen target model.

Frozen phases:

```text
Phase 1  producer provenance reconstruction          FROZEN
Phase 2  controlled Linux producer replay            FROZEN
Phase 3  dependency product promotion                FROZEN
Phase 4  CPython dev/runtime product promotion        FROZEN
Phase 5  target runtime and closure equivalence       FROZEN
```

Promoted runtime:

```text
work/termux/stage3b-promoted-runtime/prefix
```

Producer boundary made explicit:

```text
CPython source/tag/commit identity
Android SDK/NDK/API/target identity
host build Python and tools
third-party dependency versions, recipes, archives and hashes
configure/build command model
promoted dependency products
promoted CPython development/runtime products
promoted launcher input/output
transport and isolated Termux assembly
```

Target-equivalence results:

```text
STAGE3B_PROMOTED_SMOKE=PASS
STAGE3B_PROMOTED_CLOSURE=PASS
STAGE3B_PROMOTED_BOUNDARIES=PASS
STAGE3B_PROMOTED_RELOCATION=PASS
STAGE3B_PHASE5=FROZEN
STAGE3B=FROZEN
```

Promoted closure:

```text
candidate entries                         3155
ELF objects                                 81
DT_NEEDED edges                            329
unresolved edges                             0
Android-system SONAME dlopen               5/5
extension imports                         67/67
machine verifier checks                  37/37
```

Promoted boundary equivalence:

```text
CA contract equivalence                    PASS
corrected direct-zoneinfo equivalence      PASS
uv tzdata 2026.3 fallback equivalence      PASS
machine verifier checks                  28/28
```

Production-shape relocation:

```text
LOCATION_RECONFIRM[A]=PASS
LOCATION_RECONFIRM[B]=PASS
STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS
RELOCATED_RUNTIME_PORTABLE_FIDELITY_CHECK=PASS
CANDIDATE_RUNTIME_MUTATION_CHECK=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
machine verifier checks                  31/31
```

Relocated-product fidelity:

```text
source entries               3155
relocated entries            3155
added paths                     0
removed paths                   0
portable changed paths          0
pycache paths                    0
portable fidelity             PASS
strict fidelity               PASS
```

See:

```text
docs/stages/STAGE3B_FINAL.md
docs/evidence/STAGE3B_PHASE5_FINAL_SUMMARY.md
```

## 6. Frozen invariants entering Stage 3-C

Stage 3-C must preserve or intentionally reopen with new evidence:

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
zero unresolved native edges
67/67 tested extension surface
explicit CA and timezone-data boundary model
candidate/control non-mutation
relocated-product path/content/symlink fidelity
```

A packaging optimization that breaks one of these is not automatically progress.

## 7. Stage 3-C question

> What archive layout and installation contract allow downstream users or tools to inspect, verify, install, upgrade, uninstall, and relocate the runtime without project-specific knowledge?

Stage 3-C is now unblocked because Stage 3-B established explicit producer and product inputs.

The first task is contract design, not immediate tar creation.

## 8. Stage 3-C initial design surface

### 8.1 Payload boundary

Decide whether the distribution model uses:

```text
one runtime archive
or
separate runtime and development archives
```

Candidate runtime payload:

```text
interpreter launcher
stdlib
extension modules
runtime-internal native libraries
runtime metadata
licenses
```

Candidate development payload:

```text
headers
libpython development files
sysconfig development metadata
link information
optional debug material
```

### 8.2 Installation ownership

Define:

```text
install root
owned path set
collision policy
upgrade replacement policy
uninstall behavior
partial-failure rollback
```

### 8.3 Machine-readable metadata

Define at minimum:

```text
schema version
runtime version
source/toolchain/dependency provenance
ABI/API/target identity
archive payload inventory
file hashes
symlink targets
license references
runtime/development role classification
```

### 8.4 Reproducibility definition

Choose whether reproducibility means:

```text
byte-identical archive
or
manifest-identical payload with normalized archive metadata
```

The definition must explicitly address:

```text
path ordering
timestamps
uid/gid
file modes
symlinks
compression parameters
archive tool identity
```

### 8.5 Validation matrix

Required validation should include:

```text
archive checksum verification -> PASS
manifest/file inventory agreement -> PASS
extract at A -> smoke PASS
move whole extracted runtime A -> B -> smoke PASS
fresh uv venv at A -> PASS
fresh uv venv at B -> PASS
uv run at A -> PASS
uv run at B -> PASS
native closure after extraction -> PASS
source archive versus extracted product fidelity -> PASS
install -> verify -> upgrade -> uninstall transaction tests
```

## 9. Stage 3-D remains deferred

Questions may include:

```text
Can uv discover the installed interpreter naturally as a system Python?
What naming and install layout improve discovery?
Should an installer expose python3.14/python3/python links?
What metadata is required for managed-Python-style integration?
Can an Android distribution be represented without misleading Linux assumptions?
```

Explicit interpreter selection remains a valid frozen integration model:

```text
uv ... --python /absolute/path/to/python
```

The project must not imitate uv-managed distribution metadata before the archive and installation contract is stable.

## 10. Current first action

Create the Stage 3-C scope before implementing packaging.

The scope must select and justify:

```text
archive payload boundary
runtime versus development split
install-prefix ownership model
manifest schema
reproducibility contract
installer/upgrade/uninstall transaction model
validation evidence layout
```
