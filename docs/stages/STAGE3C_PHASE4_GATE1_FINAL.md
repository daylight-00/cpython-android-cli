# Stage 3-C Phase 4 Gate 1 Final: Installation Contract Model

> **Status:** FROZEN
> **Primary target:** Termux on Android arm64

## Frozen input

```text
Phase 3 runtime-base archive
  2ba7c309b1700926dc423eb4305a9eba1a53c023a11617e490b151be71e49743

Phase 3 development-addon archive
  f77ea24c92fdd982cd32e172b2d38134f1d785b1f106d1bfe36a9bffa9cc8eea

Phase 3 test-addon archive
  02a1fad1af5528a4e910f0eb3370f4a2696da4f78067586e8b62f2a10fb4c9b1

Phase 4 contract index
  79e3c173639047bc23b7dbe3c2135abe8f0b868d787735c094cbe06749c7dde3
```

## Frozen registry model

```text
registered paths               2956
structural references             4
shared structural namespace
  lib
  lib/python3.14
```

Registry and transaction state remain outside the payload prefix:

```text
<installation-root>/prefix/
<installation-root>/.cpython-android-cli/
```

## Frozen policy

```text
unowned leaf collision              reject
compatible exact directory reuse    allowed without descendant adoption
same-version exact match            NOOP
same-owner mismatch                 backup then repair
other-artifact ownership            reject
modified uninstall leaf             preserve and report
owned directory uninstall           remove only when empty
structural and unowned descendants  preserve
```

## Frozen ordering

```text
install steps      12
uninstall steps    10

preflight
  before mutation

journal
  PREPARED before first mutation

registry
  atomic replacement after payload changes

rollback
  required after any pre-commit mutation failure
```

## Validation ledger

```text
contract derivation       54/54 PASS
independent verifier      59/59 PASS
input mutation                  PASS
```

## Evidence

```text
docs/evidence/STAGE3C_PHASE4_INSTALLATION_CONTRACT_DESIGN.md
docs/evidence/STAGE3C_PHASE4_INSTALLATION_CONTRACT_RESULT.md
```

Accepted result bundle:

```text
stage3c-phase4-installation-contract-results-20260711-223404.tgz
sha256
  6c19503cc1ce76f3b832ce575e3e29a70cc5d59d5930cd552cbc365d706aea19
```

## Non-reopening rule

Later prototypes must consume this exact contract and must not weaken unowned collision rejection, exact-path ownership, non-owning structural semantics, modified-path preservation, empty-only directory removal, preflight ordering, or rollback obligations.

A policy change reopens Gate 1 and requires complete 54-check derivation and 59-check independent verification.

## Deferred

```text
transaction execution
failure-injection rollback execution
crash recovery
concurrent lock contention
upgrade and downgrade
installed runtime behavior
```

## Final marker

```text
STAGE3C_PHASE4_GATE1=FROZEN
```
