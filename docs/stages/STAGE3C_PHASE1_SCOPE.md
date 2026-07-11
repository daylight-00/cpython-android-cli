# Stage 3-C Phase 1 Scope: Product Roles and Split-Runtime Validation

> **Status:** FROZEN
> **Input:** frozen Stage 3-B promoted runtime
> **Execution host:** Termux on Android arm64

## Phase question

> Which promoted product paths belong to runtime, development, test, unsupported GUI, metadata, and license components, and does the selected runtime split preserve production behavior, native closure, extension imports, and whole-prefix relocation?

## Frozen input

```text
work/termux/stage3b-promoted-runtime/prefix

entries / ELF / symlinks
  3155 / 81 / 5

fingerprint
  5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c
```

## Completed gates

```text
complete role inventory                   43/43 PASS
UNKNOWN                                         0
role decomposition                         18/18 PASS
semantic capability                        38/38 PASS
component-policy input                     27/27 PASS
component-policy selector                  18/18 PASS
component-policy verifier                  34/34 PASS
isolated materialization                     7/7 PASS
isolated fidelity before/after            15/15 PASS
runtime-base production smoke                    PASS
development extension compile/import             PASS
test-addon representative test                  PASS
frozen phello reassessment                114/114 PASS
corrected variant capabilities             17/17 x4
runtime-base final input                    47/47 PASS
runtime-base native closure                 63/63 PASS
Stage 3-B relocation engine                 31/31 PASS
Stage 3-C relocation verifier               60/60 PASS
aggregate final verifier                    47/47 PASS
canonical and variant mutation controls           PASS
```

## Frozen component identities

```text
role manifest
  092ea87eed2a3c800053a0ef480abd8ef836bda8a8890549ce84370eae6e2a0f

component manifest
  91088a013722ad35910f049bfc45b2e61607423d833c23038c1d9645497b7b84
```

```text
runtime-base
  714 entries
  fingerprint
    9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796

development-addon
  454 component-owned entries

test-addon
  1788 component-owned entries

unsupported-gui-source
  199 entries
  not distributed
```

## Final runtime-base invariants

```text
ELF objects                    81
DT_NEEDED edges              329
ANDROID_SYSTEM edges         249
RUNTIME_INTERNAL edges        80
unresolved edges               0
inspection errors              0
system SONAME dlopen          5/5
extension imports           67/67
source/B entries            714/714
portable added/removed/changed 0/0/0
pycache paths                  0
portable relocation          PASS
```

Portable relocated fingerprint:

```text
5e3a46e454163b35f1c3bca6c381253fe0e025695f67fe874deedea006034fab
```

## Authoritative final record

```text
docs/stages/STAGE3C_PHASE1_FINAL.md
docs/evidence/STAGE3C_PHASE1_RUNTIME_BASE_FINAL_RESULT.md
```

The detailed experiment history remains in:

```text
experiments/stage3c-product-role-inventory/README.md
docs/evidence/STAGE3C_PHASE1_*.md
```

## Non-reopening rule

Later phases must consume the exact frozen component manifest and runtime identities. A change to path ownership, supported capability, native graph, or runtime-base contents reopens Phase 1 and requires the complete validation chain.

## Deferred to Phase 2 and later

```text
archive envelope and root layout
shared structural-directory semantics
manifest schema
license embedding outside installed payload
archive reproducibility and compression
installation ownership registry
collision, reinstall, upgrade and rollback
uninstall and interrupted-operation recovery
```

Next scope:

```text
docs/stages/STAGE3C_PHASE2_SCOPE.md
```

## Final marker

```text
STAGE3C_PHASE1=FROZEN
```
