# Stage 3-B Scope: Reproducible Build-Input Promotion

> **Status:** FROZEN
> **Input:** frozen Stage 3-A runtime closure and boundary model
> **Primary target:** Termux on Android arm64
> **Python baseline:** CPython 3.14.6
> **Final record:** `docs/stages/STAGE3B_FINAL.md`

## Question

> Can the launcher development input and Android runtime prefix be regenerated from explicit source, toolchain, dependency, and command inputs instead of being consumed from historical experiment paths, then preserve the frozen runtime model on the actual target?

## Answer

Yes, for the selected and recorded source, toolchain, dependency, producer, product, transport, assembly, and target-validation configuration.

## Principle

```text
reproduce producer state
before
normalizing consumer artifact metadata
```

Stage 3-B did not begin by rewriting sysconfig or hiding provenance. It first made producer state and product boundaries explicit, then validated the promoted runtime against the frozen target model.

## Frozen phase status

```text
Phase 1  current producer provenance reconstruction   FROZEN
Phase 2  controlled Linux producer replay            FROZEN
Phase 3  dependency product promotion                FROZEN
Phase 4  CPython dev/runtime prefix promotion         FROZEN
Phase 5  Stage 3-A target equivalence validation      FROZEN
```

Authoritative summaries:

```text
docs/evidence/STAGE3B_PHASE1_FINAL_SUMMARY.md
docs/evidence/STAGE3B_PHASE2_FINAL_SUMMARY.md
docs/evidence/STAGE3B_PHASE3_FINAL_SUMMARY.md
docs/evidence/STAGE3B_PHASE4_FINAL_SUMMARY.md
docs/evidence/STAGE3B_PHASE5_FINAL_SUMMARY.md
```

## Frozen producer boundary

Stage 3-B made explicit:

```text
exact CPython source identity
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
promoted CPython development product
promoted CPython runtime product
promoted launcher inputs and output
transport boundary
isolated Termux assembly boundary
```

Canonical promoted target runtime:

```text
work/termux/stage3b-promoted-runtime/prefix
```

Frozen comparison/control runtime:

```text
work/termux/stage2c/runtime/prefix
```

Both are generated local products, not tracked Git artifacts.

## Preserved runtime model

The promoted runtime preserved:

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
explicit timezone-data boundary model
whole-prefix relocation
stale-prefix absence
```

## Phase 5 final result

### Canonical behavior

```text
STAGE3B_PROMOTED_SMOKE=PASS
```

### Native closure

```text
candidate entries                         3155
symlinks                                     5
ELF objects                                 81
DT_NEEDED edges                            329
RUNTIME_INTERNAL edges                      80
ANDROID_SYSTEM edges                       249
unresolved edges                             0
inspection errors                            0
Android-system SONAME dlopen               5/5
extension imports                         67/67
candidate/frozen mutation controls         PASS
machine verifier checks                  37/37
STAGE3B_PROMOTED_CLOSURE=PASS
```

### CA and timezone boundaries

```text
CA contract equivalence                    PASS
corrected direct-zoneinfo equivalence      PASS
uv tzdata 2026.3 fallback equivalence      PASS
candidate/frozen mutation controls         PASS
machine verifier checks                  28/28
STAGE3B_PROMOTED_BOUNDARIES=PASS
```

### Production-shape relocation

```text
LOCATION_RECONFIRM[A]=PASS
LOCATION_RECONFIRM[B]=PASS
STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS
RELOCATED_RUNTIME_PORTABLE_FIDELITY_CHECK=PASS
CANDIDATE_RUNTIME_MUTATION_CHECK=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
STAGE3B_PROMOTED_RELOCATION=PASS
```

Relocation verifier:

```text
schema_version      2
check_count        31
failed_checks      []
missing_outputs    []
parse_errors       {}
pass               true
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

Portable source/B fingerprint:

```text
79ca7d53f25810b1f5276d18df31f10f2ae981dc24caf67c5f33d37fa75127c8
```

Candidate source mutation fingerprint:

```text
834f7aeb2e5266f027b6ee43dd77255079b2e01cf049dad56fda5ef39ce048b0
```

Frozen control mutation fingerprint:

```text
5a14f213bbf069b844a799615ed2b87eb34b48b4251b0a48bf431337e929ce0e
```

## Frozen design decisions

### Raw file count is not semantic equality

The frozen historical runtime aggregate was `3280`; the promoted candidate has `3155` entries. Complete inventories are retained, while acceptance is based on runtime behavior, native closure, extension surface, active identity, data boundaries, relocation, and mutation/fidelity controls.

### Validation must not mutate products

Isolated child interpreters use explicit `-B` where needed. Candidate and frozen control trees are fingerprinted before and after workflows.

### Probe flags must preserve tested inputs

The zoneinfo probe does not use isolated mode while testing `PYTHONTZPATH`; it sanitizes ambient Python variables and records actual flags and inputs.

### Same-tree mutation and cross-tree fidelity are separate

Same-tree before/after controls use strict metadata-sensitive fingerprints.

Cross-tree source/B fidelity requires:

```text
same relative path set
same entry type, mode and mtime
same regular-file size and SHA-256
same symlink target
```

Directory `st_size` is excluded because it is filesystem allocation metadata. Strict cross-tree observations are still retained.

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
[x] whole-prefix relocation passes
[x] candidate/frozen mutation controls pass
[x] relocated-product path/content/symlink fidelity passes
[x] Phase 5 final evidence frozen
```

## Frozen claim boundary

Stage 3-B does not define:

```text
release archive format
archive reproducibility contract
installer transaction model
installation prefix ownership
upgrade/uninstall behavior
consumer discovery metadata
uv managed-Python provider contract
multi-ABI/API release matrix
signing, SBOM, or published provenance attestations
```

## Next stage

Stage 3-C may consume the frozen promoted product model and design the distribution archive and installation contract.

The first Stage 3-C task is contract design, not immediate packaging implementation:

```text
select archive payload boundary
select install-prefix and ownership model
select metadata and manifest format
select reproducibility definition
select installer/upgrade/uninstall transaction model
select validation matrix for unpacked and installed forms
```

Any packaging transformation must preserve or explicitly revalidate the frozen runtime, closure, boundary, relocation, and product-fidelity invariants.

## Final marker

```text
STAGE3B=FROZEN
```
