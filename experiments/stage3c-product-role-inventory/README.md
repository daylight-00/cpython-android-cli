# Stage 3-C Phase 1: Promoted Product Role Inventory

> **Status:** INVENTORY PASS, DECOMPOSITION PASS, SEMANTIC PROBE PASS, COMPONENT POLICY ACTIVE
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

Evidence:

```text
docs/evidence/STAGE3C_PHASE1_ROLE_INVENTORY_FIRST_RESULT.md
```

## Step 2: exact role decomposition — PASS

```sh
bash experiments/stage3c-product-role-inventory/analyze-role-inventory.sh
```

```text
machine checks             18/18
entries / ELF / symlinks   3155 / 81 / 5
role counts and bytes      exact
unmatched optional         0
```

Optional decomposition:

```text
lib/python3.14/test          1785 entries   33,476,596 bytes
lib/python3.14/idlelib        161 entries    1,624,586 bytes
lib/python3.14/tkinter         14 entries      303,444 bytes
lib/python3.14/turtledemo      23 entries       61,800 bytes
lib/python3.14/__phello__       3 entries          194 bytes
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE1_ROLE_DECOMPOSITION_RESULT.md
```

## Step 3: semantic capability probes — PASS

```sh
bash experiments/stage3c-product-role-inventory/run-role-semantic-probes.sh
```

```text
machine verifier                     38/38
source mutation                       PASS
venv                                  PASS
test / test.support                   PASS
ensurepip                             PASS observation
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

The pure-Python Tk/IDLE/turtle source exists, but the target has no working `_tkinter` backend. It is therefore classified as unsupported source rather than a working runtime capability.

Evidence:

```text
docs/evidence/STAGE3C_PHASE1_ROLE_SEMANTICS_RESULT.md
```

## Step 4: component manifest policy — ACTIVE

This step does not copy or remove product files. It assigns every accepted path exactly once to a candidate product component.

```sh
bash experiments/stage3c-product-role-inventory/run-component-policy.sh
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

Selected candidate artifact compositions:

```text
runtime-base
  RUNTIME_BASE + RUNTIME_METADATA + LICENSE

development-addon
  DEVELOPMENT + DEVELOPMENT_METADATA

test-addon
  OPTIONAL_TEST_SUITE + OPTIONAL_TEST_DEMO

unsupported-gui-source
  UNSUPPORTED_GUI_SOURCE
  not distributed until a working Tk backend exists
```

Metadata split:

```text
RUNTIME_METADATA
  _sysconfigdata__android_aarch64-linux-android.py
  _sysconfig_vars__android_aarch64-linux-android.json
  build-details.json

DEVELOPMENT_METADATA
  config-*/Makefile
  config-*/Setup
  config-*/Setup.local
  config-*/config.c
  config-*/python-config.py
```

The selector pins the accepted role manifest and the accepted 38/38 semantic evidence. The independent verifier re-derives the path-to-component mapping and checks exact counts, bytes, ELF ownership, symlinks, anchors, path lists, and artifact composition.

Outputs:

```text
results/termux/stage3c-phase1-component-policy/
  component-inventory.tsv
  component-summary.tsv
  component-policy.json
  component-policy-verification.json
  artifact-composition.json
  paths/*.txt
  selector.log
  verifier.log
```

Expected markers:

```text
STAGE3C_PHASE1_COMPONENT_POLICY=PASS
COMPONENT_POLICY_COMPLETE_PARTITION=PASS
COMPONENT_POLICY_SOURCE_MUTATION_CHECK=PASS
STAGE3C_PHASE1_COMPONENT_POLICY_WORKFLOW=PASS
```

## Non-mutation contract

All probes and policy generators run under promoted Python with:

```text
python -I -B -S
```

The accepted source inventory and semantic evidence are read-only. Physical payload variants are not created until the component policy passes independently.

## Claim boundary

Current evidence proves complete classification, exact decomposition, target semantic capability, and a candidate component policy.

It does not yet prove that the candidate `runtime-base`, `development-addon`, or `test-addon` passes after physical materialization. That requires isolated-copy smoke, uv/venv, sysconfig, native closure, relocation, and addon composition validation.
