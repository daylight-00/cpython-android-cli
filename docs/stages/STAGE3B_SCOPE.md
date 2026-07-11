# Stage 3-B Scope: Reproducible Build-Input Promotion

> **Status:** ACTIVE
> **Input:** frozen Stage 3-A runtime closure and boundary model
> **Primary target:** Termux on Android arm64
> **Python baseline:** CPython 3.14.6
> **Current sub-phase:** Phase 5 final relocation rerun

## Question

> Can the launcher development input and Android runtime prefix be regenerated from explicit source, toolchain, dependency, and command inputs instead of being consumed from historical experiment paths?

Stage 3-B is a producer-reproducibility and target-equivalence stage, not a packaging stage.

## Principle

```text
reproduce producer state
before
normalizing consumer artifact metadata
```

Do not begin by mass-rewriting sysconfig or hiding historical build provenance. First make source, toolchain, dependency, command, and product boundaries explicit.

## Phase status

```text
Phase 1  current producer provenance reconstruction   FROZEN
Phase 2  controlled Linux producer replay            FROZEN
Phase 3  dependency product promotion                FROZEN
Phase 4  CPython dev/runtime prefix promotion         FROZEN
Phase 5  Stage 3-A target equivalence validation      ACTIVE
```

Authoritative documents:

```text
docs/evidence/STAGE3B_PHASE1_FINAL_SUMMARY.md
docs/stages/STAGE3B_PHASE2_SCOPE.md
docs/evidence/STAGE3B_PHASE2_FINAL_SUMMARY.md
docs/stages/STAGE3B_PHASE3_SCOPE.md
docs/evidence/STAGE3B_PHASE3_FINAL_SUMMARY.md
docs/stages/STAGE3B_PHASE4_SCOPE.md
docs/evidence/STAGE3B_PHASE4_FINAL_SUMMARY.md
docs/stages/STAGE3B_PHASE5_SCOPE.md
```

## Frozen producer result

Stage 3-B has made explicit:

```text
exact CPython source commit
CPython version/tag identity
Android SDK/NDK identity
NDK 27.3.13750724
API level and target triple
host build Python identity
third-party dependency versions and recipe revisions
dependency source archive hashes
configure inputs
build command path
promoted dependency products
promoted CPython dev/runtime products
promoted launcher inputs
transport and isolated Termux assembly
```

The promoted runtime is assembled at:

```text
work/termux/stage3b-promoted-runtime/prefix
```

Frozen control:

```text
work/termux/stage2c/runtime/prefix
```

## Stage 3-A invariants to preserve

A build is not accepted merely because it completes. The produced runtime must preserve or explicitly reopen:

```text
R2 conditional self re-exec
B0 PyConfig auto-discovery
clean launcher bootstrap
ready-process direct entry
subprocess re-entry
uv explicit-interpreter workflow
venv prefix/base_prefix identity
zero unresolved DT_NEEDED edges
67/67 tested extension surface
Termux CA integration
timezone-data boundary model
whole-prefix relocation
```

## Phase 5 completed gates

### Canonical behavior

```text
STAGE3B_PROMOTED_SMOKE=PASS
```

### Native closure

```text
candidate file entries                  3155
symlinks                                   5
ELF objects                               81
DT_NEEDED edges                          329
RUNTIME_INTERNAL edges                    80
ANDROID_SYSTEM edges                     249
unresolved edges                           0
inspection errors                          0
Android-system SONAME dlopen             5/5
extension imports                       67/67
candidate/frozen mutation controls       PASS
machine verifier checks                37/37
STAGE3B_PROMOTED_CLOSURE=PASS
```

The raw file-entry difference from the frozen aggregate (`3280`) is retained as an observation, not a semantic equality gate.

### CA and timezone boundaries

```text
CA contract equivalence                    PASS
corrected direct-zoneinfo equivalence      PASS
uv tzdata 2026.3 fallback equivalence      PASS
candidate/frozen mutation controls         PASS
machine verifier checks                  28/28
STAGE3B_PROMOTED_BOUNDARIES=PASS
```

