# Stage 3-C Phase 5 Scope: Installed Runtime and Lifecycle Validation

> **Status:** ACTIVE — Gate 2R corrected-engine relocation regression
> **Primary target:** Termux on Android arm64

## Phase question

> Does the installed runtime remain exact, functional, relocatable, repairable, composable, and safely removable through the accepted transaction and recovery engine?

## Frozen product identities

```text
runtime-base manifest entries
  714

runtime-base source-tree fingerprint
  9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796

portable installed-payload fingerprint
  f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978

runtime-base archive sha256
  2ba7c309b1700926dc423eb4305a9eba1a53c023a11617e490b151be71e49743

runtime-base manifest sha256
  ce48849c9c88c9296264d6a917c3b55b0433e0d67bdda06579d6f18d701f285a

native closure
  81 ELF
  329 DT_NEEDED edges
  0 unresolved
  67/67 extension imports
```

The source-tree fingerprint is a manifest contract identity. It is not a fixed installed strict fingerprint. The installed strict fingerprint contains `mtime_ns` and is used only as a same-tree mutation control.

## Authority order

```text
Gate 1    installed runtime baseline                               FROZEN
Gate 2    historical complete installed-root relocation           FROZEN
Gate 3A0  reinstall and repair diagnostic census                  FROZEN
Phase 4I  missing registered non-directory repair intervention    FROZEN
Gate 3A   corrected reinstall and repair product acceptance       FROZEN
Gate 2R   corrected-engine complete-root relocation regression    ACTIVE
Gate 3B   owned/unowned preservation boundaries                   DEFERRED
Gate 3C   addon lifecycle and dependency enforcement              DEFERRED
Gate 3D   runtime uninstall and final ownership boundary          DEFERRED
Gate 4    upgrade and downgrade with second frozen product        DEFERRED
```

## Frozen Gate 1

```text
archive sha256
  06aa75b8b7617dc1310e7c0f3b56781b2297d2cc1ad617c1f4045909af9fb6ea

result-index sha256
  29e6dc1e24b7ad82bd809ac44d70aac1486549e71c24d49eb3ef8cc2dc4fe377

verifier
  80/80 PASS
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_BASELINE_RESULT.md
```

## Frozen historical Gate 2

```text
archive sha256
  8e57399f907aec0c64e033a1d51380f0a27c3806773bc05ed2d88cbd3bf8785e

result-index sha256
  a6607fd9bc88e4cf2776295b0fce329b690b8ccf33aba2426847ba1529e85e3d

location A / B Gate 1
  80/80 / 80/80

Gate 2 verifier
  46/46 PASS

complete-root fingerprint
  aea9a035d55530ab513458f43dbf7604a1f6aa9628eae4218dd050e688c14a30

complete-root shape
  719 entries
  60 directories
  656 regular files
  3 symlinks
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_RELOCATION_RESULT.md
```

## Frozen Gate 3A0 diagnostic

```text
archive sha256
  9aae0ce2134331b272421bbb4f94010acde48e468ef8774617630bb6e8edd6b2

result-index sha256
  a7507ab60de402a636c8e2899706aec77844896254f28dd068c8683dcb3dce7b

scenario checks
  17/17

independent verifier
  31/31
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_GATE3A_REINSTALL_REPAIR_DIAGNOSTIC_RESULT.md
```

## Frozen Phase 4I intervention

```text
archive sha256
  d497955abf1c4f83d9efc4e01783447c30af30f9b7b532d4a454b263a89c655a

result-index sha256
  7c87a7a3ee34b9c827a4895c78dc15780058d5f3af37e7eb78cd1c454d28f3b6

scenario checks
  39/39

independent verifier
  51/51

crash boundaries
  12/12
```

Accepted correction:

```text
existing mismatch
  replaced mutation
  backup current path

missing registered non-directory
  created mutation
  skip nonexistent backup move
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE4_MISSING_LEAF_REPAIR_INTERVENTION_RESULT.md
```

## Frozen Gate 3A product acceptance

