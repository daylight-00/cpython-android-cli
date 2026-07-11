# CPython Android CLI + uv: Stage 3 Project Context

> **Status:** Current handoff context
> **Current architecture state:** Stage 2 frozen, Stage 3-A frozen, Stage 3-B Phases 1–4 frozen
> **Active phase:** Stage 3-B reproducible build-input promotion
> **Primary target:** Termux on Android arm64 (`aarch64-linux-android`)
> **Host build environment:** Separate Linux workstation
> **Python baseline:** CPython 3.14.6

## 1. Project description

The project is:

> **A CLI adaptation of an upstream CPython Android build for Termux, with uv integration.**

The project studies how an upstream-built CPython Android runtime can behave as a practical CLI interpreter under Termux while preserving:

```text
normal CPython CLI semantics
native stdlib imports
HTTPS trust
subprocess behavior
virtual environments
uv explicit interpreter workflows
whole-prefix runtime relocation
```

It is not currently:

```text
a CPython fork
a Termux Python replacement
a uv-managed Python provider
a general Android distribution system
an Android port of python-build-standalone
a static Python distribution
```

## 2. Working principle

```text
understand -> reproduce -> measure -> compare -> design -> optimize
```

not:

```text
patch -> patch more -> accidentally invent a distribution
```

The architecture process intentionally distinguishes:

```text
runtime semantics
native loader behavior
Python path discovery
host data integration
build provenance
distribution contract
consumer integration
```

A solution in one layer must not be assumed to solve the others.

## 3. Current stage status

```text
Stage 1-A  explicit runtime baseline                    FROZEN
Stage 1-B  PyConfig frontend comparison                 FROZEN
Stage 2-A  bootstrap strategy comparison                COMPLETE
Stage 2-B  conditional re-exec and relocation           COMPLETE
Stage 2-C  synthesis and project workflow               COMPLETE
Stage 2    native bootstrap and workflow architecture   FROZEN
Stage 3-A  runtime closure census and boundary model    FROZEN
Stage 3-B  reproducible build-input promotion           ACTIVE
Stage 3-C  distribution archive/installation contract  DEFERRED
Stage 3-D  consumer integration                         DEFERRED
```

## 4. Frozen Stage 2 architecture

Selected runtime architecture:

```text
R2 conditional self re-exec
        +
B0 PyConfig auto-discovery frontend
```

Conceptual flow:

```text
shell / uv / venv entry point
        |
        v
launcher
        |
        +-- RUNPATH $ORIGIN/../lib for direct libpython lookup
        |
        +-- resolve /proc/self/exe
        +-- derive actual prefix
        +-- derive <prefix>/lib
        +-- normalize LD_LIBRARY_PATH
        +-- repair/discover CA path if needed
        |
        +-- required libdir absent at process start
        |       -> execv(actual executable, original argv)
        |
        +-- required libdir already present
                -> B0 PyConfig auto-discovery
                -> Py_RunMain
```

Frozen invariants:

```text
clean top-level launch performs bootstrap re-exec
ready child process avoids redundant re-exec
self-location uses actual executable path
loader path normalization uses exact path components
Python path discovery remains automatic
CA repair remains separate from loader repair
venv sys.prefix/sys.base_prefix identity remains correct
uv explicit interpreter path remains supported
whole-prefix relocation remains supported
```

CA semantic clarification:

```text
existing SSL_CERT_FILE that points to a regular file
    -> preserve caller choice

missing or unset path
    -> discover Termux CA candidate
```

The launcher does not validate CA bundle contents.

## 5. Canonical Stage 2-C workflow

Workstation:

```text
launcher build
    -> out/aarch64-linux-android24/release/bin/python3.14
```

Transport:

```text
rsync push or Termux-initiated pull
```

Termux assembly:

```text
work/termux/stage2c/runtime/prefix
```

Validation:

```text
base runtime
subprocess re-entry
uv venv
venv identity
uv run
```

Canonical smoke marker:

```text
STAGE2C_SMOKE=PASS
```

## 6. Stage 3-A frozen closure result

Stage 3-A treated the validated runtime as data before packaging.

### Complete inventory

