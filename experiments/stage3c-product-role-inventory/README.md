# Stage 3-C Phase 1: Promoted Product Role Inventory

> **Status:** INVENTORY PASS, DECOMPOSITION PASS, SEMANTIC PASS, COMPONENT POLICY PASS, ISOLATED COMPOSITION PASS, RUNTIME-BASE FINAL GATES ACTIVE
> **Input:** frozen Stage 3-B promoted runtime

## Frozen source

```text
work/termux/stage3b-promoted-runtime/prefix
entries / ELF / symlinks
  3155 / 81 / 5
```

## Completed gates

### 1. Complete role inventory — PASS

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

### 2. Exact role decomposition — PASS

```sh
bash experiments/stage3c-product-role-inventory/analyze-role-inventory.sh
```

```text
machine checks             18/18
entries / ELF / symlinks   3155 / 81 / 5
role counts and bytes      exact
```

### 3. Semantic capability probes — PASS

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

Target Tk capability:

```text
_tkinter             absent
tkinter              import failure
turtle               import failure
idlelib.pyshell      SystemExit 1
Tcl interpreter      unavailable
```

### 4. Component manifest policy — PASS

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
  199 entries
  2,139,349 bytes
  not distributed until a working Tk backend exists
```

### 5. Isolated physical variants — PASS

```sh
bash experiments/stage3c-product-role-inventory/run-isolated-variant-validation.sh
```

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

Materialized variants:

```text
runtime-base          714 entries    38,759,749 bytes
runtime-development  1168 entries    43,733,124 bytes
runtime-test         2502 entries    72,236,539 bytes
runtime-supported    2956 entries    77,209,914 bytes
```

Observed behavior:

```text
runtime-base HTTPS status                 200
runtime-base uv venv                       PASS
runtime-base uv run + anyio                PASS
development extension result               42
test_json                                  PASS
```

### 6. Frozen `__phello__` reassessment — PASS

```sh
bash \
  experiments/stage3c-product-role-inventory/run-isolated-variant-capability-reassessment.sh
```

```text
machine verifier                 114/114
corrected capability probes       17/17 × 4
source mutation                       PASS
variant mutations                     PASS
```

Corrected contract:

```text
__phello__ import and frozen origin
  every variant

physical lib/python3.14/__phello__ absent
  runtime-base
  runtime-development

physical lib/python3.14/__phello__ present
  runtime-test
  runtime-supported
```

Frozen identities:

```text
canonical source
  3155 entries
  5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c

runtime-base
  714 entries
  9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE1_ROLE_INVENTORY_FIRST_RESULT.md
docs/evidence/STAGE3C_PHASE1_ROLE_DECOMPOSITION_RESULT.md
docs/evidence/STAGE3C_PHASE1_ROLE_SEMANTICS_RESULT.md
docs/evidence/STAGE3C_PHASE1_COMPONENT_POLICY_RESULT.md
docs/evidence/STAGE3C_PHASE1_ISOLATED_VARIANT_PHELLO_INCIDENT.md
docs/evidence/STAGE3C_PHASE1_PHELLO_REASSESSMENT_RESULT.md
```

## Active gate: runtime-base closure and relocation

Run:

```sh
bash \
  experiments/stage3c-product-role-inventory/run-runtime-base-final-validation.sh
```

The workflow first requires the accepted evidence chain:

```text
component policy selector                18/18
component policy verifier                34/34
phello reassessment                     114/114
component manifest
  91088a013722ad35910f049bfc45b2e61607423d833c23038c1d9645497b7b84
runtime-base strict fingerprint
  9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796
canonical strict fingerprint
  5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c
```

### Native closure contract

The Stage 3-A closure engines are reused against the 714-entry runtime-base.

```text
symlinks                               3
ELF objects                           81
DT_NEEDED edges                      329
ANDROID_SYSTEM edges                 249
RUNTIME_INTERNAL edges                80
unique needed SONAMEs                  9
system SONAME dlopen                  5/5
unresolved edges                        0
inspection errors                       0
extension imports                    67/67
```

Removing optional and development Python source does not relax the native graph.

### Relocation contract

The Stage 3-A production relocation engine and Stage 3-B 31-check verifier are reused.

```text
copy runtime-base to location A
validate runtime, HTTPS, subprocess, venv and uv-run at A
move the whole prefix A -> B
reject stale A paths at B
validate runtime, HTTPS, subprocess, venv and uv-run at B
compare complete source/B portable product manifests
require 714 / 714 entries
require no added, removed or portable-changed paths
require no pycache
```

The canonical promoted source and the runtime-base source are fingerprinted before and after both final gates.

Outputs:

```text
results/termux/stage3c-phase1-runtime-base-final-validation/
  input/
  input-verification.json
  runtime-base-input-fingerprint.json
  canonical-input-fingerprint.json
  closure/
    summary.json
    closure-analysis-summary.json
    system-soname-probe-summary.json
    extension-import-probe-summary.json
    runtime-base-closure-verification.json
  relocation/
    reconfirm/reconfirm.log
    fidelity-diagnosis/tree-delta.json
    promoted-relocation-verification.json
    runtime-base-relocation-verification.json
  workflow-status.json
  verification.json
```

Expected markers:

```text
RUNTIME_BASE_FINAL_INPUT_CONTRACT=PASS
RUNTIME_BASE_NATIVE_CLOSURE=PASS
RUNTIME_BASE_EXTENSION_IMPORTS=67/67 PASS
RUNTIME_BASE_RELOCATION_ENGINE=31/31 PASS
RUNTIME_BASE_RELOCATION_PORTABLE_FIDELITY=PASS
RUNTIME_BASE_SOURCE_MUTATION_CHECK=PASS
CANONICAL_SOURCE_MUTATION_CHECK=PASS
STAGE3C_PHASE1_RUNTIME_BASE_FINAL_VALIDATION=PASS
```

## Result archive

Upload the complete result directory as one distinguishable TGZ:

```sh
RESULTS="$PWD/results/termux/stage3c-phase1-runtime-base-final-validation"
ARCHIVE="$HOME/Downloads/stage3c-phase1-runtime-base-final-validation-results-$(date +%Y%m%d-%H%M%S).tgz"

tar czf "$ARCHIVE" "$RESULTS"
printf 'upload: %s\n' "$ARCHIVE"
```

## Claim boundary

A PASS proves that the selected split runtime retains the frozen native closure, imports all 67 extensions, and remains production-correct after a whole-prefix move with exact portable fidelity.

It does not yet freeze archive compression, archive byte reproducibility, extraction ownership/permissions, installer transaction behavior, or rollback semantics. Those belong to the next Stage 3-C phase.
