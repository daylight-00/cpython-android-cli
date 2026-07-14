# cpython-android-cli

An experimental CLI adaptation of an upstream CPython Android build for Termux, with uv integration.

The project studies how an upstream-built CPython Android runtime can behave as a practical command-line interpreter under Termux while preserving normal CPython CLI semantics, native stdlib imports, HTTPS trust, subprocess behavior, virtual environments, uv workflows, and whole-prefix runtime relocation.

This is a research and engineering project, not a new general-purpose Python distribution and not a replacement for CPython, Termux Python, uv, Conda, or `python-build-standalone`.

## Current status

```text
Stage 1-A  explicit runtime baseline                    frozen
Stage 1-B  PyConfig frontend comparison                 frozen
Stage 2-A  bootstrap strategy comparison                complete
Stage 2-B  conditional re-exec and relocation           complete
Stage 2-C  synthesis and project workflow               complete
Stage 2    native bootstrap and workflow architecture   frozen
Stage 3-A  runtime closure census and boundary model    frozen
Stage 3-B  reproducible build-input promotion           frozen
Stage 3-C  archive, installation, and lifecycle contract frozen through Gate 3D
Stage 3-C  Gate 4 cross-version transition              active — Gate 4B design frozen; implementation pending
Stage 3-C  Gate 4A authority acquisition                 frozen — A1-A6 complete
Stage 3-D  consumer integration                         deferred
```

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

## Current Stage 3-C boundary

Stage 3-C has frozen the archive, installation, transaction, recovery, ownership, addon-composition, and final-uninstall contracts for the first complete three-artifact product.

```text
runtime-base + development-addon + test-addon

Gate 3B  preserve-and-report ownership policy       FROZEN
Gate 3C  addon lifecycle and dependency policy      FROZEN
Gate 3D  complete teardown and final ownership      FROZEN
Gate 4   upgrade/downgrade                          ACTIVE — two authorities frozen; transition design ready
```

Gate 4A has independently frozen a second complete product authority for CPython 3.14.5 alongside the existing CPython 3.14.6 authority. The exact three-artifact identities, standalone Termux behavior, ownership and recovery semantics are frozen for both products. Upgrade/downgrade ordering, mixed-product compatibility, collision behavior, transition recovery, and post-transition target acceptance remain unclaimed until their own design and evidence gates complete.

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

## Documentation reading order

```text
README.md
    |
    v
docs/PROJECT_CONTEXT_STAGE3C.md
    |
    +--> docs/stages/STAGE2_FINAL.md
    +--> docs/stages/STAGE3A_FINAL.md
    +--> docs/stages/STAGE3B_FINAL.md
    +--> docs/evidence/STAGE3B_PHASE5_FINAL_SUMMARY.md
    +--> docs/stages/STAGE3_SCOPE.md
    +--> docs/evidence/
    +--> docs/GITHUB_COLLABORATION_WORKFLOW.md
```

`docs/PROJECT_CONTEXT.md` remains the Stage 2-era handoff record. `docs/PROJECT_CONTEXT_STAGE3.md` is the historical Stage 3-A/3-B snapshot. `docs/PROJECT_CONTEXT_STAGE3C.md` is the current context.

## Design principle

```text
understand -> reproduce -> measure -> compare -> design -> optimize
```

Project-control reconciliation is complete. Gate 4A independently froze CPython 3.14.5 (`v3.14.5`, commit `5607950ef232dad16d75c0cf53101d9649d89115`) as the genuine second complete product authority. Gate 4B now freezes the non-reopening whole-product transition contract and a 66-scenario bidirectional validation matrix. The design preserves the registry schema and frozen Phase 4 engine sources, rejects modified source-owned content before mutation, and requires one recovery-compatible transaction. No transition implementation, upgrade, downgrade, migration, or target behavior is frozen yet.

Gate 4 designs:

```text
experiments/stage3c-gate4-second-product-authority/GATE4A_SECOND_PRODUCT_AUTHORITY_DESIGN.md
experiments/stage3c-gate4-transition/GATE4B_TRANSITION_CONTRACT_DESIGN.md
```
