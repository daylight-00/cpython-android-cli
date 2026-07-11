# Stage 3-C Phase 1 Scope: Promoted Product Role Inventory

> **Status:** ACTIVE — inventory PASS, decomposition PASS, semantic PASS, component policy PASS, isolated variants pending
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

Candidate artifacts:

```text
runtime-base
  RUNTIME_BASE + RUNTIME_METADATA + LICENSE
  714 entries

development-addon
  DEVELOPMENT + DEVELOPMENT_METADATA
  454 entries

test-addon
  OPTIONAL_TEST_SUITE + OPTIONAL_TEST_DEMO
  1788 entries

unsupported-gui-source
  not distributed until a working _tkinter/Tcl/Tk backend exists
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE1_ROLE_INVENTORY_FIRST_RESULT.md
docs/evidence/STAGE3C_PHASE1_ROLE_DECOMPOSITION_RESULT.md
docs/evidence/STAGE3C_PHASE1_ROLE_SEMANTICS_RESULT.md
docs/evidence/STAGE3C_PHASE1_COMPONENT_POLICY_RESULT.md
```

## Active gate: isolated component variants

Question:

> Do exact-path copies of the selected components preserve runtime behavior, native-development behavior, test behavior, and source non-mutation before native closure and relocation are revalidated?

Run:

```sh
bash \
  experiments/stage3c-product-role-inventory/run-isolated-variant-validation.sh
```

Materialized variants:

```text
runtime-base
  714 entries
  38,759,749 bytes

runtime-development
  runtime-base + development-addon
  1168 entries
  43,733,124 bytes

runtime-test
  runtime-base + test-addon
  2502 entries
  72,236,539 bytes

runtime-supported
  runtime-base + development-addon + test-addon
  2956 entries
  77,209,914 bytes
```

No `UNSUPPORTED_GUI_SOURCE` row is copied.

The materializer requires each selected path set to be ancestor-closed. It copies regular files and symlinks, preserves file modes and nanosecond mtimes, then restores directory metadata in reverse depth order.

The independent fidelity verifier requires:

```text
exact selected path set
same type and mode
same mtime
same regular-file size and SHA-256
same symlink target
no pycache
no special files
81 ELF entries in every variant
```

Variant behavior matrix:

```text
runtime-base
  core runtime + sysconfig + runtime metadata present
  development paths absent
  test paths absent
  Tk/IDLE/turtle paths absent

runtime-development
  runtime-base behavior
  development paths and metadata present
  real C extension compile/import succeeds

runtime-test
  runtime-base behavior
  test, test.support and __phello__ present
  representative test_json regression run succeeds

runtime-supported
  development and test surfaces present together
  unsupported GUI source remains absent
```

The runtime-base production smoke reuses the frozen Stage 2-C smoke engine and therefore checks:

```text
core native imports
HTTPS through Termux CA integration
subprocess identity
uv venv
venv base identity
uv run with a first-party dependency
```

Mutation controls:

```text
canonical source strict fingerprint before/after
all four variant strict fingerprints before/after
post-behavior exact-path fidelity
explicit -B or PYTHONDONTWRITEBYTECODE controls
```

Expected outputs:

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
[ ] four exact-path variants materialize
[ ] pre-behavior fidelity passes
[ ] variant capability matrix passes
[ ] runtime-base production smoke passes
[ ] development-addon extension compile/import passes
[ ] test-addon representative test passes
[ ] post-behavior fidelity passes
[ ] all variant fingerprints remain unchanged
[ ] canonical source fingerprint remains unchanged
[ ] runtime-base native closure passes
[ ] runtime-base production relocation passes
```

## Claim boundary

The current evidence proves a complete candidate component partition and target-specific ownership policy.

The active isolated gate proves physical composition and selected behavior only. Native closure and whole-prefix relocation remain separate final Phase 1 gates before the split can be frozen.
