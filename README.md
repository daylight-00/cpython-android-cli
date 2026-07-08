# cpython-android-cli

An experimental CLI adaptation of an upstream CPython Android build for Termux, with uv integration.

The project studies how an upstream-built CPython Android runtime can behave as a practical command-line interpreter under Termux while preserving normal CPython CLI semantics, native stdlib imports, HTTPS trust, subprocess behavior, virtual environments, and uv workflows.

This is a research and engineering project, not a new general-purpose Python distribution and not a replacement for CPython, Termux Python, uv, Conda, or `python-build-standalone`.

## Current status

```text
Stage 1-A  explicit runtime baseline                    frozen
Stage 1-B  PyConfig frontend comparison                 frozen
Stage 2-A  bootstrap strategy comparison                complete
Stage 2-B  conditional re-exec and relocation           complete
Stage 2-C  synthesis and project workflow               active
Stage 3    standalone distribution engineering          deferred
```

The selected Stage 2 foundation is:

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

The relocation claim is intentionally scoped: whole-prefix runtime relocation was tested; relocation of an already-created external venv after moving its base runtime was not tested.

## Architecture in one picture

```text
shell / uv / venv entry point
        |
        v
Stage 2-C launcher
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

docs/           current project context and frozen stage documents
experiments/    historical experiment implementations and comparison harnesses

out/            canonical cross-build artifacts; ignored
work/           disposable assembly trees; ignored
results/        bulk validation output; ignored
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
./scripts/build/build-launcher.sh
```

Canonical artifact:

```text
out/aarch64-linux-android24/release/bin/python3.14
```

Generated artifacts can be pushed to the Termux checkout without using Git for binaries:

```sh
DRY_RUN=1 ./scripts/sync/push-out.sh
./scripts/sync/push-out.sh
```

The intended synchronization split is:

```text
source, scripts, docs, experiment history  -> Git
generated out/<target>/<profile>/          -> rsync
```

## Termux workflow

After source synchronization and artifact transfer:

```sh
./scripts/termux/prepare-runtime.sh
./scripts/test/smoke-termux.sh
```

The runtime assembly lives under `work/`; the cross-built launcher remains under the canonical `out/` path.

## Documentation

Start with:

- `docs/PROJECT_CONTEXT.md` — current architecture, decisions, stage history, and handoff context.
- `docs/stages/STAGE1A_BASELINE.md` — frozen explicit runtime baseline.
- `docs/stages/STAGE1B_PYCONFIG.md` — frozen PyConfig frontend comparison and B0 selection.
- `docs/stages/STAGE2C_DESIGN.md` — current repository, build-output, and deployment boundaries.

For implementation provenance, read the corresponding directory under `experiments/`.

## Design principle

```text
understand -> reproduce -> measure -> compare -> design -> optimize
```

not:

```text
patch -> patch more -> accidentally invent a distribution
```
