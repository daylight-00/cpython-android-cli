# Stage 3-C Phase 1: Promoted Product Role Inventory

> **Status:** INVENTORY PASS, DECOMPOSITION PASS, SEMANTIC PASS, COMPONENT POLICY PASS, ISOLATED VARIANTS ACTIVE
> **Input:** frozen Stage 3-B promoted runtime

## Frozen input

```text
work/termux/stage3b-promoted-runtime/prefix
entries / ELF / symlinks
  3155 / 81 / 5
```

## Step 1: complete role inventory — PASS

```sh
bash experiments/stage3c-product-role-inventory/run-role-inventory.sh
```

```text
UNKNOWN                         0
machine verifier            43/43
source mutation              PASS
role manifest
  092ea87eed2a3c800053a0ef480abd8ef836bda8a8890549ce84370eae6e2a0f
```

## Step 2: exact role decomposition — PASS

```sh
bash experiments/stage3c-product-role-inventory/analyze-role-inventory.sh
```

```text
machine checks             18/18
entries / ELF / symlinks   3155 / 81 / 5
role counts and bytes      exact
```

## Step 3: semantic capability probes — PASS

```sh
bash experiments/stage3c-product-role-inventory/run-role-semantic-probes.sh
```

```text
machine verifier                     38/38
source mutation                       PASS
venv / ensurepip                      PASS
test / test.support                   PASS
sysconfig runtime service             PASS
active sysconfig paths under prefix   PASS
_sysconfigdata import                 PASS
build-details parse                   PASS
```

Tk-dependent target capability:

```text
_tkinter             absent
tkinter              import failure
turtle               import failure
idlelib.pyshell      SystemExit 1
Tcl interpreter      unavailable
```

The Tk/IDLE/turtle source is present but not a working target capability.

## Step 4: component manifest policy — PASS

```sh
bash experiments/stage3c-product-role-inventory/run-component-policy.sh
```

```text
input contract                27/27
policy selector               18/18
independent verifier          34/34
source mutation               PASS
component manifest
  91088a013722ad35910f049bfc45b2e61607423d833c23038c1d9645497b7b84
```

Selected components:

```text
RUNTIME_BASE
RUNTIME_METADATA
DEVELOPMENT
DEVELOPMENT_METADATA
OPTIONAL_TEST_SUITE
OPTIONAL_TEST_DEMO
UNSUPPORTED_GUI_SOURCE
LICENSE
```

Selected artifact candidates:

```text
runtime-base
  RUNTIME_BASE + RUNTIME_METADATA + LICENSE
  714 entries
  38,759,749 bytes

development-addon
  DEVELOPMENT + DEVELOPMENT_METADATA
  454 entries
  4,973,375 bytes

test-addon
  OPTIONAL_TEST_SUITE + OPTIONAL_TEST_DEMO
  1788 entries
  33,476,790 bytes

unsupported-gui-source
  UNSUPPORTED_GUI_SOURCE
  199 entries
  2,139,349 bytes
  not distributed until a working Tk backend exists
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE1_ROLE_INVENTORY_FIRST_RESULT.md
docs/evidence/STAGE3C_PHASE1_ROLE_DECOMPOSITION_RESULT.md
docs/evidence/STAGE3C_PHASE1_ROLE_SEMANTICS_RESULT.md
docs/evidence/STAGE3C_PHASE1_COMPONENT_POLICY_RESULT.md
```

## Step 5: isolated variant materialization — ACTIVE

This step creates disposable trees from the accepted component manifest. The canonical promoted tree remains read-only.

```sh
bash experiments/stage3c-product-role-inventory/run-isolated-variant-validation.sh
```

Materialized variants:

```text
runtime-base
  714 entries

runtime-development
  runtime-base + development-addon
  1168 entries

runtime-test
  runtime-base + test-addon
  2502 entries

runtime-supported
  runtime-base + development-addon + test-addon
  2956 entries
```

No `UNSUPPORTED_GUI_SOURCE` row is copied.

The workflow validates:

```text
accepted component manifest identity
ancestor-closed exact path selection
path/type/mode/mtime/file-hash/symlink fidelity
all 81 ELF entries retained in every variant
variant-specific positive and negative import matrix
runtime metadata present in every variant
development metadata absent/present exactly by variant
Tk/IDLE/turtle source absent in every distributed variant
runtime-base production smoke with HTTPS and uv/venv
development-addon real C extension compile and import
test-addon representative test_json regression run
variant strict fingerprints unchanged after validation
canonical source strict fingerprint unchanged
```

The development probe compiles a real extension against the isolated headers and `libpython3.14.so`, then imports it with `runtime-development`.

The test probe executes:

```text
python -I -B -m test -j1 test_json
```

Outputs:

```text
work/termux/stage3c-phase1-isolated-variants/
  runtime-base/prefix
  runtime-development/prefix
  runtime-test/prefix
  runtime-supported/prefix

results/termux/stage3c-phase1-isolated-variants/
  materialization.json
  variant-fidelity-before.json
  variant-fidelity-after.json
  capabilities/*.json
  fingerprints/*.json
  runtime-base-smoke.log
  development-extension.log
  test-addon.log
  workflow-status.json
  verification.json
```

Expected markers:

```text
STAGE3C_PHASE1_VARIANT_MATERIALIZATION=PASS
STAGE3C_PHASE1_VARIANT_FIDELITY=PASS
STAGE3C_PHASE1_VARIANT_CAPABILITY[runtime-base]=PASS
STAGE3C_PHASE1_VARIANT_CAPABILITY[runtime-development]=PASS
STAGE3C_PHASE1_VARIANT_CAPABILITY[runtime-test]=PASS
STAGE3C_PHASE1_VARIANT_CAPABILITY[runtime-supported]=PASS
RUNTIME_BASE_SMOKE=PASS
DEVELOPMENT_ADDON_NATIVE_EXTENSION=PASS
TEST_ADDON_REPRESENTATIVE_TEST=PASS
ISOLATED_VARIANT_SOURCE_MUTATION_CHECK=PASS
STAGE3C_PHASE1_ISOLATED_VARIANTS=PASS
```

## Non-mutation contract

All Python probes run with explicit bytecode suppression. Every materialized variant and the canonical source are fingerprinted before and after behavior validation.

The first isolated gate does not modify the canonical promoted tree and does not yet freeze archive bytes.

## Claim boundary

A PASS proves exact isolated materialization plus selected runtime, development, and test behavior.

It does not yet prove that `runtime-base` preserves the frozen native closure or production-shape whole-prefix relocation. Those are the next Phase 1 gates before the component split is frozen.
