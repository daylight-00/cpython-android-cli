# Stage 3-C Phase 5 Evidence Ledger

> **Purpose:** compact authoritative identity ledger for installed-runtime and lifecycle gates.
> **Authority:** accepted Termux target archives plus repository-frozen contracts. Historical `.tgz` authorities remain immutable; new archives use `.tar.zst`.

## Gate 1 — installed runtime baseline

```text
status
  FROZEN PASS

archive sha256
  06aa75b8b7617dc1310e7c0f3b56781b2297d2cc1ad617c1f4045909af9fb6ea

result-index sha256
  29e6dc1e24b7ad82bd809ac44d70aac1486549e71c24d49eb3ef8cc2dc4fe377

verifier
  80/80 PASS

portable fingerprint
  f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978
```

Runtime: Python 3.14.6, Android aarch64, HTTPS 200, uv PASS, closure 81/329/0, system SONAME 5/5, extension imports 67/67.

## Gate 2 — historical complete-root relocation

```text
status
  FROZEN PASS

archive sha256
  8e57399f907aec0c64e033a1d51380f0a27c3806773bc05ed2d88cbd3bf8785e

result-index sha256
  a6607fd9bc88e4cf2776295b0fce329b690b8ccf33aba2426847ba1529e85e3d

Gate 1 at A / B
  80/80 / 80/80

verifier
  46/46 PASS
```

## Gate 3A0 — reinstall and repair diagnostic

```text
status
  FROZEN DIAGNOSTIC PASS

archive sha256
  9aae0ce2134331b272421bbb4f94010acde48e468ef8774617630bb6e8edd6b2

result-index sha256
  a7507ab60de402a636c8e2899706aec77844896254f28dd068c8683dcb3dce7b

checks
  17/17 + 31/31
```

## Phase 4I — missing registered leaf intervention

```text
status
  FROZEN PASS

archive sha256
  d497955abf1c4f83d9efc4e01783447c30af30f9b7b532d4a454b263a89c655a

result-index sha256
  7c87a7a3ee34b9c827a4895c78dc15780058d5f3af37e7eb78cd1c454d28f3b6

checks
  39/39 + 51/51

crash boundaries
  12/12
```

## Gate 3A — corrected reinstall and repair product acceptance

```text
status
  FROZEN PASS

archive sha256
  16dbe98dedeb8db92df574a4d22ac3e45c0dd4032771dcf75e5e489b49605142

result-index sha256
  a161eedeebd086b1be6f115671312b463ed1eb9969c4494cae1bdbb626794128

checks
  29/29 repair + 80/80 Gate 1 + 69/69 acceptance
```

## Gate 2R — corrected-engine complete-root relocation

```text
status
  FROZEN PASS

archive sha256
  8e2c131567d78a4208e7c8eb02e783a479713f6d867a3e5cd98eae60aa5738a7

result-index sha256
  69734a0ba286b9d6b55e8ef4c364dca7cb80bd380080cd6653038040ac51650c

Gate 1 at A / B
  80/80 / 80/80

historical relocation verifier
  46/46

corrected-engine verifier
  15/15

complete-root shape
  719 / 60 / 656 / 3

complete-root fingerprint
  aea9a035d55530ab513458f43dbf7604a1f6aa9628eae4218dd050e688c14a30
```

## Gate 3B0 — preservation-boundary diagnostic

```text
status
  FROZEN DIAGNOSTIC PASS

archive
  stage3c-phase5-gate3b0-preservation-diagnostic-results-20260712-211837.tgz

archive sha256
  ed5cb08cc576e74cacac4077cf9c9d7f3164a34913197aae9ef10cc8c113801a

archive size
  22,701,335 bytes

archive members
  131

result-index sha256
  7a8e982a44118dac3f232b2fefb578d22bedc0c7d32a6267ab3cd55c5e8deb27

indexed files
  110/110 exact

scenario checks
  16/16

independent verifier
  40/40
```

Frozen census:

```text
reinstall-owned-regular       ENFORCED_REPAIR
reinstall-owned-symlink       ENFORCED_REPAIR
reinstall-unowned-file        PRESERVED_NOOP
reinstall-unowned-directory   PRESERVED_NOOP
uninstall-owned-regular       PRESERVED_AND_DEREGISTERED
uninstall-owned-symlink       PRESERVED_AND_DEREGISTERED
uninstall-unowned-file        UNOWNED_PRESERVED
uninstall-unowned-directory   UNOWNED_PRESERVED
```

Contract decision:

