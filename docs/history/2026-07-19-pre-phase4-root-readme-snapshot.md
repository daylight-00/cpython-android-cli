# cpython-android-cli

An experimental CLI adaptation of an upstream CPython Android build for Termux, with uv integration.

The project studies how an upstream-built CPython Android runtime can behave as a practical command-line interpreter under Termux while preserving normal CPython CLI semantics, native stdlib imports, HTTPS trust, subprocess behavior, virtual environments, uv workflows, and whole-prefix runtime relocation.

This is a research and engineering project, not a new general-purpose Python distribution and not a replacement for CPython, Termux Python, uv, Conda, or `python-build-standalone`.

<!-- BEGIN GENERATED CURRENT STATE -->
## Current project coordinates

> Generated from [`docs/current/STATE.json`](docs/current/STATE.json). Do not hand-edit this block.

```text
immediate repository action  execute-document-lifecycle-phase4-mixed-document-correction
document migration           Phase 3 complete; Phase 4 ready
program epoch                E2 — upstream-thin research program
program gate held ready      E2-R1/UT-0 — exact official upstream control
program resume action        execute-e2-r1-ut0-exact-official-upstream-control
```

### Current claim boundary

```text
dual-device claim     accepted — AArch64 Termux compatibility
emulator qualified    false
selectable            false
publication           false
Epoch 3 selection     false
```

### Active blockers

none

### Unresolved risks

- official upstream package and BeeWare dependency identities are not yet frozen under UT-0
- mixed legacy documents retain snapshot-relative active/next/pending language pending Phase 4 normalization
- legacy live-document file-identity bindings remain grandfathered and require Phase 5 decoupling

### Accepted authorities

- [`experiments/epoch2-recalibration/recalibration-authority.json`](experiments/epoch2-recalibration/recalibration-authority.json): program architecture and epoch boundary (`24578fea080cf700d2bbdd607b448fd48fd6f759250d4a9a49986f8cb4e37c01`)
- [`experiments/epoch2-upstream-thin-plan/plan-authority.json`](experiments/epoch2-upstream-thin-plan/plan-authority.json): active research plan and completion gates (`62b3b07f37a90b497747562bb00a9db5a3d78b3b2cb45df8f66db22818f5eafa`)
- [`experiments/epoch2-archive-qualification/secondary-real-device-qualification-authority.json`](experiments/epoch2-archive-qualification/secondary-real-device-qualification-authority.json): bounded dual-real-device compatibility evidence (`e380198cda8c49cad704483e3edc33c2d745cc65857155b3a7edb1887410f06c`)
- [`experiments/document-lifecycle-control/document-lifecycle-control-authority.json`](experiments/document-lifecycle-control/document-lifecycle-control-authority.json): documentation lifecycle registry control plane (`d8e71c1c9ba387a17323fafc7c16a0c3fe5002cdac5045c76aa6e86282bc08cf`)
- [`experiments/document-current-state/document-current-state-authority.json`](experiments/document-current-state/document-current-state-authority.json): single current-state authority and generated-view contract (`77345393b51d1f7807f77884990838598d2520c6dca3426107c580a1fcb041b6`)
- [`experiments/document-navigation/document-navigation-authority.json`](experiments/document-navigation/document-navigation-authority.json): complete generated documentation navigation and reachability (`28faa2ba26dbded39ecd581a849288d87f030a25b81a1639796f863db86b1f23`)

### Current entry points

- [`docs/CURRENT_CONTEXT.md`](docs/CURRENT_CONTEXT.md)
- [`docs/INDEX.md`](docs/INDEX.md)
- [`docs/navigation/README.md`](docs/navigation/README.md)
- [`docs/SESSION_ONBOARDING.md`](docs/SESSION_ONBOARDING.md)
- [`docs/documentation/CURRENT_STATE_AUTHORITY.md`](docs/documentation/CURRENT_STATE_AUTHORITY.md)
- [`docs/documentation/GENERATED_NAVIGATION.md`](docs/documentation/GENERATED_NAVIGATION.md)
<!-- END GENERATED CURRENT STATE -->

