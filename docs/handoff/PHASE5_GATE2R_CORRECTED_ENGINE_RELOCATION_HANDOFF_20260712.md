# Phase 5 Gate 2R Corrected-Engine Relocation Regression Handoff — 2026-07-12

> **Status:** FROZEN PASS
> **Accepted evidence:** complete independently inspected Termux TGZ
> **Next boundary:** Gate 3B preservation boundaries

## Frozen Gate 2R identity

```text
archive
  stage3c-phase5-gate2r-corrected-engine-relocation-results-20260712-202419.tgz

archive sha256
  8e2c131567d78a4208e7c8eb02e783a479713f6d867a3e5cd98eae60aa5738a7

archive size
  72,501,453 bytes

archive members
  1,727

root result-index sha256
  69734a0ba286b9d6b55e8ef4c364dca7cb80bd380080cd6653038040ac51650c

root indexed files
  1,576/1,576 exact
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_GATE2R_CORRECTED_ENGINE_RELOCATION_RESULT.md
```

## Frozen verification

```text
Gate 2R verifier
  15/15 PASS

historical relocation verifier
  46/46 PASS

Gate 1 at A / B
  80/80 / 80/80

workflow return codes
  all 0
```

## Corrected-engine authority

```text
recovery_engine_missing_leaf.py sha256
  33b55d94714fb96f401caefe0e72d6587da955a9d0c201f4eb18dfc5193eb87a

recovery_operations_missing_leaf.py sha256
  61d20c68c7c5234a00328104914b83adc69859acca9791f3b14d9ff969e24021
```

Fresh installation at location A used the corrected engine and produced 714 create actions with 715 mutations.

## Frozen relocation result

```text
same filesystem
  true

inode preserved
  true

location A absent / B present
  true / true

complete-root shape
  719 / 60 / 656 / 3

complete-root fingerprint
  aea9a035d55530ab513458f43dbf7604a1f6aa9628eae4218dd050e688c14a30

portable fingerprint
  f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978

strict same-tree fingerprint
  3d61c27a3943930e53ac30035a2c4b77932cfabd17e4994f6370a30408a034f3

registry
  byte exact / 1 artifact / 714 owned rows

stale location-A references
  0
```

## Destination runtime

```text
Python 3.14.6
Android aarch64
HTTPS 200
uv venv and uv run PASS
native closure 81/329/0
system SONAME 5/5
extension imports 67/67
engine verify 1 artifact / 714 owned rows / 0 bad paths
```

## Next boundary: Gate 3B

Gate 3B must derive and validate preservation semantics for:

```text
modified owned regular leaf
modified owned symlink
unowned sentinel file
unowned sentinel directory
```

The test must distinguish install/repair ownership enforcement from uninstall preservation policy and must not invent policy outside the frozen transaction contract.

## Termux execution policy

Every target-only workflow must provide one script that verifies accepted input TGZ identities, freshly extracts them, executes the workflow, records status and result indices, and packages a TGZ on PASS or FAIL. Log capture must be synchronous before packaging.

## Claim boundary

Gate 2R proves same-filesystem rename-style relocation of a complete root created and verified with the accepted corrected engine. Cross-filesystem relocation, preservation boundaries, addon lifecycle, uninstall, upgrade, and downgrade remain separate claims.
