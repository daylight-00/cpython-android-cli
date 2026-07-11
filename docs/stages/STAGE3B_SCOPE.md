# Stage 3-B Scope: Reproducible Build-Input Promotion

> **Status:** ACTIVE
> **Input:** Frozen Stage 3-A runtime closure and boundary model
> **Primary target:** Termux on Android arm64
> **Current Python baseline:** CPython 3.14.6
> **Current active sub-phase:** Phase 5 target runtime and closure equivalence

## 1. Question

Stage 3-B asks:

> Can the current launcher development input and Android runtime prefix be regenerated from explicit source, toolchain, dependency, and command inputs instead of being consumed from historical experiment paths?

Stage 3-B is not a packaging stage.

It must first establish and replay a reproducible producer model for the already-validated runtime closure.

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

Stage 3-B models these as producer provenance before any metadata normalization.

## 3. Principle

```text
reproduce producer state
before
normalizing consumer artifact metadata
```

Do not begin Stage 3-B by mass-rewriting sysconfig values.

First identify and replay:

```text
source identity
host/toolchain identity
dependency graph
configure inputs
build command path
output product boundary
```

## 4. Phase status

```text
Phase 1  current producer provenance reconstruction   FROZEN
Phase 2  controlled Linux producer replay            FROZEN
Phase 3  dependency product promotion                FROZEN
Phase 4  CPython dev/runtime prefix promotion         FROZEN
Phase 5  Stage 3-A closure equivalence validation     ACTIVE
```

Authoritative phase documents:

```text
docs/evidence/STAGE3B_PHASE1_FINAL_SUMMARY.md
docs/stages/STAGE3B_PHASE2_SCOPE.md
docs/evidence/STAGE3B_PHASE2_FINAL_SUMMARY.md
docs/stages/STAGE3B_PHASE3_SCOPE.md
docs/evidence/STAGE3B_PHASE3_FINAL_SUMMARY.md
docs/stages/STAGE3B_PHASE4_SCOPE.md
docs/evidence/STAGE3B_PHASE4_FINAL_SUMMARY.md
docs/stages/STAGE3B_PHASE5_SCOPE.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_SMOKE.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_CLOSURE.md
docs/evidence/STAGE3B_PHASE5_BOUNDARY_PROBE_REASSESSMENT.md
```

Current Phase 5 checkpoint:

```text
promoted canonical behavior smoke        PASS
promoted semantic closure equivalence    PASS
candidate mutation control               PASS
frozen runtime mutation control          PASS
next gate                                CA and timezone boundary equivalence
```

Next command on Termux:

```sh
bash experiments/stage3b-target-validation/validate-promoted-boundaries.sh
```

## 5. Phase 1 frozen result

Phase 1 recovered enough producer identity to begin a controlled replay.

Observed:

```text
phase2_ready=true
remaining_gates=[]
```

Producer structure:

```text
CONFIG_ARGS structure   PASS
CFLAGS structure        PASS
LDFLAGS structure       PASS
```

Dependency release-tag model:

```text
bzip2   1.0.8-3   MATCH
libffi  3.4.4-3   MATCH
openssl 3.5.7-0   MATCH
sqlite  3.50.4-0  MATCH
xz      5.4.6-1   MATCH
zstd    1.5.7-2   MATCH
```

NDK identity:

```text
preserved snapshot       27.3.13750724
embedded prefix metadata 27.3.13750724
active Linux compiler    27.3.13750724
```

Source gate:

```text
exact_cpython_source_git_identity_available=true
```

Producer lineage:

```text
current dev prefix metadata
  macOS producer
  darwin-x86_64 NDK prebuilt
  /Users/runner/work/release-tools/... workspace

replay workstation
  Linux
```

Phase 1 conclusion:

```text
STAGE3B_PHASE1=FROZEN
STAGE3B_PHASE2_READY=true
```

## 6. Phase 2 frozen result

Phase 2 answered:

> The exact identified CPython source commit can be rebuilt through the preserved Android producer model on Linux using the matched NDK, explicit driver Python, and dependency declaration graph.

Observed final marker:

```text
STAGE3B_UPSTREAM_REPLAY=PASS
```

