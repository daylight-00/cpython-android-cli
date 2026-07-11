# Stage 3-B Phase 5: Target Runtime and Closure Equivalence

> **Status:** FROZEN
> **Input:** isolated promoted runtime candidate
> **Execution host:** Termux on Android arm64
> **Baseline:** frozen Stage 2-C runtime and Stage 3-A closure/boundary model

## Question

> Does the runtime assembled from promoted products preserve the frozen runtime behavior and closure invariants on the actual target?

## Inputs

```text
candidate
  work/termux/stage3b-promoted-runtime/prefix

frozen control
  work/termux/stage2c/runtime/prefix
```

Both are treated as read-only source/control trees during validation.

## Gate sequence

```text
1. canonical behavior smoke
2. complete prefix inventory
3. ELF and DT_NEEDED closure
4. 67-extension isolated import surface
5. active runtime/sysconfig paths
6. CA and timezone boundary behavior
7. subprocess, uv and venv identity
8. production-shape whole-prefix relocation
```

## Gate 1: canonical smoke — PASS

```text
candidate executable/prefix/base_prefix identity   PASS
native stdlib smoke                                PASS
HTTPS                                               200
subprocess identity                                PASS
uv venv creation                                   PASS
venv prefix/base_prefix identity                   PASS
uv run                                             PASS
frozen mutation control                            PASS
STAGE3B_PROMOTED_SMOKE=PASS
```

## Gate 2: native closure — PASS

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
STAGE3B_PROMOTED_CLOSURE=PASS
```

The first attempt created 43 bytecode-related entries because isolated child interpreters ignored shell `PYTHON*` controls. The child contract was corrected to `python -I -B -S`, and a fresh candidate was assembled rather than cleaned in place.

## Gate 3: CA and timezone boundaries — PASS

```text
machine verifier checks                  28/28
CA policy matrix                          equivalent
corrected direct-zoneinfo scenarios      equivalent
base timezone source                     unavailable in both
uv first-party tzdata                    2026.3
UTC                                      PASS for both
Asia/Seoul                               PASS for both
America/New_York                         PASS for both
candidate mutation control               PASS
frozen mutation control                  PASS
STAGE3B_PROMOTED_BOUNDARIES=PASS
```

The direct-zoneinfo probe was corrected because isolated mode ignored the `PYTHONTZPATH` variable under test.

## Gate 4: production-shape relocation — PASS

Production shape:

```text
canonical promoted candidate
  -> copy complete prefix to location A
  -> validate A
  -> move complete prefix A -> B
  -> validate B
```

A and B validated:

```text
sys.executable, sys.prefix and sys.base_prefix
active sysconfig paths
native stdlib and libc loadability
HTTPS through Termux CA integration
subprocess interpreter identity
fresh uv venv and venv base identity
uv run and uv run base identity
forbidden stale-prefix absence
```

Final markers:

```text
LOCATION_RECONFIRM[A]=PASS
LOCATION_RECONFIRM[B]=PASS
STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS
RELOCATED_RUNTIME_PORTABLE_FIDELITY_CHECK=PASS
CANDIDATE_RUNTIME_MUTATION_CHECK=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
STAGE3B_PROMOTED_RELOCATION=PASS
```

Machine verdict:

```text
schema_version      2
check_count        31
failed_checks      []
missing_outputs    []
parse_errors       {}
pass               true
```

## Relocated-product fidelity

```text
source_entry_count             3155
relocated_entry_count          3155
added_count                       0
removed_count                     0
portable_changed_count            0
pycache_path_count                 0
portable_pass                   true
strict_changed_count               0
strict_pass                     true
```

Portable source/B fingerprint:

```text
79ca7d53f25810b1f5276d18df31f10f2ae981dc24caf67c5f33d37fa75127c8
```

Path-level strict diagnostic source/B fingerprint:

```text
f46b5d81917e9d5dbcfc826a7ef33ef84c1b7db127689def7f20966037a57011
```

Same-tree shell source/B fingerprint on the clean rerun:

```text
834f7aeb2e5266f027b6ee43dd77255079b2e01cf049dad56fda5ef39ce048b0
```

## Fidelity incident and resolution

The first relocation attempt passed functional A/B validation but the old cross-tree fingerprint differed because `lib/python3.14/lib-dynload` had a different directory `st_size` after copying.

Read-only diagnosis proved:

```text
same 3155 paths
no added or removed entries
no regular-file content differences
no file metadata differences
no symlink differences
no directory mtime differences
no bytecode additions
```

The failure was classified as a fingerprint-contract false positive. The final architecture separates:

```text
same-tree mutation
  strict metadata-sensitive fingerprint

cross-tree product fidelity
  same path/type/mode/mtime
  same regular-file size and SHA-256
  same symlink target
  directory st_size excluded
```

This is stronger for actual product payload because every regular file is hashed.

## Source/control mutation fingerprints

Canonical candidate:

```text
before == after
834f7aeb2e5266f027b6ee43dd77255079b2e01cf049dad56fda5ef39ce048b0
```

Frozen control:

```text
before == after
5a14f213bbf069b844a799615ed2b87eb34b48b4251b0a48bf431337e929ce0e
```

## File-entry count policy

The frozen historical aggregate was `3280`; the promoted candidate has `3155` entries. Raw aggregate equality across separately produced trees is not a semantic gate. Complete inventories are retained, while acceptance is based on behavior, native closure, import surface, active identity, data boundaries, relocation, and mutation/product-fidelity controls.

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
[x] relocation A validation passes
[x] relocation B validation passes
[x] stale A-prefix assertions pass
[x] relocated-product path/content/symlink fidelity passes
[x] relocation candidate/frozen mutation controls pass
[x] relocation machine verdict passes 31/31
```

## Evidence map

```text
docs/evidence/STAGE3B_PHASE5_PROMOTED_SMOKE.md
docs/evidence/STAGE3B_PHASE5_PROBE_MUTATION_DIAGNOSIS.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_CLOSURE.md
docs/evidence/STAGE3B_PHASE5_BOUNDARY_PROBE_REASSESSMENT.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_BOUNDARIES.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_RELOCATION_FIDELITY_INCIDENT.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_RELOCATION_FIDELITY_RESOLUTION.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_RELOCATION.md
docs/evidence/STAGE3B_PHASE5_FINAL_SUMMARY.md
```

## Final marker

```text
STAGE3B_PHASE5=FROZEN
```
