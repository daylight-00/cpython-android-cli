# Stage 3-B Scope: Reproducible Build-Input Promotion

> **Status:** ACTIVE
> **Input:** Frozen Stage 3-A runtime closure and boundary model
> **Primary target:** Termux on Android arm64
> **Current Python baseline:** CPython 3.14.6

## 1. Question

Stage 3-B asks:

> Can the current launcher development input and Android runtime prefix be regenerated from explicit source, toolchain, dependency, and command inputs instead of being consumed from historical experiment paths?

Stage 3-B is not a packaging stage.

It must first establish a reproducible producer model for the already-validated runtime closure.

## 2. Starting problem

The current launcher development input is:

```text
experiments/bootstrap-android-build/android-python-work/prefix
```

and the validated runtime input has historical provenance through the earlier Android build experiment.

This is accepted evidence for Stage 2 and Stage 3-A, but it is not the desired final build-product boundary.

Stage 3-A also observed development metadata containing:

```text
upstream build workspace residue
macOS NDK toolchain paths
/usr/local build-prefix residue
host build-tool paths
```

The next stage must model these as reproducible inputs rather than patching individual strings after the fact.

## 3. Principle

```text
reproduce producer state
before
normalizing consumer artifact metadata
```

Do not begin Stage 3-B by mass-rewriting sysconfig values.

First identify:

```text
what source produced them
what host/toolchain produced them
what dependency prefix produced them
what command-line options produced them
which values matter only to development workflows
```

## 4. Required input identities

Stage 3-B must capture at minimum:

```text
CPython source identity
  version
  tag
  commit
  source hash or equivalent immutable identity

Android toolchain identity
  SDK version
  NDK version
  API level
  target triple
  host toolchain platform

host build environment
  host OS identity
  host architecture
  host build Python identity
  key build tools and versions

third-party native dependencies
  name
  version
  source identity
  build options
  output prefix identity

CPython build configuration
  configure command
  environment inputs
  cross-build paths
  dependency paths
  build command sequence

launcher build configuration
  compiler identity
  include path source
  libpython source
  compile flags
  link flags
```

## 5. Desired conceptual pipeline

```text
source inputs
    -> declared and immutable

toolchain inputs
    -> declared

native dependency sources
    -> reproducible dependency build products

CPython Android build
    -> reproducible Android host/runtime prefix

launcher build
    -> reproducible production launcher artifact

runtime assembly
    -> Stage 3-A-equivalent runtime closure
```

## 6. Stage 3-A invariants that Stage 3-B must preserve

A Stage 3-B producer is not acceptable merely because it builds.

The produced runtime must preserve or intentionally reopen:

```text
R2 conditional self re-exec behavior
B0 PyConfig auto-discovery
clean launcher bootstrap
ready-process direct entry
subprocess re-entry behavior
uv explicit-interpreter workflow
venv prefix/base_prefix identity
native closure with zero unresolved DT_NEEDED edges
67/67 tested extension import surface, unless the produced runtime inventory intentionally differs and is reviewed
Termux CA integration behavior
timezone-data boundary understanding
whole-prefix production relocation behavior
```

## 7. First experiment sequence

Stage 3-B should proceed in this order.

### Phase 1: provenance reconstruction

Record the current known producer lineage without rebuilding anything yet.

Outputs should include:

```text
current-build-inputs.json
current-toolchain-identity.json
current-dependency-provenance.tsv
current-build-command-map.md
```

### Phase 2: upstream Android build replay

Replay the upstream CPython Android build flow from declared source and toolchain inputs.

Do not optimize or redesign the upstream build process during the first replay.

### Phase 3: dependency product promotion

Move third-party native dependency products out of opaque historical experiment paths into explicit generated-product boundaries.

Candidate shape:

```text
out/deps/<target>/<dependency>/<version>/...
```

The exact layout is not yet frozen.

### Phase 4: CPython development/runtime prefix promotion

Produce explicit generated prefixes suitable for:

```text
launcher compilation
runtime assembly
metadata inspection
```

Do not silently use `pristine-test` or copied historical trees as canonical producer inputs.

### Phase 5: closure equivalence validation

Compare the newly produced runtime against Stage 3-A constraints:

```text
file inventory differences
ELF object inventory differences
DT_NEEDED closure differences
SONAME classification differences
extension import results
sysconfig metadata differences
smoke behavior
relocation behavior
```

## 8. Initial acceptance conditions

Stage 3-B is complete only when:

```text
[ ] CPython source identity is explicit and reproducible
[ ] Android SDK/NDK/API identities are explicit
[ ] host build Python identity is explicit
[ ] third-party dependency sources and versions are explicit
[ ] dependency build commands are recorded
[ ] CPython Android build commands are recorded
[ ] launcher build inputs come from promoted generated products
[ ] historical experiment paths are not required as hidden canonical inputs
[ ] runtime assembly can be regenerated from declared products
[ ] regenerated runtime passes closure comparison review
[ ] regenerated runtime passes smoke validation
[ ] regenerated runtime passes whole-prefix relocation validation
```

## 9. Non-goals

Do not add during Stage 3-B unless required by new evidence:

```text
final release archive naming
installer UX
uv managed-Python download metadata
multi-ABI release matrix
multi-API-level release matrix
PGO/LTO optimization
binary-size optimization
mass patchelf rewriting
SBOM generation
release signing
```

These belong to later work.

## 10. First concrete action

Start with a read-only provenance reconstruction of the current producer chain.

The first Stage 3-B experiment should answer:

> Which exact source, SDK/NDK, host Python, third-party native dependency products, commands, and paths produced the currently validated CPython Android prefix and launcher development input?

Only after that map exists should the project attempt a clean replay.
