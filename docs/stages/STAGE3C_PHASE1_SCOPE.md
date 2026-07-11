# Stage 3-C Phase 1 Scope: Promoted Product Role Inventory

> **Status:** ACTIVE — inventory PASS, decomposition PASS, semantic probe PASS, component policy pending
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

Phase 1 must not modify, prune, strip, rewrite, or package the canonical promoted tree.

## Completed evidence

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

Important surfaces:

```text
lib/python3.14/test          1785 entries   33,476,596 bytes
lib/python3.14/idlelib        161 entries    1,624,586 bytes
lib/python3.14/tkinter         14 entries      303,444 bytes
lib/python3.14/turtledemo      23 entries       61,800 bytes
lib/python3.14/__phello__       3 entries          194 bytes

include/                      434 entries    4,701,144 bytes
lib/pkgconfig/                  9 entries        1,689 bytes
lib/python3.14/config-*         6 entries       34,331 bytes
```

### Semantic capability probe — PASS

```text
machine verifier                     38/38
source mutation                       PASS
venv                                  PASS
ensurepip                             PASS observation
test / test.support                   PASS
sysconfig runtime service             PASS
active sysconfig paths under prefix   PASS
_sysconfigdata import                 PASS
build-details parse                   PASS
```

Tk-dependent capability:

```text
_tkinter             absent
tkinter              import failure
turtle               import failure
idlelib.pyshell      SystemExit 1
Tcl interpreter      unavailable
```

Selected interpretation:

```text
Tk/IDLE/turtle pure-Python source is present but unsupported on this target
runtime sysconfig metadata is active and must remain in runtime-base
config-tree metadata belongs to the development consumer surface
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE1_ROLE_INVENTORY_FIRST_RESULT.md
docs/evidence/STAGE3C_PHASE1_ROLE_DECOMPOSITION_RESULT.md
docs/evidence/STAGE3C_PHASE1_ROLE_SEMANTICS_RESULT.md
```

## Candidate product components

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
  not distributed until a working _tkinter/Tcl/Tk backend exists
```

Selected metadata ownership:

```text
RUNTIME_METADATA
  lib/python3.14/_sysconfigdata__android_aarch64-linux-android.py
  lib/python3.14/_sysconfig_vars__android_aarch64-linux-android.json
  lib/python3.14/build-details.json

DEVELOPMENT_METADATA
  config-*/Makefile
  config-*/Setup
  config-*/Setup.local
  config-*/config.c
  config-*/python-config.py
```

## Active gate: complete component manifest policy

Question:

> Can every accepted product path be assigned exactly once to the selected candidate components while retaining the accepted source manifest and source tree identity?

Run:

```sh
bash \
  experiments/stage3c-product-role-inventory/run-component-policy.sh
```

The workflow:

```text
recomputes the accepted 3155-row role manifest
requires accepted 38/38 semantic evidence
fingerprints the canonical product before and after
assigns every source row to one component
emits exact component path lists and byte/count summaries
re-derives the mapping in an independent verifier
checks all 81 ELF entries remain in RUNTIME_BASE
checks runtime/development anchors and metadata sets
marks unsupported GUI source as non-distributed
```

Outputs:

```text
results/termux/stage3c-phase1-component-policy/
  input-verification.json
  component-inventory.tsv
  component-summary.tsv
  component-policy.json
  component-policy-verification.json
  artifact-composition.json
  source-before.json
  source-after.json
  source-mutation-check.txt
  paths/*.txt
```

Expected markers:

```text
STAGE3C_PHASE1_COMPONENT_POLICY=PASS
COMPONENT_POLICY_INPUT_CONTRACT=PASS
COMPONENT_POLICY_COMPLETE_PARTITION=PASS
COMPONENT_POLICY_SOURCE_MUTATION_CHECK=PASS
STAGE3C_PHASE1_COMPONENT_POLICY_WORKFLOW=PASS
```

## Acceptance conditions

```text
[x] role inventory 43/43
[x] UNKNOWN = 0
[x] role decomposition 18/18
[x] semantic capability verifier 38/38
[x] semantic probe source mutation PASS
[x] regression-suite candidate selected
[x] unsupported Tk/IDLE/turtle policy selected
[x] runtime/development metadata candidates selected
[ ] accepted input contract recomputes
[ ] all 3155 paths assigned exactly once
[ ] component counts and bytes cross-check
[ ] all 81 ELF entries remain RUNTIME_BASE
[ ] component policy independent verifier passes
[ ] component policy source mutation control passes
[ ] isolated runtime-base materialization passes
[ ] development-addon composition passes
[ ] test-addon composition passes
[ ] closure and relocation pass for selected product
```

## Claim boundary

Current evidence proves complete classification, decomposition, and semantic target behavior.

The component policy gate will prove only a complete candidate path partition. It will not prove physical payload variants work. Phase 1 remains active until isolated copies validate smoke, uv/venv, sysconfig, addon composition, native closure, and relocation without modifying the canonical product.
