# Stage 2-C Design: Synthesis and Project Workflow

> **Status:** COMPLETE / FROZEN
> **Result:** PASS
> **Input:** Stage 2-B R2 validation and relocation success
> **Target:** Termux on Android arm64
> **Python:** CPython 3.14.6
> **Freeze document:** `docs/stages/STAGE2_FINAL.md`

## 1. Purpose

Stage 2-C turned the validated Stage 2-B R2 experiment into a production-shaped project workflow.

The stage had two goals:

1. preserve the behavior validated in Stage 2-B while reducing experimental naming and manual file wiring;
2. establish one repository-wide path model for source, build artifacts, runtime assembly, test results, and workstation-to-Termux synchronization.

Stage 2-C was a synthesis stage, not a new bootstrap-strategy experiment.

The end-to-end workflow passed and Stage 2 is now frozen.

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

Two artifact-transport initiators are supported:

```text
workstation-initiated push:
  scripts/sync/push-out.sh

Termux-initiated pull:
  scripts/sync/pull-out.sh
```

The successful Stage 2-C test used Termux-initiated pull because Termux inbound connectivity was unavailable.

Deletion is opt-in in both directions and remains scoped to the current target/profile output tree.

## 7. Workstation workflow

```sh
mkdir -p .local
cp config/workstation.env.example .local/env
$EDITOR .local/env

bash scripts/build/build-launcher.sh
```

The build script writes directly to the canonical `out/` tree.

Optional push topology:

```sh
DRY_RUN=1 bash scripts/sync/push-out.sh
bash scripts/sync/push-out.sh
```

## 8. Termux workflow

```sh
mkdir -p .local
cp config/termux.env.example .local/env
$EDITOR .local/env
```

For the tested pull topology:

```sh
DRY_RUN=1 bash scripts/sync/pull-out.sh
bash scripts/sync/pull-out.sh
```

Then:

```sh
bash scripts/termux/prepare-runtime.sh
bash scripts/test/smoke-termux.sh
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

## 10. Completion result

The canonical workflow passed end to end:

```text
workstation build                              PASS
canonical out artifact                        PASS
artifact transport                            PASS
Termux runtime assembly                       PASS
clean base runtime validation                 PASS
native stdlib validation                      PASS
HTTPS validation                              PASS
subprocess validation                         PASS
uv venv validation                            PASS
venv identity validation                      PASS
uv run validation                             PASS
final STAGE2C_SMOKE marker                     PASS
```

The selected R2 architecture survived the cleaned repository and deployment workflow without manual experiment-specific wiring.

Therefore:

```text
Stage 2-C: PASS
Stage 2: FROZEN
```

See:

```text
docs/stages/STAGE2_FINAL.md
docs/evidence/STAGE2C_E2E_SMOKE_SUMMARY.md
```
