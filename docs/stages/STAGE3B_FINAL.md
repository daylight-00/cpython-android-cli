# Stage 3-B Final: Reproducible Build-Input Promotion

> **Status:** FROZEN
> **Primary target:** Termux on Android arm64
> **Python baseline:** CPython 3.14.6
> **Input:** frozen Stage 3-A runtime closure and boundary model
> **Output:** promoted, target-validated CPython Android CLI runtime products

## Final question

> Can the launcher development input and Android runtime prefix be regenerated from explicit source, toolchain, dependency, and command inputs, then preserve the frozen runtime model on the actual target?

## Answer

Yes, for the selected CPython 3.14.6, NDK 27.3.13750724, target/API configuration, dependency set, producer workflow, and Termux/Android arm64 validation host recorded by this stage.

## Frozen phase structure

```text
Phase 1  producer provenance reconstruction          FROZEN
Phase 2  controlled Linux producer replay            FROZEN
Phase 3  dependency product promotion                FROZEN
Phase 4  CPython dev/runtime product promotion        FROZEN
Phase 5  target runtime and closure equivalence       FROZEN
```

## Producer boundary

Stage 3-B made explicit:

```text
exact CPython source identity
CPython release identity
Android SDK/NDK identity
NDK 27.3.13750724
API level and target triple
host build Python and tool identities
third-party dependency versions and recipe revisions
dependency source archive hashes
configure inputs
build command path
promoted dependency products
promoted CPython development product
promoted CPython runtime product
promoted launcher input and output
transport boundary
isolated Termux assembly boundary
```

The canonical promoted target runtime is:

```text
work/termux/stage3b-promoted-runtime/prefix
```

This is a generated local product, not a tracked Git artifact.

## Target equivalence result

### Canonical behavior

```text
STAGE3B_PROMOTED_SMOKE=PASS
```

### Native closure

```text
candidate entries                         3155
ELF objects                                 81
DT_NEEDED edges                            329
RUNTIME_INTERNAL edges                      80
ANDROID_SYSTEM edges                       249
unresolved edges                             0
inspection errors                            0
Android-system SONAME dlopen               5/5
extension imports                         67/67
machine verifier checks                  37/37
STAGE3B_PROMOTED_CLOSURE=PASS
```

### Host/data boundaries

```text
CA boundary equivalence                    PASS
corrected direct-zoneinfo equivalence      PASS
uv tzdata 2026.3 fallback equivalence      PASS
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
check_count        31
failed_checks      []
missing_outputs    []
parse_errors       {}
pass               true
```

## Frozen architecture decisions

### Reproduce before normalizing

Historical experiment paths were not disguised as canonical producer inputs. Source, toolchain, dependencies, commands, products, transport, assembly, and validation were first made explicit.

### Product boundaries are first-class

The selected dependency and CPython outputs are promoted products with explicit consumers. The launcher no longer depends conceptually on an opaque historical experiment prefix.

### Runtime acceptance is semantic

Raw file-entry equality between the frozen historical runtime (`3280`) and the promoted candidate (`3155`) is not a gate. Complete inventory is retained, while acceptance is based on behavior, native closure, import surface, active identity, boundaries, relocation, and mutation controls.

### Validation must not mutate products

Isolated Python children explicitly use `-B` where required. Candidate and frozen source/control trees are fingerprinted before and after validation.

### Probe inputs must survive interpreter flags

The zoneinfo probe does not use isolated mode while testing `PYTHONTZPATH`; it sanitizes ambient Python variables and records the actual child flags and inputs.

### Same-tree mutation and cross-tree fidelity are different contracts

Same-tree before/after checks retain strict metadata-sensitive fingerprints.

Cross-tree product fidelity requires:

```text
identical relative path set
identical entry type, mode and mtime
identical regular-file size and SHA-256
identical symlink target
```

Directory `st_size` is excluded from cross-tree product identity because it is filesystem allocation metadata. Strict cross-tree differences remain diagnostic evidence.

## Final product-fidelity evidence

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

## Frozen claim boundary

Stage 3-B proves, on the tested environment:

```text
producer inputs are explicit and replayed
promoted products can be assembled on Termux
the promoted runtime preserves frozen CLI behavior
native closure has zero unresolved edges
the tested extension surface passes
CA and timezone boundary behavior is explicit and equivalent
whole-prefix relocation re-roots runtime and consumer identity
no stale A path remains in tested active state
validation does not mutate canonical candidate or frozen control
relocated B matches source product content and structure
```

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
signing, SBOM, provenance-attestation publication
```

## Stage 3-C entry boundary

Stage 3-C may now consume the frozen Stage 3-B promoted product model and design the distribution archive and installation contract.

It must not reopen producer or runtime semantics merely to simplify packaging. Any packaging transformation must preserve or explicitly revalidate:

```text
complete product path/content fidelity
runtime and subprocess identity
native closure
CA integration policy
timezone data boundary
uv and venv workflows
whole-prefix relocatability
```

The first Stage 3-C task is contract design, not immediate archive implementation:

```text
select archive payload boundary
select install-prefix and ownership model
select metadata and manifest format
select reproducibility definition
select installer/upgrade/uninstall transaction model
select validation matrix for unpacked and installed forms
```

## Evidence map

```text
docs/evidence/STAGE3B_PHASE1_FINAL_SUMMARY.md
docs/evidence/STAGE3B_PHASE2_FINAL_SUMMARY.md
docs/evidence/STAGE3B_PHASE3_FINAL_SUMMARY.md
docs/evidence/STAGE3B_PHASE4_FINAL_SUMMARY.md
docs/evidence/STAGE3B_PHASE5_FINAL_SUMMARY.md
```

## Final marker

```text
STAGE3B=FROZEN
```
