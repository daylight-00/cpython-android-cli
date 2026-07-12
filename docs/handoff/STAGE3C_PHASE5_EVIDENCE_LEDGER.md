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

portable payload fingerprint
  f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978

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

archive sha256
  8e57399f907aec0c64e033a1d51380f0a27c3806773bc05ed2d88cbd3bf8785e

result-index sha256
  a6607fd9bc88e4cf2776295b0fce329b690b8ccf33aba2426847ba1529e85e3d

Gate 1 at A / B
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

## Gate 3A0 — reinstall and repair diagnostic census

```text
status
  FROZEN DIAGNOSTIC PASS

archive sha256
  9aae0ce2134331b272421bbb4f94010acde48e468ef8774617630bb6e8edd6b2

result-index sha256
  a7507ab60de402a636c8e2899706aec77844896254f28dd068c8683dcb3dce7b

scenario checks
  17/17

independent verifier
  31/31
```

Frozen prior-engine classification:

```text
exact same-version reinstall            supported NOOP
four existing-path mismatch classes     supported repair
registered regular absent               unsupported
registered symlink absent               unsupported
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_GATE3A_REINSTALL_REPAIR_DIAGNOSTIC_RESULT.md
```

## Phase 4I — missing registered leaf repair intervention

```text
status
  FROZEN PASS

archive
  stage3c-phase4-missing-leaf-repair-intervention-results-20260712-180237.tgz

archive sha256
  d497955abf1c4f83d9efc4e01783447c30af30f9b7b532d4a454b263a89c655a

archive size
  23,980,515 bytes

archive members
  580

result-index sha256
  7c87a7a3ee34b9c827a4895c78dc15780058d5f3af37e7eb78cd1c454d28f3b6

indexed files
  523/523 exact

scenario checks
  39/39 PASS

independent verifier
  51/51 PASS

Phase 4 copied input
  324/324 exact
```

Accepted correction:

```text
existing registered mismatch
  replaced mutation
  backup current path

missing registered non-directory
  created mutation
  skip nonexistent backup move
```

Success/regression matrix:

```text
exact reinstall NOOP                 PASS
existing-path repairs               4/4 PASS
missing regular/symlink repair      2/2 PASS
```

Crash matrix:

```text
regular leaf boundaries             6/6 PASS
symlink leaf boundaries             6/6 PASS
all crash boundaries               12/12 PASS
```

Pre-commit recovery restored the original missing state and prior registry. Committed recovery preserved the repaired leaf and cleaned the transaction.

Evidence:

```text
docs/evidence/STAGE3C_PHASE4_MISSING_LEAF_REPAIR_INTERVENTION_RESULT.md
```

## Active boundary

```text
Phase 5 Gate 3A product acceptance
```

Required proof:

```text
exact reinstall NOOP
six accepted repair classes
registry and portable identity after every repair
full post-repair Python runtime behavior
HTTPS 200
smoke-termux
uv venv and uv run
81/329/0 native closure
5/5 system SONAME dlopen
67/67 extension imports
no transaction residue
```

Handoff:

```text
docs/handoff/PHASE5_GATE3A_PRODUCT_ACCEPTANCE_HANDOFF_20260712.md
```

## Deferred boundaries

```text
Gate 2 relocation regression under corrected engine
Gate 3B preservation boundaries
Gate 3C addon lifecycle and dependencies
Gate 3D runtime uninstall and final ownership boundary
Gate 4 upgrade and downgrade
```