```text
file entries             3280
symlinks                    5
ELF objects                 81
DT_NEEDED edges            329
inspection errors            0
mutation check            PASS
```

### Native closure

```text
9 unique needed SONAMEs
  4 RUNTIME_INTERNAL
  5 ANDROID_SYSTEM

RUNTIME_INTERNAL edges    80
ANDROID_SYSTEM edges     249
TERMUX native edges        0
UNRESOLVED edges            0
```

All five unique Android-system SONAMEs passed tested fresh-process loadability probes.

### Extension surface

```text
67 candidates
67 isolated import PASS
0 FAIL
```

### Runtime paths versus build metadata

Active runtime state was relocation-aware:

```text
sys.prefix
sys.base_prefix
sys.path
active sysconfig.get_paths()
```

Development metadata remained partially stale, including:

```text
/usr/local build-prefix residue
upstream build-workspace paths
macOS NDK toolchain paths
host build-tool paths
```

Frozen distinction:

```text
runtime execution correctness
    !=
development metadata relocation correctness
```

### Sysconfig path classification

The extractor-v2 missing absolute-path set closed with:

```text
91 records
27 unique paths
UNKNOWN=0
```

Categories:

```text
BUILD_WORKSPACE_RESIDUE
TOOLCHAIN_RESIDUE
USER_SCHEME_DESTINATION
HOST_BUILD_TOOL_RESIDUE
TZDATA_SEARCH_PATH_METADATA
```

### Timezone data

```text
base runtime source absent
uv ephemeral first-party tzdata fallback PASS
```

Representative keys:

```text
UTC                  PASS with tzdata
Asia/Seoul           PASS with tzdata
America/New_York     PASS with tzdata
```

A later probe review found that the original direct `PYTHONTZPATH` scenarios used `-I`, which ignored the variable under test. Stage 3-B Phase 5 repaired the child contract and reran the frozen runtime.

Corrected result:

```text
default configured TZPATH        absent, three keys FAIL
PYTHONTZPATH=""                  delivered, package absent, three keys FAIL
explicit Termux zoneinfo path    delivered, host path absent, three keys FAIL
uv tzdata 2026.3 fallback        three keys PASS
```

The promoted runtime matched the frozen runtime exactly.

Stage 3-C must later decide whether to bundle, declare, or externally integrate timezone data.

### CA trust

```text
clean launcher environment    PASS
explicit Termux CA            PASS
missing path repair           PASS
existing empty regular file   preserved, HTTPS FAIL
```

Frozen interpretation:

```text
CA path repair exists
CA content validation does not
```

The promoted runtime preserved the same four-scenario matrix in Stage 3-B Phase 5.

### Representative runtime audit

Exact observed rows were classified as:

```text
/dev/null
project experiment path
$PREFIX/tmp temporary storage
libc.so
network :443
file / uname optional platform helpers
```

No exact observed row remained semantically unknown.

The audit hook result is observational and not a complete syscall trace.

## 7. Final Stage 3-A reconfirmation

Canonical smoke:

```text
STAGE2C_SMOKE=PASS
```

Production-shape relocation:

```text
LOCATION_RECONFIRM[A]=PASS
LOCATION_RECONFIRM[B]=PASS
STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS
STAGE3A_PRODUCTION_RELOCATION_RECONFIRM=PASS
```

At B, the harness directly checked absence of the old A path from:

```text
sys.prefix
sys.base_prefix
sys.path
active sysconfig paths
child interpreter identity
fresh venv base identity
uv run base identity
```

Stage result:

```text
STAGE3A=FROZEN
```

## 8. Current Stage 3-B problem

Current launcher development input:

```text
experiments/bootstrap-android-build/android-python-work/prefix
```

This is accepted historical provenance, but not the desired final build-product boundary.

Stage 3-B asks:

> Can the launcher development input and Android runtime prefix be regenerated from explicit source, toolchain, dependency, and command inputs?

Required reconstruction domains:

```text
CPython source identity
CPython tag/commit identity
Android SDK identity
Android NDK identity
API level
host build Python identity
third-party native dependency names and versions
third-party dependency source identities
build commands
build options
dependency prefixes
CPython output prefix identity
launcher compile/link inputs
hashes of promoted build products
```

## 9. Current Stage 3-B action

