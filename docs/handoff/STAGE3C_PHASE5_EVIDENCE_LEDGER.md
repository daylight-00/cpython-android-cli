# Stage 3-C Phase 5 Evidence Ledger

> **Purpose:** compact authoritative identity ledger for installed-runtime and lifecycle gates.
> **Authority:** accepted Termux TGZ evidence plus repository-frozen contracts.

## Gate 1 — installed runtime baseline

```text
status
  FROZEN PASS

accepted archive sha256
  06aa75b8b7617dc1310e7c0f3b56781b2297d2cc1ad617c1f4045909af9fb6ea

result-index sha256
  29e6dc1e24b7ad82bd809ac44d70aac1486549e71c24d49eb3ef8cc2dc4fe377

verifier
  80/80 PASS

portable payload fingerprint
  f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978

payload / registry
  714 entries
  1 artifact
  714 owned rows

runtime
  Python 3.14.6
  Android aarch64
  HTTPS 200
  uv venv and uv run PASS
  81 ELF / 329 edges / 0 unresolved
  5/5 system SONAME dlopen
  67/67 extension imports
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_BASELINE_RESULT.md
```

## Gate 2 — complete installed-root relocation

```text
status
  FROZEN PASS

accepted archive sha256
  8e57399f907aec0c64e033a1d51380f0a27c3806773bc05ed2d88cbd3bf8785e

result-index sha256
  a6607fd9bc88e4cf2776295b0fce329b690b8ccf33aba2426847ba1529e85e3d

Gate 1 at location A
  80/80 PASS

Gate 1 at location B
  80/80 PASS

Gate 2 verifier
  46/46 PASS

complete-root fingerprint
  aea9a035d55530ab513458f43dbf7604a1f6aa9628eae4218dd050e688c14a30

complete-root shape
  719 entries
  60 directories
  656 regular files
  3 symlinks
  0 special

relocation
  same filesystem
  inode preserved
  registry byte exact
  stale source references 0
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_RELOCATION_RESULT.md
```

## Gate 3A0 — reinstall and repair diagnostic census

```text
status
  FROZEN DIAGNOSTIC PASS

product acceptance
  BLOCKED

accepted archive
  stage3c-phase5-gate3a-reinstall-repair-diagnostic-results-20260712-172353.tgz

accepted archive sha256
  9aae0ce2134331b272421bbb4f94010acde48e468ef8774617630bb6e8edd6b2

archive size
  23,954,673 bytes

archive members
  409

result-index sha256
  a7507ab60de402a636c8e2899706aec77844896254f28dd068c8683dcb3dce7b

indexed files
  365/365 exact

scenario checks
  17/17 PASS

independent verifier
  31/31 PASS

Phase 4 copied input
  324/324 exact
```

Frozen classification:

```text
exact same-version reinstall            supported NOOP
regular byte mismatch                   supported repair
regular mode mismatch                   supported repair
symlink target mismatch                 supported repair
registered regular wrong type           supported repair
registered regular absent               unsupported
registered symlink absent               unsupported
```

Missing-leaf sequence:

```text
install                     rc 44 FileNotFoundError
journal                     APPLYING
recover 1                   ROLLED_BACK, restored 0
recover 2                   NOOP_ROLLED_BACK
post-recovery verify        same missing bad path
registry row                retained
leaf                        absent
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_GATE3A_REINSTALL_REPAIR_DIAGNOSTIC_RESULT.md
```

## Active authority

```text
narrow Phase 4 architecture intervention
  registered missing non-directory repair

required correction
  existing mismatch → replaced mutation
  missing registered leaf → created mutation
```

Decision:

```text
docs/handoff/PHASE5_GATE3A_INTERVENTION_DECISION_20260712.md
```

## Deferred boundaries

```text
Gate 3A product acceptance
Gate 3B preservation boundaries
Gate 3C addon lifecycle and dependencies
Gate 3D runtime uninstall and final ownership boundary
Gate 4 upgrade and downgrade
```

No later gate may proceed until the intervention and affected downstream regressions are accepted from authoritative Termux evidence.
