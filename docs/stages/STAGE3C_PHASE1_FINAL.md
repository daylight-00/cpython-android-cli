# Stage 3-C Phase 1 Final: Product Decomposition and Split-Runtime Validation

> **Status:** FROZEN
> **Frozen commit input:** `c1c4c2fa4ff726fcff16dabfafc41d263566c2dc`
> **Primary target:** Termux on Android arm64
> **Python baseline:** CPython 3.14.6

## Phase question

> Which promoted product paths belong to runtime, development, test, unsupported GUI, metadata, and license components, and does the selected split remain a valid relocatable runtime product?

## Frozen source

```text
work/termux/stage3b-promoted-runtime/prefix

entries     3155
ELF           81
symlinks       5
fingerprint
  5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c
```

## Frozen component partition

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

```text
role manifest
  092ea87eed2a3c800053a0ef480abd8ef836bda8a8890549ce84370eae6e2a0f

component manifest
  91088a013722ad35910f049bfc45b2e61607423d833c23038c1d9645497b7b84
```

## Frozen distributable candidates

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

unsupported-gui-source
  199 entries
  not distributed until a working _tkinter/Tcl/Tk backend exists
```

## Frozen semantic decisions

Runtime metadata remains in `runtime-base`:

```text
lib/python3.14/_sysconfigdata__android_aarch64-linux-android.py
lib/python3.14/_sysconfig_vars__android_aarch64-linux-android.json
lib/python3.14/build-details.json
```

Development metadata remains in `development-addon`:

```text
lib/python3.14/config-3.14-aarch64-linux-android/Makefile
lib/python3.14/config-3.14-aarch64-linux-android/Setup
lib/python3.14/config-3.14-aarch64-linux-android/Setup.local
lib/python3.14/config-3.14-aarch64-linux-android/config.c
lib/python3.14/config-3.14-aarch64-linux-android/python-config.py
```

Unsupported target source:

```text
lib/python3.14/tkinter/
lib/python3.14/idlelib/
lib/python3.14/turtledemo/
lib/python3.14/turtle.py
lib/python3.14/turtle.cfg, if present
```

`__phello__` is frozen into CPython. Its importability is independent of physical optional-source ownership.

## Validation ledger

```text
role inventory                         43/43 PASS
UNKNOWN                                     0
role decomposition                     18/18 PASS
semantic capability                    38/38 PASS
component-policy input                 27/27 PASS
component-policy selector              18/18 PASS
component-policy verifier              34/34 PASS
isolated materialization                 7/7 PASS
isolated fidelity before/after        15/15 PASS
frozen phello reassessment            114/114 PASS
corrected capabilities                 17/17 x4
final runtime input                     47/47 PASS
runtime-base closure                    63/63 PASS
Stage 3-B relocation engine             31/31 PASS
Stage 3-C relocation wrapper            60/60 PASS
aggregate final verifier                47/47 PASS
```

## Runtime-base frozen result

```text
entries                   714
directories                57
regular files             654
symlinks                    3
special files               0
ELF objects                81
DT_NEEDED edges           329
ANDROID_SYSTEM edges      249
RUNTIME_INTERNAL edges     80
unresolved edges            0
inspection errors           0
system SONAME dlopen      5/5
extension imports        67/67
```

Runtime-base strict fingerprint:

```text
9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796
```

Relocated portable fingerprint:

```text
5e3a46e454163b35f1c3bca6c381253fe0e025695f67fe874deedea006034fab
```

Relocation result:

```text
location A runtime/HTTPS/venv/uv-run       PASS
whole-prefix move A -> B                   PASS
location B runtime/HTTPS/venv/uv-run       PASS
stale A-prefix assertions                  PASS
source/B entries                       714/714
added / removed / portable changed      0/0/0
pycache                                    0
portable fidelity                         PASS
source mutation                            PASS
canonical mutation                         PASS
```

## Frozen evidence

```text
docs/evidence/STAGE3C_PHASE1_ROLE_INVENTORY_FIRST_RESULT.md
docs/evidence/STAGE3C_PHASE1_ROLE_DECOMPOSITION_RESULT.md
docs/evidence/STAGE3C_PHASE1_ROLE_SEMANTICS_RESULT.md
docs/evidence/STAGE3C_PHASE1_COMPONENT_POLICY_RESULT.md
docs/evidence/STAGE3C_PHASE1_ISOLATED_VARIANT_PHELLO_INCIDENT.md
docs/evidence/STAGE3C_PHASE1_PHELLO_REASSESSMENT_RESULT.md
docs/evidence/STAGE3C_PHASE1_RUNTIME_BASE_FINAL_RESULT.md
```

## Non-reopening rule

Later archive and installer work must consume these exact identities. It must not:

```text
move working runtime metadata into an addon
restore unsupported GUI source to runtime-base
remove any of the 81 ELF objects
weaken the 329-edge native closure
accept fewer than 67 extension imports
change the selected component path ownership merely to simplify tar creation
write validation state into the frozen source products
hard-code a final absolute installation prefix
```

Any intentional component change reopens Phase 1 and requires the complete semantic, physical, closure, and relocation validation chain.

## Deferred contract

Phase 1 does not select or freeze:

```text
archive envelope and root layout
manifest schema and installed registry
archive normalization and reproducibility
compression format and parameters
collision and transaction semantics
upgrade, rollback and uninstall behavior
signing, SBOM or publication
```

These begin in Stage 3-C Phase 2.

## Final marker

```text
STAGE3C_PHASE1=FROZEN
```