## Frozen runtime architecture

```text
R2 conditional self re-exec
        +
B0 PyConfig auto-discovery frontend
```

```text
shell / uv / venv entry point
        |
        v
Stage 2 launcher
        |
        +-- resolve /proc/self/exe
        +-- derive <prefix>/lib
        +-- normalize LD_LIBRARY_PATH
        +-- preserve existing regular-file SSL_CERT_FILE
        +-- otherwise discover Termux CA bundle
        |
        +-- required libdir absent at process start
        |       -> execv(actual executable, original argv)
        |
        +-- required libdir already present
                -> B0 PyConfig initialization
                -> Py_RunMain
```

Python path discovery, native dependency lookup, host CA trust integration, timezone data sourcing, build provenance, distribution packaging, and consumer integration are treated as separate responsibilities.

## Stage 3-A frozen result

Observed inventory:

```text
file entries             3280
symlinks                    5
ELF objects                 81
DT_NEEDED edges            329
inspection errors            0
mutation check            PASS
```

Native closure:

```text
9 unique needed SONAMEs
  4 RUNTIME_INTERNAL
  5 ANDROID_SYSTEM

RUNTIME_INTERNAL edges    80
ANDROID_SYSTEM edges     249
TERMUX native edges        0
UNRESOLVED edges            0
```

Extension surface:

```text
67 candidates
67 isolated imports PASS
0 FAIL
```

Non-ELF boundaries:

```text
CA trust
  Termux host CA integration confirmed

timezone data
  absent in base runtime on tested host
  first-party tzdata package fallback PASS

temporary storage
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
```

## Stage 3-B frozen result

Stage 3-B replaced opaque historical producer assumptions with explicit source, toolchain, dependency, command, product, transport, assembly, and target-validation boundaries.

Frozen phase structure:

```text
Phase 1  producer provenance reconstruction          frozen
Phase 2  controlled Linux producer replay            frozen
Phase 3  dependency product promotion                frozen
Phase 4  CPython dev/runtime product promotion        frozen
Phase 5  target runtime and closure equivalence       frozen
```

Canonical promoted target runtime:

```text
work/termux/stage3b-promoted-runtime/prefix
```

This is a generated local product and is not stored in Git.

### Promoted behavior

```text
STAGE3B_PROMOTED_SMOKE=PASS
```

### Promoted native closure

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
machine verifier checks                  37/37
STAGE3B_PROMOTED_CLOSURE=PASS
```

### Promoted host/data boundaries

```text
CA boundary equivalence                    PASS
corrected direct-zoneinfo equivalence      PASS
uv tzdata 2026.3 fallback equivalence      PASS
machine verifier checks                  28/28
STAGE3B_PROMOTED_BOUNDARIES=PASS
```

### Promoted production-shape relocation

```text
LOCATION_RECONFIRM[A]=PASS
LOCATION_RECONFIRM[B]=PASS
STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS
RELOCATED_RUNTIME_PORTABLE_FIDELITY_CHECK=PASS
CANDIDATE_RUNTIME_MUTATION_CHECK=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
STAGE3B_PROMOTED_RELOCATION=PASS
```

Machine verifier:

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

Candidate and frozen source/control trees remained unchanged:

```text
candidate
  834f7aeb2e5266f027b6ee43dd77255079b2e01cf049dad56fda5ef39ce048b0

frozen control
  5a14f213bbf069b844a799615ed2b87eb34b48b4251b0a48bf431337e929ce0e
