# Stage 3-C Phase 1 Scope: Promoted Product Role Inventory

> **Status:** ACTIVE — isolated composition PASS, runtime-base closure and relocation pending
> **Input:** frozen Stage 3-B promoted runtime
> **Execution host:** Termux on Android arm64

## Frozen source

```text
work/termux/stage3b-promoted-runtime/prefix
entries / ELF / symlinks
  3155 / 81 / 5
```

Frozen Stage 3-B properties:

```text
unresolved native edges                0
extension imports                   67/67
promoted relocation verifier        31/31
candidate mutation control           PASS
```

The canonical promoted tree remains read-only throughout Phase 1.

## Completed gates

```text
role inventory                       43/43 PASS
UNKNOWN                                   0
role decomposition                   18/18 PASS
semantic capability                  38/38 PASS
component-policy input               27/27 PASS
component-policy selector            18/18 PASS
component-policy verifier            34/34 PASS
isolated materialization               7/7 PASS
isolated fidelity before/after      15/15 PASS
runtime-base production smoke              PASS
development extension compile/import       PASS
test-addon test_json                         PASS
frozen phello reassessment          114/114 PASS
corrected variant capabilities       17/17 × 4
canonical and variant mutations             PASS
```

Accepted manifests and identities:

```text
role manifest
  092ea87eed2a3c800053a0ef480abd8ef836bda8a8890549ce84370eae6e2a0f

component manifest
  91088a013722ad35910f049bfc45b2e61607423d833c23038c1d9645497b7b84

canonical source fingerprint
  5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c

runtime-base fingerprint
  9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796
```

## Selected component contract

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

Selected distributable candidates:

```text
runtime-base
  RUNTIME_BASE + RUNTIME_METADATA + LICENSE
  714 entries
  38,759,749 regular-file bytes

development-addon
  DEVELOPMENT + DEVELOPMENT_METADATA
  454 entries
  4,973,375 regular-file bytes

test-addon
  OPTIONAL_TEST_SUITE + OPTIONAL_TEST_DEMO
  1788 entries
  33,476,790 regular-file bytes
```

Unsupported GUI source remains non-distributed until a working `_tkinter`/Tcl/Tk backend exists.

## Frozen `__phello__` contract

```text
import + frozen origin
  every isolated variant

physical source root absent
  runtime-base
  runtime-development

physical source root present
  runtime-test
  runtime-supported
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE1_ISOLATED_VARIANT_PHELLO_INCIDENT.md
docs/evidence/STAGE3C_PHASE1_PHELLO_REASSESSMENT_RESULT.md
```

## Active final gate

Question:

> Does the exact 714-entry runtime-base preserve the frozen native closure and remain production-correct after a whole-prefix relocation without modifying either runtime-base or the canonical promoted source?

Run:

```sh
bash \
  experiments/stage3c-product-role-inventory/run-runtime-base-final-validation.sh
```

### Input gate

The workflow requires:

```text
component-policy selector             18/18
component-policy verifier             34/34
phello reassessment                  114/114
runtime-base entries                     714
canonical entries                       3155
current fingerprints equal accepted identities
no pycache or special files
```

### Native closure gate

The Stage 3-A inventory and probe engines are reused with no relaxed native expectations.

```text
runtime-base symlinks                      3
ELF objects                               81
DT_NEEDED edges                          329
ANDROID_SYSTEM edges                     249
RUNTIME_INTERNAL edges                    80
unique needed SONAMEs                      9
ANDROID_SYSTEM SONAME dlopen             5/5
unresolved edges                            0
inspection errors                           0
extension candidates/imports            67/67
```

The runtime identity must resolve entirely under the runtime-base prefix, including executable, prefix/base_prefix, stdlib, lib-dynload, sysconfig paths and loader-library path.

### Whole-prefix relocation gate

The Stage 3-A relocation engine is reused:

```text
source runtime-base -> location A
validate A
move whole prefix A -> B
validate B
reject stale A paths
validate HTTPS, subprocess, uv venv and uv run
```

The Stage 3-B 31-check relocation verifier is reused unchanged, then wrapped by Stage 3-C checks requiring:

```text
source and relocated entries       714 / 714
portable added paths                       0
portable removed paths                     0
portable changed paths                     0
pycache paths                               0
portable fingerprints                   equal
runtime-base source fingerprint       unchanged
canonical source fingerprint          unchanged
```

## Implementation

```text
experiments/stage3c-product-role-inventory/
  verify-runtime-base-final-inputs.py
  verify-runtime-base-closure.py
  verify-runtime-base-relocation.py
  verify-runtime-base-final-validation.py
  run-runtime-base-final-validation.sh
```

The workflow calls the existing engines:

```text
experiments/stage3a-runtime-closure/inventory-runtime.sh
experiments/stage3a-runtime-closure/analyze-and-probe.sh
experiments/stage3a-runtime-closure/probe-extension-imports.sh
experiments/stage3a-runtime-closure/reconfirm-production-relocation.sh
experiments/stage3b-target-validation/diagnose-promoted-relocation-fidelity.py
experiments/stage3b-target-validation/verify-promoted-relocation.py
```

## Outputs

```text
results/termux/stage3c-phase1-runtime-base-final-validation/
  input/
  input-verification.json
  runtime-base-input-fingerprint.json
  canonical-input-fingerprint.json
  closure/
  relocation/
  workflow-status.json
  verification.json
```

## Expected markers

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

```sh
RESULTS="$PWD/results/termux/stage3c-phase1-runtime-base-final-validation"
ARCHIVE="$HOME/Downloads/stage3c-phase1-runtime-base-final-validation-results-$(date +%Y%m%d-%H%M%S).tgz"

tar czf "$ARCHIVE" "$RESULTS"
printf 'upload: %s\n' "$ARCHIVE"
```

## Acceptance conditions

```text
[x] role inventory 43/43
[x] UNKNOWN = 0
[x] role decomposition 18/18
[x] semantic capability 38/38
[x] component policy 27/27 + 18/18 + 34/34
[x] isolated physical composition gates
[x] frozen phello reassessment 114/114
[ ] final input contract passes
[ ] runtime-base native graph matches 81 / 329 / 249+80
[ ] unresolved and inspection errors remain zero
[ ] all 67 extension imports pass
[ ] runtime-base and canonical source remain unchanged during closure
[ ] Stage 3-B relocation engine passes 31/31
[ ] source/B portable product fidelity passes at 714 / 714
[ ] runtime-base and canonical source remain unchanged during relocation
[ ] aggregate final verifier passes
```

## Claim boundary

A final PASS proves the split runtime-base itself is a valid portable product surface.

It does not freeze archive bytes, compression parameters, extraction ownership and permission policy, installation transactions, upgrade behavior, rollback, or uninstall semantics. Those belong to subsequent Stage 3-C phases.