Phases 1–4 are frozen. Source and toolchain provenance, the controlled Linux replay, exact dependency products, the promoted CPython package, the promoted launcher, workstation handoff, transport, and isolated Termux assembly are explicit and verified.

### Completed Phase 5 gates

Promoted canonical behavior:

```text
STAGE2C_SMOKE=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
STAGE3B_PROMOTED_SMOKE=PASS
```

Promoted closure equivalence:

```text
ELF objects                               81
DT_NEEDED edges                          329
RUNTIME_INTERNAL edges                    80
ANDROID_SYSTEM edges                     249
unresolved edges                           0
Android-system SONAME dlopen             5/5
extension imports                       67/67
candidate mutation control              PASS
frozen mutation control                 PASS
machine verifier checks                37/37
STAGE3B_PROMOTED_CLOSURE=PASS
```

The `+43` bytecode incident is closed as validation-induced mutation. The repaired isolated child contract uses explicit `-B`, and the candidate was freshly reassembled before the passing rerun.

Promoted CA/timezone boundaries:

```text
CA contract equivalence                    PASS
corrected direct-zoneinfo equivalence      PASS
uv tzdata 2026.3 fallback equivalence      PASS
candidate mutation control                 PASS
frozen mutation control                    PASS
machine verifier checks                  28/28
STAGE3B_PROMOTED_BOUNDARIES=PASS
```

The corrected direct-zoneinfo child uses:

```text
python -B -P -s -c ...
```

with a sanitized Python environment so `PYTHONTZPATH` remains the deliberate variable under test.

### Current action: promoted whole-prefix relocation

Run:

```sh
bash experiments/stage3b-target-validation/validate-promoted-relocation.sh
```

The workflow uses:

```text
source candidate
  work/termux/stage3b-promoted-runtime/prefix

relocation copy
  work/termux/stage3b-promoted-relocation/location-a/prefix
    -> move to
  work/termux/stage3b-promoted-relocation/location-b/prefix

results
  results/termux/stage3b-promoted-relocation
```

At A and B it validates:

```text
base runtime identity
active sysconfig paths
HTTPS
subprocess identity
fresh uv venv and base identity
uv run and base identity
forbidden stale-prefix absence
```

Outer controls validate:

```text
canonical source candidate unchanged
frozen Stage 2-C control unchanged
final B fingerprint equals source candidate fingerprint
A absent after move
B present with executable Python
structured machine verdict
```

Expected final marker:

```text
STAGE3B_PROMOTED_RELOCATION=PASS
```

The frozen Stage 2-C prefix and frozen Stage 3-A result directory remain read-only controls.

Authoritative scope and current evidence:

```text
docs/stages/STAGE3B_SCOPE.md
docs/stages/STAGE3B_PHASE5_SCOPE.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_SMOKE.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_CLOSURE.md
docs/evidence/STAGE3B_PHASE5_BOUNDARY_PROBE_REASSESSMENT.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_BOUNDARIES.md
```

Collaboration workflow:

```text
docs/GITHUB_COLLABORATION_WORKFLOW.md
```

## 10. Repository structure

Tracked project state:

```text
src/
scripts/
config/
docs/
experiments/
```

Machine-local configuration:

```text
.local/env
```

Generated state:

```text
out/
work/
results/
dist/
cache/
tools/
```

Current canonical output shape:

```text
out/<target>/<profile>/
```

Current target:

```text
out/aarch64-linux-android24/release/
```

## 11. Reading order

Current recommended order:

```text
README.md
    |
    v
docs/PROJECT_CONTEXT_STAGE3.md
    |
    +--> docs/stages/STAGE2_FINAL.md
    |
    +--> docs/stages/STAGE3A_FINAL.md
    |
    +--> docs/stages/STAGE3B_SCOPE.md
    |
    +--> docs/stages/STAGE3B_PHASE5_SCOPE.md
    |
    +--> docs/evidence/
    |
    +--> docs/GITHUB_COLLABORATION_WORKFLOW.md
```

`docs/PROJECT_CONTEXT.md` remains useful as the Stage 2-era handoff record, but `PROJECT_CONTEXT_STAGE3.md` is the current Stage 3 handoff context.