```

Final markers:

```text
STAGE3B_PHASE5=FROZEN
STAGE3B=FROZEN
```

See:

```text
docs/stages/STAGE3B_FINAL.md
docs/evidence/STAGE3B_PHASE5_FINAL_SUMMARY.md
```

## Important validation lessons

### Validation is not allowed to mutate products

Isolated child probes explicitly use `-B` where required. A failed attempt that produced 43 bytecode-related entries was preserved, diagnosed, repaired, and rerun from a freshly assembled candidate.

### Interpreter flags must preserve the input under test

The direct-zoneinfo probe was corrected because `-I` ignored `PYTHONTZPATH`. The final probe sanitizes ambient Python state without invalidating its own input.

### Same-tree mutation and cross-tree product fidelity differ

Same-tree before/after controls use strict metadata-sensitive fingerprints.

Cross-tree source/B fidelity requires:

```text
same relative path set
same entry type, mode and mtime
same regular-file size and SHA-256
same symlink target
```

Directory `st_size` is filesystem allocation metadata and is not part of cross-tree product identity. Strict differences remain diagnostic evidence.

### Raw aggregate file count is not semantic equality

The frozen historical runtime has `3280` entries and the promoted runtime has `3155`. Both complete inventories are retained; acceptance is based on runtime behavior, native closure, extension surface, active identity, host/data boundaries, relocation, source immutability, and product fidelity.

## Historical Stage 3-C boundary

Stage 3-C has frozen the archive, installation, transaction, recovery, ownership, addon-composition, and final-uninstall contracts for the first complete three-artifact product.

```text
runtime-base + development-addon + test-addon

Gate 3B  preserve-and-report ownership policy       FROZEN
Gate 3C  addon lifecycle and dependency policy      FROZEN
Gate 3D  complete teardown and final ownership      FROZEN
Gate 4   upgrade/downgrade                          FROZEN — 66/66 target scenarios accepted
```

Gate 4A independently froze CPython 3.14.5 alongside the existing CPython 3.14.6 authority. Gate 4B froze the whole-product transition contract, Gate 4C implemented the dedicated coordinator, Gate 4D executed the 66-scenario Termux matrix, and Gate 4E independently froze the combined evidence. Exact bidirectional transition behavior is accepted for the four frozen artifact topologies; compatibility with any third product, in-place schema migration, and consumer integration remain outside this authority.

Packaging or transition work must not silently reopen frozen producer or runtime semantics. Every new product or transformation must preserve or explicitly revalidate:

```text
runtime and subprocess identity
native closure and extension surface
CA and timezone-data boundaries
uv and venv workflows
whole-prefix relocatability
archive and manifest identities
installation ownership and dependency rules
transaction, recovery, and residual policy
```

## Repository map

```text
src/            selected current implementation
scripts/        current build, sync, assembly, and smoke workflows
config/         tracked defaults and machine-role examples
.local/         machine-local configuration; ignored

docs/           current project context, frozen stages, scopes, selected evidence
experiments/    historical and active experiment implementations

