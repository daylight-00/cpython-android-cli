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
Stage 3-B  reproducible build-input promotion           active
Stage 3-C  distribution archive/installation contract  deferred
Stage 3-D  consumer integration                         deferred
```

The frozen Stage 2 runtime architecture is:

```text
R2 conditional self re-exec
        +
B0 PyConfig auto-discovery frontend
```

The frozen Stage 3-A result adds an evidence-based runtime closure and host/data boundary model on the tested Termux/Android arm64 environment.

## Stage 3-A frozen result

Stage 3-A inventoried and probed the already-validated Stage 2-C runtime before packaging work.

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

The five unique Android-system SONAMEs passed tested fresh-process loadability probes.

Extension surface:

```text
67 candidates
67 isolated imports PASS
0 FAIL
```

Sysconfig missing-path classification:

```text
91 records
27 unique paths
UNKNOWN=0
```

Non-ELF boundaries:

```text
CA trust
  Termux host CA integration confirmed

timezone data
  absent in base runtime
  first-party tzdata package fallback PASS

temporary storage
  Termux $PREFIX/tmp observed
```

Representative Python-level audit rows were reviewed and classified; no exact observed row remained semantically unknown.

## Final Stage 3-A reconfirmation

Canonical smoke:

```text
STAGE2C_SMOKE=PASS
```

Production-shape whole-prefix relocation:

```text
LOCATION_RECONFIRM[A]=PASS
LOCATION_RECONFIRM[B]=PASS
STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS
STAGE3A_PRODUCTION_RELOCATION_RECONFIRM=PASS
```

After moving the whole prefix from A to B, the tested runtime identity, active sysconfig paths, subprocess identity, fresh venv base identity, and uv run base identity all re-rooted at B.

Stage result:

```text
STAGE3A=FROZEN
```

See:

```text
docs/stages/STAGE3A_FINAL.md
```

## Active Stage 3-B question

Stage 3-B asks:

> Can the current launcher development input and Android runtime prefix be regenerated from explicit source, toolchain, dependency, and command inputs instead of being consumed from historical experiment paths?

The current development input is:

```text
experiments/bootstrap-android-build/android-python-work/prefix
```

This remains accepted provenance for frozen Stage 2 and Stage 3-A, but it is not the desired final build-product boundary.

Stage 3-B begins with read-only provenance reconstruction before attempting a clean replay.

See:

```text
docs/stages/STAGE3B_SCOPE.md
```

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

Python path discovery, native dependency lookup, host CA trust integration, timezone data sourcing, build provenance, and distribution packaging are treated as separate responsibilities.

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

Generated launcher artifacts use rsync rather than Git.

## Termux workflow

Depending on network topology, use the configured sync helper, then:

```sh
bash scripts/termux/prepare-runtime.sh
bash scripts/test/smoke-termux.sh
```

The intended synchronization split is:

```text
source, scripts, docs, experiment history  -> Git
generated out/<target>/<profile>/          -> rsync
```

## Documentation reading order

Current handoff path:

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
    +--> docs/evidence/
```

`docs/PROJECT_CONTEXT.md` remains the Stage 2-era handoff record. `docs/PROJECT_CONTEXT_STAGE3.md` is the current Stage 3 context.

## Design principle

```text
understand -> reproduce -> measure -> compare -> design -> optimize
```

The current active work is Stage 3-B provenance reconstruction, not archive packaging or launcher redesign.
