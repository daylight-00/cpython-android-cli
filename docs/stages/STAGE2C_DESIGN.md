# Stage 2-C Design: Synthesis and Project Workflow

> **Status:** Active synthesis stage
> **Input:** Stage 2-B R2 validation and relocation success
> **Target:** Termux on Android arm64
> **Python:** CPython 3.14.6

## 1. Purpose

Stage 2-C turns the validated Stage 2-B R2 experiment into a production-shaped project workflow.

The stage has two goals:

1. preserve the behavior validated in Stage 2-B while reducing experimental naming and manual file wiring;
2. establish one repository-wide path model for source, build artifacts, runtime assembly, test results, and workstation-to-Termux synchronization.

Stage 2-C is a synthesis stage, not a new bootstrap-strategy experiment.

## 2. Selected runtime design

The selected launcher policy is the Stage 2-B R2 fixed-point design:

```text
actual executable
        |
        v
derive prefix/lib
        |
        v
normalize LD_LIBRARY_PATH
        |
        +-- required libdir absent at process start
        |       configure CA
        |       execv(actual executable, original argv)
        |
        +-- required libdir already present
                repair/discover CA if needed
                B0 PyConfig
                Py_RunMain
```

The runtime responsibilities remain separate:

```text
Python initialization
    B0 PyConfig auto-discovery

native dependency lookup
    self-derived <prefix>/lib
    conditional re-exec when activation is required

CA trust
    preserve a valid SSL_CERT_FILE
    otherwise discover the Termux CA bundle
```

## 3. Repository source of truth

Git tracks:

```text
src/
scripts/
config/
docs/
experiments/
README.md
.gitignore
```

The experiment directories preserve decision provenance. The selected current implementation lives under `src/`.

## 4. Configuration model

Tracked defaults:

```text
config/defaults.env
```

Machine-specific configuration:

```text
.local/env
```

Role examples:

```text
config/workstation.env.example
config/termux.env.example
```

Scripts load defaults and local configuration themselves. Date-based environment files under `config/legacy/` are historical inputs only.

## 5. Canonical generated trees

```text
out/<target>/<profile>/
    cross-build artifacts

work/
    disposable assembly and runtime trees

results/
    bulk validation logs, venvs, and test output

dist/<target>/<profile>/
    packaged deliverables

cache/
    optional local caches
```

These trees are repo-local but untracked.

For the current target:

```text
out/aarch64-linux-android24/release/
├── bin/
│   └── python3.14
└── metadata/
    └── build-info.txt
```

The same repo-relative artifact path is used on the workstation and Termux. No cross-machine or date-specific symlink is required.

## 6. Synchronization policy

Use Git for:

```text
source
scripts
documentation
experiment history
configuration templates
```

Use rsync for:

```text
out/<target>/<profile>/
```

The source tree and generated artifact tree are independent synchronization channels.

The rsync helper does not enable deletion by default. Remote deletion is an explicit opt-in and remains scoped to the current target/profile output directory.

## 7. Workstation workflow

```sh
mkdir -p .local
cp config/workstation.env.example .local/env
$EDITOR .local/env

./scripts/build/build-launcher.sh

DRY_RUN=1 ./scripts/sync/push-out.sh
./scripts/sync/push-out.sh
```

The build script writes directly to the canonical `out/` tree.

## 8. Termux workflow

```sh
mkdir -p .local
cp config/termux.env.example .local/env
$EDITOR .local/env

./scripts/termux/prepare-runtime.sh
./scripts/test/smoke-termux.sh
```

Runtime assembly consumes:

```text
pristine runtime archive
        +
out/<target>/<profile>/bin/python3.14
        |
        v
work/termux/stage2c/runtime/prefix
```

## 9. Naming policy

Experimental names remain in `experiments/`:

```text
python-pyconfig-auto
python-s2-setenv
python-s2-linker-update
python-s2-reexec
python-s2-r2
```

The Stage 2-C build artifact uses the runtime-facing name:

```text
python3.14
```

Runtime assembly creates:

```text
python3 -> python3.14
python  -> python3
```

## 10. Stage 2-C completion condition

Before Stage 2 can be frozen, the new canonical workflow must pass end to end:

```text
workstation build
    -> canonical out artifact
    -> artifact sync
    -> Termux runtime assembly
    -> clean base runtime validation
    -> native stdlib validation
    -> HTTPS validation
    -> subprocess validation
    -> uv venv validation
    -> venv identity validation
    -> uv run validation
```

The selected R2 architecture is already validated. Stage 2-C verifies that the repository and deployment workflow preserve that behavior without manual experiment-specific wiring.