out/            canonical cross-build artifacts; ignored
work/           disposable assembly trees; ignored
results/        bulk validation and census output; ignored
dist/           packaged deliverables; ignored
cache/          optional local caches; ignored
tools/          repo-local SDK/toolchain/upstream working trees; ignored
```

`experiments/` is a first-class part of the project. Failed and superseded variants are retained when they explain a design decision.

## Configuration model

Tracked defaults:

```text
config/defaults.env
```

Machine-specific paths and sync settings:

```text
.local/env
```

```sh
mkdir -p .local
cp config/workstation.env.example .local/env
# or
cp config/termux.env.example .local/env
```

Scripts load these files themselves. Normal workflows should not require manually sourcing a date-named environment script.

## Workstation workflow

```sh
bash scripts/build/build-launcher.sh
```

Canonical launcher artifact:

```text
out/aarch64-linux-android24/release/bin/python3.14
```

Generated launcher artifacts use the tracked workstation/device sync scripts rather than Git. This build-product transport is separate from assistant/user project exchange.

## Termux workflow

```sh
bash scripts/termux/prepare-runtime.sh
bash scripts/test/smoke-termux.sh
```

Transport split:

```text
source, scripts, docs, experiment history       -> Git
generated workstation/device build products     -> tracked rsync workflows when applicable
assistant/user repository and evidence exchange -> Google Drive, normally one .tar.zst per direction
```

The Git/Termux/Drive/assistant operating contract is documented in:

```text
docs/GITHUB_COLLABORATION_WORKFLOW.md
```

## Design principle

```text
understand -> reproduce -> measure -> compare -> design -> optimize
```

Project-control reconciliation is complete. Gate 4A independently froze CPython 3.14.5 (`v3.14.5`, commit `5607950ef232dad16d75c0cf53101d9649d89115`) as the genuine second complete product authority. Gate 4B froze the non-reopening whole-product transition contract and 66-scenario matrix. Gate 4C implemented the topology-preserving coordinator while retaining registry schema 1 and the frozen Phase 4 engine sources. Gate 4D then executed the exact CPython 3.14.5 ↔ 3.14.6 matrix on Termux; the preserved v1 archive supplied 55 unaffected PASS results and raw false-negative evidence, while the corrective v2 retested H01–H08, replayed C11–C12, and derived A04 for a provenance-preserving 66/66 acceptance. Gate 4E independently freezes that authority. No third-product compatibility, registry-schema migration, or Stage 3-D consumer integration claim is made.

Gate 4 design and implementation records:

```text
experiments/stage3c-gate4-second-product-authority/GATE4A_SECOND_PRODUCT_AUTHORITY_DESIGN.md
experiments/stage3c-gate4-transition/GATE4B_TRANSITION_CONTRACT_DESIGN.md
experiments/stage3c-gate4-transition/GATE4C_TRANSITION_COORDINATOR_IMPLEMENTATION.md
experiments/stage3c-gate4-transition/GATE4D_BIDIRECTIONAL_TERMUX_TARGET_VALIDATION.md
docs/evidence/STAGE3C_PHASE5_GATE4E_INDEPENDENT_TRANSITION_FREEZE.md
```

## Stage 3-D frozen consumer integration and managed-Python feasibility

Gate 2 accepted a 64-scenario Termux census and Gate 3 froze the exact uv system-Python contract using an absolute interpreter path. Gate 4 then accepted a safe self-indexed 48-scenario Termux result: 8/8 explicit `find`/`venv`, 8/8 `uv run`, 8/8 `uv sync`, 8/8 bounded discovery, 4/4 transition continuity, and 12/12 precedence, negative, and invariant controls. The independent verifier passed 27/27 checks, and Gate 5 freezes the exact two-product, four-topology system-Python consumer surface.

Gate 6 separately proves bounded feasibility for one exact CPython 3.14.5 runtime-only product: a custom `cpython-3.14.5-linux-aarch64-none` downloads entry and local `file://` archive support isolated install, discovery, launch, uv venv creation, exact reinstall no-op, and uninstall under uv 0.11.28 without patching uv or mutating global/user state.

Global links, shell edits, production managed-install registration, automatic or network downloads, built-in catalog changes, uv patching, product mutation, schema migration, CPython 3.14.6 or multi-version managed operation, and third-product compatibility remain outside the accepted authority.

See:

```text
docs/PROJECT_CONTEXT_STAGE3D.md
docs/stages/STAGE3D_SCOPE.md
experiments/stage3d-consumer-integration/gate4-consumer-integration-authority.json
experiments/stage3d-consumer-integration/verify-gate4-consumer-integration.py
docs/evidence/STAGE3D_GATE4_CONSUMER_INTEGRATION_TARGET_VALIDATION_RESULT.md
experiments/stage3d-consumer-integration/gate6-managed-python-feasibility-authority.json
docs/evidence/STAGE3D_GATE6_MANAGED_PYTHON_FEASIBILITY_RESULT.md
```

## Stage 3-E frozen managed-Python distribution authority

Stage 3-E is frozen through Gate 5. Gate 2 accepts dual-version isolated behavior through external 117/117 re-audit, Gate 3 freezes exact-key policy, and Gate 4 accepts project-owned persistent-root lifecycle evidence with target 37/37 and independent 74/74 verification.

The accepted surface is local, offline, exact-key, and project-owned. uv's default managed root, network publication, global links, upgrades, recovery, concurrency, durability, third products, and general upstream Android support remain outside the authority and require a new stage.