Both base runtimes lacked a usable timezone source on the tested host. The first-party `tzdata` fallback resolved `UTC`, `Asia/Seoul`, and `America/New_York` for both.

## Phase 5 final gate: promoted whole-prefix relocation

Production shape:

```text
canonical promoted candidate
  -> copy to location A
  -> validate A
  -> move complete prefix A -> B
  -> validate B
```

At A and B the harness validates:

```text
runtime identity
active sysconfig paths
native stdlib and libc loadability
HTTPS through Termux CA integration
subprocess identity
fresh uv venv
fresh venv base identity
uv run
uv run base identity
stale-prefix absence
```

## First relocation run

Functional relocation passed:

```text
LOCATION_RECONFIRM[A]=PASS
LOCATION_RECONFIRM[B]=PASS
STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS
STAGE3A_PRODUCTION_RELOCATION_RECONFIRM=PASS
candidate mutation control                 PASS
frozen mutation control                    PASS
```

The initial source/B fingerprint failed because it included directory `st_size`.

Read-only diagnosis:

```text
source entries               3155
relocated entries            3155
added paths                     0
removed paths                   0
portable changed paths          0
pycache paths                    0
portable fidelity             PASS
```

Only one strict row differed:

```text
lib/python3.14/lib-dynload
  type          directory
  changed       st_size only
  source        12288
  relocated     20480
```

No regular-file content, file metadata, symlink target, path set, or directory mtime changed.

Classification:

```text
FINGERPRINT CONTRACT FALSE POSITIVE
```

## Corrected fidelity architecture

The earlier implementation reused one fingerprint for two different questions. The corrected architecture separates them.

### Same-tree mutation controls

Candidate and frozen prefixes are measured before and after the workflow using the strict metadata-sensitive fingerprint. These are the same inode trees and must remain unchanged.

### Cross-tree product fidelity

Source and relocated B are different inode trees. Product fidelity requires:

```text
same relative path set
same entry type
same mode
same mtime
same regular-file size and SHA-256
same symlink target
```

Directory `st_size` is excluded because it is filesystem allocation metadata, not runtime product content. The strict source/B difference remains recorded for diagnosis.

This corrected contract is stronger for actual file payload because every regular file is hashed.

Evidence:

```text
docs/evidence/STAGE3B_PHASE5_PROMOTED_RELOCATION_FIDELITY_INCIDENT.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_RELOCATION_FIDELITY_RESOLUTION.md
```

## Current action

Run the corrected end-to-end gate on Termux:

```sh
rm -rf \
  work/termux/stage3b-promoted-relocation \
  results/termux/stage3b-promoted-relocation

bash \
  experiments/stage3b-target-validation/validate-promoted-relocation.sh
```

Expected final markers:

```text
LOCATION_RECONFIRM[A]=PASS
LOCATION_RECONFIRM[B]=PASS
STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS
RELOCATED_RUNTIME_PORTABLE_FIDELITY_CHECK=PASS
CANDIDATE_RUNTIME_MUTATION_CHECK=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
STAGE3B_PROMOTED_RELOCATION=PASS
```

## Stage 3-B completion conditions

```text
[x] source identity explicit
[x] NDK/API/target identities explicit
[x] host build environment inventoried
[x] dependency identities and hashes explicit
[x] producer command model recorded
[x] replay build completes
[x] promoted products produced
[x] launcher uses promoted inputs
[x] historical experiment paths are not hidden canonical inputs
[x] promoted runtime assembled from declared products
[x] smoke equivalence passes
[x] native closure equivalence passes
[x] CA/timezone boundary equivalence passes
[x] first relocation functional assertions pass
[x] relocation fingerprint incident classified
[x] portable cross-tree fidelity contract implemented
[ ] corrected relocation workflow passes end to end
[ ] final Phase 5 evidence frozen
```

## Non-goals

Deferred unless new evidence requires them:

```text
final archive naming
installer UX
uv managed-Python provider metadata
multi-ABI/API matrix
PGO/LTO
binary-size optimization
mass patchelf rewriting
SBOM
release signing
```
