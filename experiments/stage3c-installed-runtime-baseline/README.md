# Stage 3-C Phase 5 Gate 1: Installed Runtime Baseline

> **Status:** ACTIVE — corrected authoritative Termux rerun pending
> **Input:** frozen Stage 3-C Phase 4 integrated durability result

## Preserved first target failure

The first target run completed installation, runtime, HTTPS, uv, and native-closure validation but failed two of the 80 independent checks:

```text
phase4_result_index_exact
installed_fingerprint_exact
```

The failure is preserved in:

```text
docs/evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_BASELINE_FAILURE.md
```

The exact accepted Phase 4 result-index gate remains unchanged. The invalid source-tree-to-installed-tree strict fingerprint comparison is replaced by a portable payload identity while the strict before/after mutation control remains mandatory.

## Accepted Phase 4 input

The corrected rerun must consume a fresh extraction of the accepted Phase 4 TGZ:

```text
stage3c-phase4-integrated-durability-results-20260712-082135.tgz

sha256
  76bb78f200d9836d96f677cc1eca1e2f1483186f3655efa17a8e1f2361bd0187

result-index sha256
  878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce
```

The workflow now verifies the root Phase 4 result-index before installation and fails early with `rc=62` when the input directory is not the accepted frozen evidence.

## Corrected run

```sh
PHASE4_ARCHIVE="$HOME/Downloads/stage3c-phase4-integrated-durability-results-20260712-082135.tgz"
PHASE4_EXTRACT="$PREFIX/tmp/stage3c-phase4-integrated-durability-accepted"

printf '%s  %s\n' \
  '76bb78f200d9836d96f677cc1eca1e2f1483186f3655efa17a8e1f2361bd0187' \
  "$PHASE4_ARCHIVE" | sha256sum -c -

rm -rf "$PHASE4_EXTRACT"
mkdir -p "$PHASE4_EXTRACT"
tar xzf "$PHASE4_ARCHIVE" -C "$PHASE4_EXTRACT"

PHASE4_RESULTS="$(find "$PHASE4_EXTRACT" \
  -type d \
  -path '*/results/termux/stage3c-phase4-integrated-durability' \
  -print -quit)"

test -n "$PHASE4_RESULTS"

PHASE4_RESULTS="$PHASE4_RESULTS" \
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

## Installed payload identities

The source-tree runtime fingerprint remains a frozen manifest compatibility identity:

```text
9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796
```

It is not compared directly with an installed strict fingerprint because strict fingerprints contain filesystem-specific directory size and timestamp metadata.

Installed portable identity uses only:

```text
relative path
entry type
mode
regular-file size and SHA-256
symlink target
```

Expected portable identity:

```text
kind
  stage3c-installed-payload-portable-v1

fingerprint
  f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978

entries
  714

regular / directory / symlink / special
  654 / 57 / 3 / 0
```

Metadata-sensitive strict fingerprints are still captured before and after all runtime probes. They must remain identical.

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
Phase 4 input before/after     exact
installed strict before/after  exact
installed portable identity    exact
installed prefix entries       714/714
installed pycache paths        0
installed special paths        0
```

Smoke execution receives an external `PYTHONPYCACHEPREFIX` so validation cannot write bytecode into the installed prefix.

## Verifier

```text
80/80 checks
```

It independently checks the accepted frozen Phase 4 evidence, manifest-to-registry equality, installed portable payload identity, strict before/after immutability, runtime probes, smoke markers, uv probes, native closure, extension imports, canonical generated JSON, and both mutation controls.

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
ARCHIVE="$HOME/Downloads/stage3c-phase5-installed-runtime-baseline-portable-fingerprint-corrected-results-$(date +%Y%m%d-%H%M%S).tgz"

tar czf "$ARCHIVE" "$RESULTS"
printf 'upload: %s\n' "$ARCHIVE"
```

## Claim boundary

A PASS proves exact runtime-base registry and portable payload identity plus runtime behavior on the original installed path after installation through the frozen Phase 4 engine. Relocation, later repair and reinstall behavior, exact uninstall preservation, upgrade, and downgrade remain separate gates.