The accepted Gate 4 target archive is `4553c5aae0ef3a34979a1678112b01dcdebe7087ba370aea69c44dcbce4fe112`; its target verifier passes 37/37 and the independent freeze audit passes 74/74.

See:

```text
docs/PROJECT_CONTEXT_STAGE3E.md
docs/stages/STAGE3E_SCOPE.md
docs/evidence/STAGE3E_GATE2_ISOLATED_DUAL_VERSION_CENSUS_RESULT.md
experiments/stage3e-managed-python-distribution/GATE3_MANAGED_PYTHON_DISTRIBUTION_CONTRACT.md
docs/evidence/STAGE3E_GATE4_PROJECT_OWNED_PERSISTENT_ROOT_RESULT.md
experiments/stage3e-managed-python-distribution/gate4-project-owned-persistent-root-authority.json
experiments/stage3e-managed-python-distribution/gate4-v2-independent-freeze-audit.json
experiments/stage3e-managed-python-distribution/GATE5_INDEPENDENT_DISTRIBUTION_FREEZE.md
experiments/stage3e-managed-python-distribution/gate5-independent-distribution-freeze.json
docs/evidence/STAGE3E_FINAL_SUMMARY.md
```

## Stage 3-F frozen publication and acquisition authority

Stage 3-F is complete through Gate 5. It freezes authority separation, canonical snapshot behavior, the 31/31 fail-closed loopback acquisition engine, retained actual-byte Termux validation, and the independent publication/acquisition freeze.

The selectable retained snapshot is `dbdc0edd20eeca1506066c6ec95078d9ad4fe231b81a13aa1236b480d3faa233` over exact artifacts `2edec6cfaf20a44b2458567856c1d505e6942d0e43da0e8ba2a36761ebc05be2` and `f0c449f7bc5b5bd740f4776f43bec4418645d5f33da220fa523409b6aa0af208`. Gate 4 target evidence `6cba95839a5dc05a7d4261467f1b7693e9d232fd44abe21ca4712e09b8e1977b` passes 16/16 target and 31/31 independent checks. Gate 4 repository recording result `daaf64255fce6d9c1ef2f5eb5e57d8dcc85472a4be48e56c47f21b94dee891f8` passes 91/91 project-control checks.

The first Gate 5 repository commit `71ded3869f38ed59118435f119a35591aee29f75` mechanically passed 44/44 and 108/108, but an independent post-push audit found fixture-derived replacement files had collapsed six long-lived documents, including this README and the collaboration workflow. That commit is preserved as failure evidence and is not the accepted final documentation state. The documentation-integrity correction restores the complete parent documents, keeps the Gate 5 authority files, and adds structural preservation checks so a short fixture cannot satisfy the production verifier again.

The historical Gate 2 concrete snapshot remains preserved but unselectable because its exact bytes were not retained. No public endpoint, origin trust, uv automatic acquisition, execution, installation, recovery, concurrency, durability, or third-product claim is made. Any broader work requires a new stage authority.

See:

```text
docs/PROJECT_CONTEXT_STAGE3F.md
docs/stages/STAGE3F_SCOPE.md
experiments/stage3f-publication-acquisition/gate2-retention-correction-authority.json
experiments/stage3f-publication-acquisition/gate4-retained-publication-snapshot.json
experiments/stage3f-publication-acquisition/gate4-retained-artifact-acquisition-authority.json
experiments/stage3f-publication-acquisition/GATE5_INDEPENDENT_PUBLICATION_ACQUISITION_FREEZE.md
experiments/stage3f-publication-acquisition/gate5-independent-publication-acquisition-freeze.json
experiments/stage3f-publication-acquisition/gate5-documentation-integrity-correction-authority.json
docs/evidence/STAGE3F_GATE5_INDEPENDENT_FREEZE.md
docs/evidence/STAGE3F_GATE5_DOCUMENTATION_INTEGRITY_CORRECTION.md
docs/evidence/STAGE3F_FINAL_SUMMARY.md
docs/handoff/2026-07-16-stage3f-gate5-documentation-integrity-correction.md
```
