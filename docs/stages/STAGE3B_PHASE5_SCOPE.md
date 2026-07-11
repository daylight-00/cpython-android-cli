# Stage 3-B Phase 5 Scope: Target Runtime and Closure Equivalence

> **Status:** ACTIVE — corrected final relocation rerun pending
> **Input:** isolated promoted runtime candidate
> **Execution host:** Termux on Android arm64
> **Baseline:** frozen Stage 3-A runtime and closure model

## Question

> Does the runtime assembled from promoted products preserve the frozen Stage 2 behavior and Stage 3-A closure invariants on the actual target?

## Candidate and baseline

```text
candidate
  work/termux/stage3b-promoted-runtime/prefix

baseline
  work/termux/stage2c/runtime/prefix
```

The baseline and canonical candidate are source/control inputs. Candidate-specific evidence is written under `results/termux/stage3b-*`.

## Validation order

```text
1. canonical behavior smoke
2. complete prefix inventory
3. ELF and DT_NEEDED closure
4. 67-extension isolated import surface
5. active runtime/sysconfig paths
6. CA and timezone boundary behavior
7. subprocess, uv and venv identity
8. whole-prefix relocation
```

## Gate 1: promoted canonical smoke — PASS

```text
candidate executable/prefix/base_prefix identity   PASS
native stdlib smoke                                PASS
HTTPS                                               200
subprocess identity                                PASS
uv venv creation                                   PASS
venv prefix/base_prefix identity                   PASS
uv run                                             PASS
frozen runtime mutation check                      PASS
```

Final marker:

```text
STAGE3B_PROMOTED_SMOKE=PASS
```

Evidence:

```text
docs/evidence/STAGE3B_PHASE5_PROMOTED_SMOKE.md
```

## Gate 2: promoted closure equivalence — PASS

Clean rerun result after repairing isolated-child bytecode controls:

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
candidate mutation control              PASS
frozen mutation control                 PASS
machine verifier checks                37/37
```

Final marker:

```text
STAGE3B_PROMOTED_CLOSURE=PASS
```

Evidence:

```text
docs/evidence/STAGE3B_PHASE5_PROBE_MUTATION_DIAGNOSIS.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_CLOSURE.md
```

## Gate 3: CA and timezone boundary equivalence — PASS

Corrected boundary verifier:

```text
check_count        28
failed_checks      []
missing_outputs    []
parse_errors       {}
pass               true
```

Observed model for both candidate and frozen runtime:

```text
CA policy matrix
  clean default                 HTTPS 200 through Termux CA
  explicit Termux CA            preserved, HTTPS 200
  missing CA path               repaired, HTTPS 200
  existing empty regular file   preserved, expected HTTPS failure

base zoneinfo data
  default POSIX TZPATH           unavailable on tested host
  explicit Termux zoneinfo path  delivered but absent
  base first-party tzdata        absent

uv first-party fallback
  tzdata 2026.3
  UTC                            PASS
  Asia/Seoul                     PASS
  America/New_York               PASS
```

Final marker:

```text
STAGE3B_PROMOTED_BOUNDARIES=PASS
```

Evidence:

```text
docs/evidence/STAGE3B_PHASE5_BOUNDARY_PROBE_REASSESSMENT.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_BOUNDARIES.md
```

## Gate 4 first run: functional relocation PASS, fingerprint contract incident

The production-shape workflow used:

```text
promoted source candidate
  -> copy complete prefix to location A
  -> validate A
  -> move whole prefix A -> B
  -> validate B
```

Functional result:

```text
LOCATION_RECONFIRM[A]=PASS
LOCATION_RECONFIRM[B]=PASS
STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS
STAGE3A_PRODUCTION_RELOCATION_RECONFIRM=PASS
candidate source mutation control       PASS
frozen control mutation control         PASS
```

The initial machine verifier passed 15 of 16 checks. Only the source/B tree fingerprint failed.

## Relocation fidelity diagnosis

A retained-tree, path-level comparison hashed every regular file.

```text
source_entry_count          3155
relocated_entry_count       3155
added_count                    0
removed_count                  0
portable_changed_count         0
pycache_path_count              0
portable_pass                true
```

The only strict difference was:

```text
path          lib/python3.14/lib-dynload
type          directory
field         st_size
source        12288
relocated     20480
```

No product path, file content, file metadata, symlink target, or directory mtime changed.

Classification:

```text
FINGERPRINT CONTRACT FALSE POSITIVE
```

The previous source/B fingerprint treated directory allocation size as product payload. That is not a valid cross-inode fidelity requirement.

Evidence:

```text
docs/evidence/STAGE3B_PHASE5_PROMOTED_RELOCATION_FIDELITY_INCIDENT.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_RELOCATION_FIDELITY_RESOLUTION.md
```

## Corrected fidelity contracts

### Same-tree mutation checks

Candidate and frozen before/after controls retain the strict metadata-sensitive fingerprint because the same inode tree is measured twice and must remain untouched.

### Cross-tree source/B product fidelity

The corrected portable manifest requires:

```text
same relative path set
same entry type
same mode
same mtime

regular files
  same size
  same SHA-256

symlinks
  same target

directories
  st_size excluded
```

The strict source/B fingerprint remains recorded as a non-gating observation.

## Current action: corrected Gate 4 rerun

```sh
git pull --ff-only

rm -rf \
  work/termux/stage3b-promoted-relocation \
  results/termux/stage3b-promoted-relocation

bash \
  experiments/stage3b-target-validation/validate-promoted-relocation.sh
```

The corrected wrapper now:

```text
runs A and B functional relocation assertions
keeps candidate/frozen strict same-tree mutation controls
builds source and B path-level manifests
hashes every regular file
compares symlink targets
ignores only directory st_size for cross-tree fidelity
retains strict source/B differences for diagnosis
writes a structured verifier result
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

Primary evidence:

```text
results/termux/stage3b-promoted-relocation/promoted-relocation-verification.json
results/termux/stage3b-promoted-relocation/fidelity-diagnosis/tree-delta.json
results/termux/stage3b-promoted-relocation/relocated-runtime-fidelity-check.txt
```

## File-entry count policy

The frozen Stage 3-A aggregate was `3280`; the promoted candidate has `3155` entries. Raw aggregate count is not a semantic equality gate across different products. Complete inventories, native closure, runtime identity, import surface, data boundaries, relocation behavior, and mutation controls are the acceptance dimensions.

## Acceptance conditions

```text
[x] base runtime starts
[x] native stdlib imports pass
[x] HTTPS passes
[x] subprocess re-entry passes
[x] uv venv creation passes
[x] venv prefix/base_prefix identity passes
[x] uv run passes
[x] full inventory captured
[x] unresolved DT_NEEDED edges = 0
[x] provider classification matches reviewed model
[x] 67/67 extension imports pass
[x] active runtime and sysconfig paths point to candidate
[x] closure candidate/frozen mutation controls pass
[x] CA boundary equivalence passes
[x] corrected timezone boundary equivalence passes
[x] first-party tzdata fallback equivalence passes
[x] boundary candidate/frozen mutation controls pass
[x] first-run relocation A validation passes
[x] first-run relocation B validation passes
[x] first-run stale A-prefix assertions pass
[x] first-run candidate/frozen mutation controls pass
[x] source/B fidelity incident classified
[x] corrected portable source/B contract defined
[ ] corrected relocation wrapper passes end to end
[ ] corrected relocation machine verdict passes
```

Phase 5 remains active until the corrected Gate 4 rerun passes and its final evidence is frozen.
