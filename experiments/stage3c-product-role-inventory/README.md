# Stage 3-C Phase 1: Promoted Product Role Inventory

> **Status:** INVENTORY PASS, DECOMPOSITION PASS, SEMANTIC PASS, COMPONENT POLICY PASS, ISOLATED PHYSICAL GATES PASS, PHELLO REASSESSMENT ACTIVE
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

## Step 5: isolated variant materialization — PHYSICAL GATES PASS

```sh
bash experiments/stage3c-product-role-inventory/run-isolated-variant-validation.sh
```

Materialized variants:

```text
runtime-base          714 entries    38,759,749 bytes
runtime-development  1168 entries    43,733,124 bytes
runtime-test         2502 entries    72,236,539 bytes
runtime-supported    2956 entries    77,209,914 bytes
```

No `UNSUPPORTED_GUI_SOURCE` row was copied.

First-run retained result:

```text
materialization                      7/7 PASS
initial exact-path fidelity         15/15 PASS
final exact-path fidelity           15/15 PASS
runtime-base production smoke             PASS
development extension compile/import      PASS
test-addon representative test            PASS
canonical source mutation control         PASS
all four variant mutation controls        PASS
```

Observed behavior:

```text
runtime-base HTTPS status                 200
runtime-base uv venv                       PASS
runtime-base uv run + anyio                PASS
development extension result               42
test_json                                  PASS
```

Canonical source before/after:

```text
entries
  3155 / 3155

fingerprint
  5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c
```

Variant strict fingerprints:

```text
runtime-base
  9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796

runtime-development
  c310052378f2ab40041c8ed599c301fbe6778c139665496ddb9f8b8a9ec947c6

runtime-test
  da1627557907b417bea4b0175e431c746a450dbfa8f31698077853328a54835e

runtime-supported
  ea5930b2b0c0266b28efa0a66fb70267f8ecafe5c62a5c29c61f26cc05c20a64
```

Every before/after pair was equal.

### First-run capability false negative

The aggregate verifier reported:

```text
checks             46
failed checks       3
pass             false
```

Exact failed checks:

```text
runtime-base_capability_pass
runtime-development_capability_pass
workflow_status_pass
```

The only underlying capability mismatch was `__phello__`.

```text
runtime-base
  physical OPTIONAL_TEST_DEMO absent
  __phello__ import succeeds
  spec origin = frozen

runtime-development
  physical OPTIONAL_TEST_DEMO absent
  __phello__ import succeeds
  spec origin = frozen
```

`__phello__` is frozen into this CPython. Importability is therefore independent of physical `lib/python3.14/__phello__` ownership. The synthetic module `__file__` path must not be treated as proof that the physical source directory exists.

The corrected contract is:

```text
__phello__ import succeeds with frozen origin in every variant

physical lib/python3.14/__phello__ absent
  runtime-base
  runtime-development

physical lib/python3.14/__phello__ present
  runtime-test
  runtime-supported
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE1_ISOLATED_VARIANT_PHELLO_INCIDENT.md
```

## Step 6: targeted frozen-module reassessment — ACTIVE

The first-run result is retained unchanged. This workflow does not rematerialize variants or rerun smoke, compilation, or regression tests.

```sh
bash \
  experiments/stage3c-product-role-inventory/run-isolated-variant-capability-reassessment.sh
```

It validates:

```text
first-run failure set exactly preserved
all first-run non-capability return codes remain zero
materialization 7/7 retained
fidelity before/after 15/15 retained
current source and variant fingerprints equal first-run identities
corrected capability schema 2 and 17/17 per variant
__phello__ import and frozen origin in every variant
physical __phello__ root follows test-addon ownership
source and variant fingerprints unchanged by reassessment
```

Outputs:

```text
results/termux/stage3c-phase1-isolated-variant-capability-reassessment/
  source-before.json
  source-after.json
  capabilities/*.json
  fingerprints/*.json
  reassessment-status.json
  verification.json
  verifier.log
```

Expected markers:

```text
FIRST_RUN_FAILURE_PRESERVED=PASS
PHELLO_FROZEN_CONTRACT_CORRECTED=PASS
ISOLATED_VARIANT_CAPABILITIES_REASSESSED=PASS
ISOLATED_VARIANT_REASSESSMENT_MUTATION_CHECK=PASS
STAGE3C_PHASE1_PHELLO_REASSESSMENT=PASS
```

## Non-mutation contract

All Python probes run with explicit bytecode suppression. The canonical source and every isolated variant are fingerprinted before and after the targeted reassessment.

The original failed output remains evidence and is never rewritten into a synthetic PASS.

## Claim boundary

A corrected reassessment PASS closes only the frozen-module semantic false negative and completes the isolated physical-composition gate.

It does not yet prove that `runtime-base` preserves the frozen native closure or production-shape whole-prefix relocation. Those remain the next Phase 1 gates before the component split is frozen.