```text
archive sha256
  16dbe98dedeb8db92df574a4d22ac3e45c0dd4032771dcf75e5e489b49605142

result-index sha256
  a161eedeebd086b1be6f115671312b463ed1eb9969c4494cae1bdbb626794128

repair scenario checks
  29/29

corrected-engine Gate 1 regression
  80/80

independent acceptance verifier
  69/69
```

Accepted product matrix:

```text
exact reinstall NOOP
six isolated repairs
six sequential repairs
registry identity exact after every repair
unaffected owned paths exact
portable identity f860caf... exact
zero transaction residue
```

Runtime:

```text
Python 3.14.6
Android aarch64
HTTPS 200
smoke-termux PASS
uv venv and uv run PASS
native closure 81/329/0
system SONAME 5/5
extension imports 67/67
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_GATE3A_PRODUCT_ACCEPTANCE_RESULT.md
```

## Active Gate 2R corrected-engine relocation regression

### Regression question

> Does a complete installation root created by the accepted corrected engine retain exact ownership identity and full runtime behavior after the same-filesystem inode-preserving relocation proven by historical Gate 2?

### Required topology

```text
fresh corrected-engine runtime-base installation at location A
full Gate 1-equivalent validation at A
complete-root and payload identities at A
same-filesystem mv A → B
full Gate 1-equivalent validation at B
complete-root and payload identities after move and after probes
stale location-A scan
```

The complete root includes:

```text
prefix/
.cpython-android-cli/lock
.cpython-android-cli/registry.json
.cpython-android-cli/transactions/
```

### Required relocation evidence

```text
source and destination parent device identical
root inode preserved
location A absent
location B present
location B Python executable
registry bytes exact
portable fingerprint f860caf... exact
strict same-tree fingerprint exact across move
complete-root fingerprint exact across move and probes
complete-root shape 719 / 60 / 656 / 3
zero special paths
zero stale A references
zero transaction residue
```

### Runtime validation at A and B

```text
Gate 1 verifier 80/80
Python 3.14.6
Android aarch64
HTTPS 200
smoke-termux PASS
uv venv PASS
uv run anyio PASS
native closure 81/329/0
system SONAME 5/5
extension imports 67/67
engine verify 1 artifact / 714 owned rows / 0 bad paths
```

### Termux execution policy

The workflow must provide one Termux wrapper that verifies accepted input archives, performs fresh extraction and execution, writes status and result-index evidence, and packages a TGZ on PASS or FAIL.

Handoff:

```text
docs/handoff/PHASE5_GATE2R_CORRECTED_ENGINE_RELOCATION_HANDOFF_20260712.md
```

### Claim boundary

Gate 2R proves only same-filesystem rename-style corrected-engine relocation. Cross-filesystem copy relocation remains unproved.

## Deferred Gate 3B

```text
modified owned regular leaf
modified owned symlink
unowned sentinel file
unowned sentinel directory
policy derived from the transaction contract
```

## Deferred Gate 3C

```text
runtime-base
→ development-addon
→ test-addon
→ dependency-order rejection
→ addon removals
→ runtime-base revalidation
```

## Deferred Gate 3D

```text
runtime-base-only state
approved unowned sentinels
owned payload removal
unowned preservation
registry transition
transaction residue check
empty-state verification
```

## Deferred Gate 4

Upgrade and downgrade remain deferred until a second complete frozen product identity exists. Synthetic version labels are not accepted.

## Non-reopening rule

Gate 2R may adapt historical relocation orchestration and verification to the accepted corrected engine only.

It must not broaden:

```text
journal schema
registry schema
manifest or archive identity
ownership policy
uninstall policy
addon dependency policy
```

Any broader change requires a new authority decision.

## Results layout

```text
Gate 3A product acceptance
  results/termux/stage3c-phase5-gate3a-reinstall-repair-acceptance/

Gate 2R corrected-engine relocation regression
  results/termux/stage3c-phase5-gate2r-corrected-engine-relocation/
```
