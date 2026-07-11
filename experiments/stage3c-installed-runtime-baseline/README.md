# Stage 3-C Phase 5 Gate 1: Installed Runtime Baseline

> **Status:** ACTIVE — authoritative Termux result pending
> **Input:** frozen Stage 3-C Phase 4 integrated durability result

## Run

```sh
bash experiments/stage3c-installed-runtime-baseline/run-installed-runtime-baseline.sh
```

## Product path under test

```text
frozen runtime-base archive
  → frozen integrated Phase 4 installer
  → fresh installation root/prefix
  → runtime, HTTPS, uv, closure, and extension validation
```

The test does not use the Stage 3-B promoted prefix or Phase 1 isolated prefix as the runtime under test. The promoted prefix is used only as an immutable tool Python.

## Installation checks

```text
create actions            714
registry mutation count   715
engine verify             PASS
registry artifacts          1
registry owned rows       714
manifest mapping          exact
```

## Runtime checks

```text
version                    3.14.6
platform                   android
machine                    aarch64
SOABI                      cpython-314-aarch64-linux-android
MULTIARCH                  aarch64-linux-android
HTTPS status               200
subprocess identity        installed prefix
```

## uv checks

The frozen Stage 2-C smoke workflow is rerun from the installed prefix:

```text
uv venv                    PASS
venv base_prefix           installed prefix
uv run --with anyio        PASS
uv run base_prefix         installed prefix
```

Generated venv and redirected bytecode caches are removed after machine probes. They are not part of the installed prefix or final evidence archive.

## Native closure checks

```text
symlinks                       3
ELF objects                   81
DT_NEEDED edges              329
RUNTIME_INTERNAL edges        80
ANDROID_SYSTEM edges         249
unresolved edges               0
inspection errors              0
system SONAME dlopen          5/5
extension imports            67/67
```

## Mutation controls

```text
Phase 4 input before/after   exact
installed prefix entries     714/714
installed fingerprint        exact
installed pycache paths      0
installed special paths      0
```

Smoke execution receives an external `PYTHONPYCACHEPREFIX` so validation cannot write bytecode into the installed prefix.

## Verifier

```text
80/80 checks
```

It independently checks the frozen Phase 4 evidence, manifest-to-registry equality, installed tree identity, runtime probes, smoke markers, uv probes, native closure, extension imports, canonical generated JSON, and both mutation controls.

## Expected markers

```text
INSTALLED_RUNTIME_BASELINE_ACCEPTED_INPUTS=PASS
INSTALLED_RUNTIME_BASELINE_INSTALL=714/714 PASS
INSTALLED_RUNTIME_BASELINE_REGISTRY=714/714 PASS
INSTALLED_RUNTIME_BASELINE_SMOKE=PASS
INSTALLED_RUNTIME_BASELINE_HTTPS=200 PASS
INSTALLED_RUNTIME_BASELINE_UV_VENV=PASS
INSTALLED_RUNTIME_BASELINE_UV_RUN=PASS
INSTALLED_RUNTIME_BASELINE_NATIVE_CLOSURE=81/329/0 PASS
INSTALLED_RUNTIME_BASELINE_EXTENSION_IMPORTS=67/67 PASS
INSTALLED_RUNTIME_BASELINE_VERIFICATION=80/80 PASS
INSTALLED_RUNTIME_BASELINE_MUTATION_CHECK=PASS
STAGE3C_PHASE5_INSTALLED_RUNTIME_BASELINE=PASS
```

## Results

```text
results/termux/stage3c-phase5-installed-runtime-baseline/
```

## Upload

```sh
RESULTS="$PWD/results/termux/stage3c-phase5-installed-runtime-baseline"
ARCHIVE="$HOME/Downloads/stage3c-phase5-installed-runtime-baseline-results-$(date +%Y%m%d-%H%M%S).tgz"

tar czf "$ARCHIVE" "$RESULTS"
printf 'upload: %s\n' "$ARCHIVE"
```

## Claim boundary

A PASS proves exact runtime-base identity and behavior on the original installed path after installation through the frozen Phase 4 engine. Relocation, later repair and reinstall behavior, exact uninstall preservation, upgrade, and downgrade remain separate gates.