The replay must not modify:

```text
original CPython source checkout
historical bootstrap experiment tree
historical development prefix
frozen Stage 2-C runtime
frozen Stage 3-A results
```

Replay shape:

```text
exact source commit
    -> detached Git worktree

source Android producer model
    -> hash-checked against preserved snapshot

separate cross-build root
    -> build Python
    -> target dependency prefix
    -> Android CPython prefix

shared explicit dependency cache
    -> declared source-deps release archives

package product
    -> replay artifact for later comparison
```

See:

```text
docs/stages/STAGE3B_PHASE2_SCOPE.md
```

## 7. Required producer identities

Stage 3-B captures and preserves at minimum:

```text
CPython source identity
  version
  tag/describe
  exact commit

Android toolchain identity
  SDK root identity
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
  recipe revision
  release tag
  source release location
  later: archive hashes and produced-file equivalence

CPython build configuration
  configure arguments
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

## 8. Desired conceptual pipeline

```text
source inputs
    -> declared and immutable

toolchain inputs
    -> declared

native dependency sources
    -> reproducible dependency products

CPython Android build
    -> reproducible Android host/runtime prefix

launcher build
    -> reproducible production launcher artifact

runtime assembly
    -> Stage 3-A-equivalent runtime closure
```

## 9. Stage 3-A invariants that Stage 3-B must preserve

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
67/67 tested extension import surface, unless intentionally changed and reviewed
Termux CA integration behavior
timezone-data boundary understanding
whole-prefix production relocation behavior
```

## 10. Phase 2 acceptance conditions

The controlled replay step is successful when:

```text
[x] exact source detached worktree prepared
[x] source producer scripts match preserved snapshot
[x] SDK root resolved
[x] NDK 27.3.13750724 confirmed
[x] build Python configured and built
[x] Android host prefix configured and built
[x] target prefix installed
[x] Python.h exists
[x] pyconfig.h exists
[x] libpython3.14.so exists
[x] stdlib exists
[x] replay package archive produced
```

A successful build replay does not yet prove Stage 3-A equivalence.

## 11. Phase 5 comparison requirements

The replayed runtime is compared against Stage 3-A constraints:

```text
file inventory differences
ELF object inventory differences
DT_NEEDED graph differences
unique SONAME differences
provider classification differences
extension import surface
active runtime path behavior
sysconfig metadata differences
CA behavior
timezone boundary behavior
smoke behavior
relocation behavior
```

Completed comparisons:

```text
canonical behavior smoke
ELF and DT_NEEDED closure
provider classification
Android-system SONAME loadability
67-extension isolated import surface
active runtime and sysconfig identity
candidate/frozen mutation controls for closure workflow
```

Current comparison:

```text
corrected CA boundary equivalence
corrected direct-zoneinfo input and semantic equivalence
uv-injected first-party tzdata fallback equivalence
candidate/frozen mutation controls for boundary workflow
```

Expected producer-host metadata deltas such as:

```text
BUILD_GNU_TYPE
absolute workspace paths
NDK prebuilt host path
host build-Python path
```

are not failures by themselves.

The raw file-entry aggregate is also not a semantic gate. The promoted candidate had `3155` entries versus the frozen aggregate `3280`, while every closure, identity, import, and mutation gate passed. Complete row-level inventories remain available for review.

## 12. Stage 3-B completion conditions

Stage 3-B is complete only when:

```text
[x] CPython source identity is explicit
[x] Android NDK/API/target identities are explicit
[x] host build environment is inventoried
[x] third-party dependency release tags are explicit
[x] CPython configure/build command model is recorded
[x] dependency archive hashes are promoted
[x] replay build completes
[x] replay package is produced
[x] launcher build inputs come from promoted generated products
[x] historical experiment paths are not hidden canonical inputs
[x] runtime assembly is regenerated from declared products
[x] regenerated runtime passes closure comparison review
[x] regenerated runtime passes smoke validation
[ ] regenerated runtime preserves or intentionally reopens CA/timezone boundaries
[ ] regenerated runtime passes whole-prefix relocation validation
```

## 13. Non-goals

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
