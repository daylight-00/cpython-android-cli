# Stage 3-C Phase 5 Evidence Ledger

> **Purpose:** compact authoritative identity ledger for installed-runtime and lifecycle gates.
> **Authority:** accepted Termux TGZ evidence plus repository-frozen contracts.

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

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_BASELINE_RESULT.md
```

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

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_RELOCATION_RESULT.md
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

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_GATE3A_REINSTALL_REPAIR_DIAGNOSTIC_RESULT.md
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

Evidence:

```text
docs/evidence/STAGE3C_PHASE4_MISSING_LEAF_REPAIR_INTERVENTION_RESULT.md
```

## Gate 3A — corrected reinstall and repair product acceptance

```text
status
  FROZEN PASS

archive sha256
  16dbe98dedeb8db92df574a4d22ac3e45c0dd4032771dcf75e5e489b49605142

result-index sha256
  a161eedeebd086b1be6f115671312b463ed1eb9969c4494cae1bdbb626794128

repair scenarios
  29/29

corrected-engine Gate 1
  80/80

acceptance verifier
  69/69
```

Accepted matrix: exact reinstall NOOP; six isolated repairs; six sequential repairs; registry and unaffected-owned identity exact; portable fingerprint exact; zero transaction residue; complete runtime contract PASS.

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_GATE3A_PRODUCT_ACCEPTANCE_RESULT.md
```

## Gate 2R — corrected-engine complete-root relocation

```text
status
  FROZEN PASS

archive
  stage3c-phase5-gate2r-corrected-engine-relocation-results-20260712-202419.tgz

archive sha256
  8e2c131567d78a4208e7c8eb02e783a479713f6d867a3e5cd98eae60aa5738a7

archive size
  72,501,453 bytes

archive members
  1,727

result-index sha256
  69734a0ba286b9d6b55e8ef4c364dca7cb80bd380080cd6653038040ac51650c

indexed files
  1,576/1,576 exact

Gate 1 at A / B
  80/80 / 80/80

historical relocation verifier
  46/46

corrected-engine authority verifier
  15/15
```

Frozen relocation identity:

```text
same filesystem / inode preserved
  true / true

complete-root shape
  719 / 60 / 656 / 3

complete-root fingerprint
  aea9a035d55530ab513458f43dbf7604a1f6aa9628eae4218dd050e688c14a30

portable fingerprint
  f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978

strict same-tree fingerprint
  3d61c27a3943930e53ac30035a2c4b77932cfabd17e4994f6370a30408a034f3

stale location-A references
  0
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_GATE2R_CORRECTED_ENGINE_RELOCATION_RESULT.md
```

## Active boundary

```text
Gate 3B preservation boundaries
```

Required investigation:

```text
modified owned regular leaf
modified owned symlink
unowned sentinel file
unowned sentinel directory
install/repair enforcement versus uninstall preservation
registry and transaction-state consequences
```

Policy must be derived from the frozen transaction contract rather than assumed.

## Deferred boundaries

```text
Gate 3C addon lifecycle and dependencies
Gate 3D runtime uninstall and final ownership boundary
Gate 4 upgrade and downgrade
```
