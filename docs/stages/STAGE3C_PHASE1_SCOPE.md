# Stage 3-C Phase 1 Scope: Promoted Product Role Inventory

> **Status:** ACTIVE — physical variant gates PASS, frozen `__phello__` reassessment pending
> **Input:** frozen Stage 3-B promoted runtime
> **Execution host:** Termux on Android arm64

## Frozen input

```text
work/termux/stage3b-promoted-runtime/prefix
entries / ELF / symlinks
  3155 / 81 / 5
```

Frozen runtime properties:

```text
unresolved native edges                0
extension imports                   67/67
promoted relocation verifier        31/31
candidate mutation control           PASS
```

The canonical promoted tree is read-only throughout Phase 1.

## Completed gates

### Complete role inventory — PASS

```text
UNKNOWN                                0
machine verifier                    43/43
source mutation                      PASS
role manifest
  092ea87eed2a3c800053a0ef480abd8ef836bda8a8890549ce84370eae6e2a0f
```

### Exact role decomposition — PASS

```text
machine checks                      18/18
role/type/path/byte totals           exact
```

### Semantic capability probe — PASS

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

### Component manifest policy — PASS

```text
input contract                      27/27
policy selector                     18/18
independent verifier                34/34
source mutation                      PASS
component manifest
  91088a013722ad35910f049bfc45b2e61607423d833c23038c1d9645497b7b84
```

Complete component partition:

```text
component                  entries     regular bytes     ELF
RUNTIME_BASE                   710        38,625,987       81
RUNTIME_METADATA                 3           119,958        0
DEVELOPMENT                    449         4,737,164        0
DEVELOPMENT_METADATA             5           236,211        0
OPTIONAL_TEST_SUITE           1785        33,476,596        0
OPTIONAL_TEST_DEMO               3               194        0
UNSUPPORTED_GUI_SOURCE         199         2,139,349        0
LICENSE                          1            13,804        0
```

### Isolated physical variants — PASS

First-run physical results:

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

No `UNSUPPORTED_GUI_SOURCE` row was copied.

Runtime and addon observations:

```text
runtime-base HTTPS status                 200
runtime-base uv venv                       PASS
runtime-base uv run + anyio                PASS
development C extension result              42
test_json                                  PASS
```

Canonical source identity remained:

```text
entries
  3155

fingerprint
  5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c
```

## Retained first-run incident

The aggregate first-run verifier reported:

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

All non-capability workflow return codes were zero. The two capability failures each contained only:

```text
module_expectations_match
```

The differing module expectation was `__phello__`.

Observed in `runtime-base` and `runtime-development`:

```text
physical OPTIONAL_TEST_DEMO rows absent
__phello__ import succeeds
__phello__ spec origin = frozen
```

`__phello__` is compiled into this CPython as a frozen package. Its importability does not prove that physical `lib/python3.14/__phello__` rows are present.

The first probe incorrectly equated frozen importability with optional physical-source ownership.

Evidence:

```text
docs/evidence/STAGE3C_PHASE1_ISOLATED_VARIANT_PHELLO_INCIDENT.md
```

## Active gate: targeted frozen-module reassessment

Question:

> Does the isolated capability matrix pass when frozen `__phello__` importability and physical test-addon ownership are treated as separate contracts, while all first-run physical evidence and tree identities are preserved?

Run:

```sh
bash \
  experiments/stage3c-product-role-inventory/run-isolated-variant-capability-reassessment.sh
```

Corrected capability contract:

```text
__phello__ import succeeds in every variant
__phello__ spec origin is frozen in every variant

physical lib/python3.14/__phello__ absent
  runtime-base
  runtime-development

physical lib/python3.14/__phello__ present
  runtime-test
  runtime-supported
```

The targeted workflow does not rematerialize variants and does not overwrite the first-run results. It requires:

```text
first-run failed-check set exact
first-run capability return code exactly 16
all first-run non-capability return codes zero
materialization 7/7 retained
fidelity before/after 15/15 retained
current source and variant fingerprints equal first-run identities
corrected capabilities schema 2 and 17/17 for all variants
physical __phello__ root state follows test-addon ownership
source and variant fingerprints unchanged by reassessment
```

Expected outputs:

```text
results/termux/stage3c-phase1-isolated-variant-capability-reassessment/
  source-before.json
  source-after.json
  capabilities/*.json
  fingerprints/*.json
  reassessment-status.json
  verification.json
```

Expected markers:

```text
FIRST_RUN_FAILURE_PRESERVED=PASS
PHELLO_FROZEN_CONTRACT_CORRECTED=PASS
ISOLATED_VARIANT_CAPABILITIES_REASSESSED=PASS
ISOLATED_VARIANT_REASSESSMENT_MUTATION_CHECK=PASS
STAGE3C_PHASE1_PHELLO_REASSESSMENT=PASS
```

## Acceptance conditions

```text
[x] role inventory 43/43
[x] UNKNOWN = 0
[x] role decomposition 18/18
[x] semantic capability verifier 38/38
[x] component policy input contract 27/27
[x] component policy selector 18/18
[x] component policy independent verifier 34/34
[x] component policy source mutation PASS
[x] four exact-path variants materialize
[x] pre-behavior fidelity passes
[x] runtime-base production smoke passes
[x] development-addon extension compile/import passes
[x] test-addon representative test passes
[x] post-behavior fidelity passes
[x] all variant fingerprints remain unchanged
[x] canonical source fingerprint remains unchanged
[ ] corrected isolated capability matrix 17/17 x4
[ ] frozen `__phello__` and physical-root contract verified
[ ] targeted reassessment mutation controls pass
[ ] runtime-base native closure passes
[ ] runtime-base production relocation passes
```

## Claim boundary

Current evidence proves the complete component partition and every isolated physical-composition gate. The retained first-run failure is a semantic verifier false negative, not a payload leak or runtime failure.

A corrected reassessment PASS closes only that false negative. Native closure and whole-prefix relocation remain separate final Phase 1 gates before the split can be frozen.
