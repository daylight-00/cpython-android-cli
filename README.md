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
Stage 3    distribution engineering                     active
Stage 3-A  runtime closure census                       active
```

The frozen Stage 2 foundation is:

```text
R2 conditional self re-exec
        +
B0 PyConfig auto-discovery frontend
```

The Stage 2-B validation established, on the tested Termux/Android arm64 environment:

- clean top-level launch performs one bootstrap re-exec,
- prepared subprocesses enter Python directly without another re-exec,
- missing or wrong native search-path state is repaired,
- invalid CA configuration is repaired independently,
- duplicate required library-path entries are normalized,
- native stdlib imports work,
- HTTPS works,
- subprocess re-entry works,
- uv venv and venv identity work,
- uv run works,
- the runtime prefix works after a whole-prefix move from one absolute path to another.

Stage 2-C then reproduced the selected architecture through the cleaned repository workflow:

```text
workstation canonical build
    -> artifact transport
    -> Termux runtime assembly
    -> base runtime smoke
    -> subprocess
    -> uv venv
    -> venv identity
    -> uv run
    -> STAGE2C_SMOKE=PASS
```

The relocation claim is intentionally scoped: whole-prefix runtime relocation was tested; relocation of an already-created external venv after moving its base runtime was not tested.

## Current Stage 3 question

Stage 3 does not begin by changing the frozen launcher.

It asks:

> How should the validated Stage 2 runtime become a reproducible, inspectable, relocatable distribution product without losing the frozen runtime behavior?

The first active sub-stage is Stage 3-A:

```text
runtime file inventory
symlink inventory
ELF object inventory
DT_NEEDED edge inventory
Python runtime identity
provider classification
unresolved-edge review
non-mutation verification
```

Run the first census on Termux with:

```sh
bash experiments/stage3a-runtime-closure/inventory-runtime.sh
```

See `docs/stages/STAGE3_SCOPE.md`.

## Architecture in one picture

```text
shell / uv / venv entry point
        |
        v
Stage 2 launcher
        |
        +-- resolve /proc/self/exe
        +-- derive <prefix>/lib
        +-- normalize LD_LIBRARY_PATH
        +-- preserve or discover Termux CA bundle
        |
        +-- required libdir absent at process start
        |       -> execv(actual executable, original argv)
        |
        +-- required libdir already present
                -> B0 PyConfig initialization
                -> Py_RunMain
```

Python path discovery, native dependency lookup, and host CA trust integration are treated as separate responsibilities.

## Repository map

```text
src/            selected current implementation
scripts/        current build, sync, assembly, and smoke workflows
config/         tracked defaults and machine-role examples
.local/         machine-local configuration; ignored

docs/           current project context, frozen stages, selected evidence
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

Tracked project defaults:

```text
config/defaults.env
```

Machine-specific paths and sync settings:

```text
.local/env
```

Start from the appropriate example:

```sh
mkdir -p .local
cp config/workstation.env.example .local/env
# or
cp config/termux.env.example .local/env
```

Scripts load these files themselves. Normal workflows should not require manually sourcing a date-named environment script.

The files under `config/legacy/` are historical snapshots from the earlier date-based workspace and are not active configuration.

## Workstation workflow

```sh
bash scripts/build/build-launcher.sh
```

Canonical artifact:

```text
out/aarch64-linux-android24/release/bin/python3.14
```

For a topology where the workstation can initiate the connection to Termux:

```sh
DRY_RUN=1 bash scripts/sync/push-out.sh
bash scripts/sync/push-out.sh
```

## Termux pull topology

The successful Stage 2-C validation used Termux-initiated pull because Termux inbound connectivity was unavailable.

```sh
DRY_RUN=1 bash scripts/sync/pull-out.sh
bash scripts/sync/pull-out.sh
```

Then:

```sh
bash scripts/termux/prepare-runtime.sh
bash scripts/test/smoke-termux.sh
```

The intended synchronization split is:

```text
source, scripts, docs, experiment history  -> Git
generated out/<target>/<profile>/          -> rsync
```

The connection initiator may be workstation push or Termux pull depending on network topology.

## Documentation

Start with:

- `docs/PROJECT_CONTEXT.md` — frozen Stage 2 architecture, decisions, history, and handoff context.
- `docs/stages/STAGE1A_BASELINE.md` — frozen explicit runtime baseline.
- `docs/stages/STAGE1B_PYCONFIG.md` — frozen PyConfig frontend comparison and B0 selection.
- `docs/stages/STAGE2_FINAL.md` — low-level Stage 2 architecture, validation, relocation, and workflow freeze.
- `docs/stages/STAGE2C_DESIGN.md` — completed repository, build-output, transport, and deployment design.
- `docs/stages/STAGE3_SCOPE.md` — active distribution-engineering scope and Stage 3-A closure census.
- `docs/evidence/` — selected decision-bearing evidence summaries.

For implementation provenance, read the corresponding directory under `experiments/`.

## Design principle

```text
understand -> reproduce -> measure -> compare -> design -> optimize
```

not:

```text
patch -> patch more -> accidentally invent a distribution
```