```text
local modification uninstall policy
  preserve-and-report

modified regular or symlink
  PRESERVE_AND_REPORT

owned directory
  REMOVE_ONLY_WHEN_EMPTY

structural parent
  PRESERVE_NAMESPACE

unowned descendant
  PRESERVE
```

The Termux census matches the frozen contract. No intervention is required.

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_GATE3B0_PRESERVATION_DIAGNOSTIC_RESULT.md
```

## Gate 3B — preserve-and-report product acceptance

```text
status
  FROZEN PASS

archive
  stage3c-phase5-gate3b-preservation-acceptance-results-20260713-024946.tgz

archive sha256
  0be850523ddc9b0fcb652d47f4414d0772dea1d8767f23490c3655576683270b

archive size
  24,857,211 bytes

archive members
  323

root result-index sha256
  f3e0bd34c61f5b1e0960d002175478b112641fa71f0e914ec712e6c514e52fe9

root indexed files
  289/289 exact

scenario checks
  29/29 PASS

independent verifier
  62/62 PASS

happy / crash topology
  8/8 / 12/12

return codes
  scenario 0 / verifier 0 / workflow 0 / wrapper 0
```

Accepted boundaries are PREPARED rc 90, late APPLYING rc 93, and COMMITTED rc 92. Modified-owned pre-commit recovery intentionally returns verifier rc 44 with exactly the modified leaf; unowned pre-commit and committed states return rc 0.

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_GATE3B_PRESERVATION_ACCEPTANCE_RESULT.md
```

## Gate 3C — addon lifecycle and dependency enforcement

```text
status
  FROZEN PASS

archive
  stage3c-phase5-gate3c-addon-lifecycle-results-20260713T033412Z.tar.zst

archive sha256
  43fa4bbbfdfb7fc7562c3881771a625662422980b352482da19ab2b3a07dee7a

archive size
  23,994,806 bytes

archive members
  801

root result-index sha256
  fb51d53ab0a4605159e58208c374017c2de9fed6ba924f08d98cfabf82ce6c7c

root indexed files
  731/731 exact

checks
  design 73/73
  scenarios 50/50
  independent verifier 103/103
  external archive audit 27/27
```

Accepted boundaries:

```text
development-addon -> exact runtime-base
test-addon -> exact runtime-base
no inter-addon dependency
both addon install and removal orders
runtime-base removal rejected while any addon remains
rollback audit tombstone and committed cleanup semantics preserved
complete runtime regression after addon removal
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_GATE3C_ADDON_LIFECYCLE_ACCEPTANCE_RESULT.md
docs/evidence/STAGE3C_PHASE5_GATE3C_ARCHIVE_INTEGRITY_CORRECTION.md
```

## Gate 3D — final uninstall and ownership boundary

```text
status
  FROZEN PASS

archive
  stage3c-phase5-gate3d-final-uninstall-results-20260713T053801Z.tar.zst

archive sha256
  579b880495098e9a46b40e2d96c9555178d0ad8c725d40768e6b854227d66143

accepted implementation tree
  5d54f8e0ab69ab5923949b9a5a34d71e2ab3da36

root result-index sha256
  5f9aa64cb4e0679a4784c9c3b8ebd6d8d91829704984672186dc9f9c0d96ed60

result-tree-safety sha256
  47b571d79990cf6c5f1157f7784a5acfa47478b04a7c6f55185d3c4f38ab8a00

checks
  design 108/108
  target scenarios 44/44
  independent verifier 138/138
  external archive audit 37/37
```

Accepted evidence surface:

```text
archive members                   909
root indexed files            845/845
canonical generated JSON      442/442
raw process records                177
unsafe / link / special        0 / 0 / 0
```

Gate 3D freezes both complete addon teardown orders, final runtime-base removal, rejection while dependencies remain, exact-owned teardown, modified-owned and unowned residual classes, PREPARED/APPLYING rollback tombstones, COMMITTED cleanup, lock exclusion, and empty-registry versus physically-empty-prefix distinctions.

Design and acceptance authority:

```text
experiments/stage3c-installed-runtime-lifecycle/GATE3D_FINAL_UNINSTALL_DESIGN.md
experiments/stage3c-installed-runtime-lifecycle/gate3d-final-uninstall-matrix.json
docs/evidence/STAGE3C_PHASE5_GATE3D_FINAL_UNINSTALL_ACCEPTANCE_RESULT.md
docs/evidence/STAGE3C_PHASE5_GATE3D_EXTERNAL_AUDIT.json
experiments/stage3c-installed-runtime-lifecycle/gate3d-final-uninstall-acceptance.json
```

