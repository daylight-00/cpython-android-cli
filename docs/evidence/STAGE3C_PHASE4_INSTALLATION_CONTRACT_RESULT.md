# Stage 3-C Phase 4 Installation Contract Result

> **Status:** PASS — Gate 1 deterministic contract closed
> **Target:** Termux on Android arm64
> **Result archive:** `stage3c-phase4-installation-contract-results-20260711-223404.tgz`

## Result archive identity

```text
sha256
  6c19503cc1ce76f3b832ce575e3e29a70cc5d59d5930cd552cbc365d706aea19

members
  41

unsafe member names
  0

special archive entries
  0
```

## Machine result

```text
contract derivation       54/54 PASS
independent verifier      59/59 PASS
workflow return codes      all 0
failed checks                  []
```

```text
STAGE3C_PHASE4_INSTALLATION_CONTRACT_DERIVATION=PASS
STAGE3C_PHASE4_INSTALLATION_CONTRACT=PASS
```

## Deterministic outputs

```text
registered owned paths          2956
non-owning structural refs         4
collision policy rows             17
operation-order rows               22
install steps                      12
uninstall steps                    10
```

Contract index:

```text
sha256
  79e3c173639047bc23b7dbe3c2135abe8f0b868d787735c094cbe06749c7dde3
```

Generated identities:

```text
collision-policy.tsv
  c7028170967dc8293e435a09672bb7868f1826407ce44c4d572b1b8e4c70ad93

contract-summary.tsv
  14af3e4b0ab64f91f2a5064e2d1be16dda5658ebdb9acc050109addec0104511

installation-contract.json
  8ff6f65fd10cfeb94e3782162f1140ab39e4c41f26c6c3cf69cbb2d9e7379264

installed-owned-paths.tsv
  b56517716b6c18598ed7d9858966acfcacedaf2da74ce71ea0bfbf0bb598b1be

operation-order.tsv
  7abcc837faa03c45efcc7f8d168c745f825b5ea0f2191e032adc2ed01e428efc

registry-template.json
  c6ba8926fab14495a2b299af2a8906252282b09e5d1c1fc412dc8832a13b0590

structural-paths.tsv
  a8b33283badc5e876a0431adceee001b7b9076525dcb016f9d9b17caafb2bbe0
```

## Frozen ownership direction

```text
registry records
  OWNED_PAYLOAD only

structural namespace
  lib
  lib/python3.14

STRUCTURAL_PARENT
  non-owning reference only

archive metadata
  not installed into prefix/
```

Exact owned-path overlap is zero. All 2956 registry paths are safe relative paths and map to one artifact owner.

## Frozen collision direction

```text
unowned regular file or symlink at required leaf
  conflict before mutation

compatible existing owned-directory path
  reuse and register the directory path only

compatible structural directory
  reuse without ownership

required directory occupied by non-directory
  conflict

same-version exact registered entry
  no-op

same-owner registered mismatch
  replacement requires backup

other-artifact owner
  conflict
```

Directory ownership never grants descendant ownership.

## Frozen uninstall direction

```text
matching registered leaf
  remove exact

locally modified registered leaf
  preserve and report

owned directory
  remove only when empty

structural parent
  preserve namespace

unowned descendant
  preserve
```

## Transaction obligations

```text
complete preflight before mutation
exclusive installation lock
same-filesystem staging
backup before replace or remove
prior registry backup
PREPARED journal before first mutation
atomic registry replacement
rollback after pre-commit mutation failure
```

States:

```text
PREPARED
APPLYING
COMMITTED
ROLLING_BACK
ROLLED_BACK
FAILED
```

## Input mutation

```text
input entries before/after
  22 / 22

input fingerprint before/after
  779695b07ae5bdecdb18f655433086a86d61e959ffd9af5942fd0caf6f1a14fb

special paths
  0
```

## Closed claims

This result proves that the frozen archives deterministically derive the complete installed ownership registry, structural references, collision rules, reinstall rules, operation ordering, rollback obligations, and uninstall rules.

## Claim boundary

This result does not prove filesystem mutation, rollback execution, crash recovery, lock contention, upgrade, downgrade, or installed runtime behavior. Those require later Phase 4 gates.