## Gate 4 — upgrade and downgrade

```text
status
  FROZEN — Gate 4E independent transition freeze complete

Gate 4A second-product authority
  FROZEN PASS — CPython 3.14.5 / android24 / aarch64

Gate 4B transition contract
  DESIGN FROZEN — 66 scenarios

Gate 4C coordinator
  IMPLEMENTED — repository verifier 69/69 PASS

Gate 4D target validation
  ACCEPTED — 66/66

Gate 4E independent freeze
  FROZEN PASS
```

### Gate 4A frozen second product

```text
product
  cpython-android-cli 3.14.5 / android24 / aarch64

source commit
  5607950ef232dad16d75c0cf53101d9649d89115

product lock sha256
  e8c189d4a7386f1c522cc1479515b266fff60fdffedb3b7e842d9730ec21faeb

runtime / development / test owned paths
  714 / 447 / 1785

A6 independent candidate result sha256
  4565b69e78c618f58fda59f928c086bbcf1cd02cfb28252f419e42e8cbc266aa

repository freeze result sha256
  5daf2d05ddbaa3cba5f9fec183a92f967f50502dbddc73bbf7c25b77fd0e0158
```

Authority records:

```text
experiments/stage3c-gate4-second-product-authority/gate4a-a6-second-product-freeze-authority.json
docs/evidence/STAGE3C_PHASE5_GATE4A_A6_SECOND_PRODUCT_FREEZE_RESULT.md
```

### Gate 4B frozen transition contract

The exact product delta contains 2,958 union owned paths: 2,944 shared, 216 byte-exact shared, 2,728 replacements, 12 first-product-only, 2 second-product-only, and zero cross-artifact owner transfers.

```text
scenario matrix
  66

design verifier
  106/106 PASS

design-freeze result sha256
  f1b4670feccafa70824eb359bd835b9fba9e436513a482511565dda32404c915
```

The frozen policy requires a dedicated whole-product transition, exact-source preflight, topology preservation, unowned collision rejection, one recovery-compatible transaction, schema-1 registry replacement, and bidirectional PREPARED/APPLYING/COMMITTED recovery.

Authority records:

```text
experiments/stage3c-gate4-transition/GATE4B_TRANSITION_CONTRACT_DESIGN.md
experiments/stage3c-gate4-transition/gate4b-transition-matrix.json
experiments/stage3c-gate4-transition/gate4b-cross-version-inventory.json
experiments/stage3c-gate4-transition/gate4b-transition-design-authority.json
docs/evidence/STAGE3C_PHASE5_GATE4B_TRANSITION_CONTRACT_DESIGN_RESULT.md
```

### Gate 4C implemented coordinator

```text
repository verifier
  69/69 PASS

verification result sha256
  6c97a9cf0d97c8f3f24a7931a995e54bc9d57b209db144774bb73f2a42325073

frozen engine source changes
  none

registry schema
  remains 1
```

Gate 4C accepts repository implementation and synthetic transaction semantics only. No real CPython upgrade, downgrade, runtime behavior, or target crash recovery is frozen.

Implementation records:

```text
experiments/stage3c-gate4-transition/GATE4C_TRANSITION_COORDINATOR_IMPLEMENTATION.md
experiments/stage3c-gate4-transition/gate4c-transition-authorities.json
experiments/stage3c-gate4-transition/transition_coordinator.py
experiments/stage3c-gate4-transition/verify-gate4c-transition-implementation.py
experiments/stage3c-gate4-transition/gate4c-transition-implementation-authority.json
docs/evidence/STAGE3C_PHASE5_GATE4C_TRANSITION_COORDINATOR_IMPLEMENTATION_RESULT.md
```

### Gate 4D target validation and Gate 4E freeze

```text
v1 target archive  ef24baca1f01d3e106825fb99e537d68ba0beffa9cd4e92577e43bd35421e77c  493427  1223/1223
v2 corrective     98ab810732dd2eb35bff9180dcb8fa1ec872eb09103d58670edb481cc9e3e5b2  720554  529/529
focused retest    8/8 PASS
final matrix      66/66 PASS
independent audit 16/16 PASS
```

The v1 archive remains immutable. H01-H08 were corrected by focused target retest, C11-C12 by exact baseline evidence replay, and A04 by derivation after corrected group acceptance.

## Immediate next boundary

Gate 4 is closed. Stage 3-D consumer integration remains deferred and must begin with its own scope and authority decision.
