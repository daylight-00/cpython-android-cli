# Stage 3-C Evidence Ledger

> **Purpose:** compact identity ledger for successor sessions.
> **Authority:** repository-frozen evidence plus accepted Termux TGZ results.

## Repository baseline at handoff

```text
main before handoff-doc merge
  c216bc21670620024eef307688fd6fd5e3d267ef
  Freeze Phase 4 and open installed runtime validation (#27)
```

The handoff-doc merge will create a newer main commit. Successor sessions must begin with `git pull --ff-only` and inspect the new head rather than assuming `c216bc2` remains current.

## Stage 2 and Stage 3-B frozen ancestry

```text
Stage 2
  conditional self re-exec and PyConfig auto-discovery frozen

Stage 3-B promoted product
  entries                 3155
  ELF                       81
  symlinks                   5
  unresolved native edges    0
  extension imports       67/67

portable fingerprint
  79ca7d53f25810b1f5276d18df31f10f2ae981dc24caf67c5f33d37fa75127c8

candidate same-tree fingerprint
  834f7aeb2e5266f027b6ee43dd77255079b2e01cf049dad56fda5ef39ce048b0

frozen fingerprint
  5a14f213bbf069b844a799615ed2b87eb34b48b4251b0a48bf431337e929ce0e

frozen commit
  00f789479158adb6ff246abd8a4e42d2a2cbaddc
```

## Stage 3-C Phase 1 — frozen product semantics

```text
canonical entries
  3155

canonical fingerprint
  5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c

runtime-base entries
  714

runtime-base fingerprint
  9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796

native closure
  81 ELF
  329 DT_NEEDED edges
  0 unresolved

extension imports
  67/67

isolated relocation
  PASS
```

Component variants:

```text
runtime-base          714
runtime-development  1168
runtime-test         2502
runtime-supported    2956
```

## Stage 3-C Phase 2 — frozen ownership and manifests

```text
runtime-base owned paths
  714

development-addon owned paths
  454

test-addon owned paths
  1788

selected total
  2956

unsupported GUI excluded
  199

exact owned overlap
  0
```

Shared non-owning structural namespace:

```text
lib
lib/python3.14
```

Ownership identities:

```text
owned paths
  ab2c7374d2a70c7eb48db72dbfd1de86b708167efef151519f25b6a5a65023ea

structural directories
  9481da6ffa6bf0f54a10b631a31b81252580e2323bd1c8a92c6899aff26b78b3

shared namespace
  cc40599da21dbef18e48b940b77143e44479e821b3273946843a89340052956e
```

Manifest index:

```text
540adfaacf9387e80a258dfa3db8c299ad775d99e771c475a89dfc61de6868c1
```

Manifest identities:

```text
runtime-base
  ce48849c9c88c9296264d6a917c3b55b0433e0d67bdda06579d6f18d701f285a

development-addon
  9a01655d63044ab126fd71236ca2cb814221317ee9b6b44fd2417fa5535a8b2a

test-addon
  47d9f2e24e74b23e34ae6bfa95a0df22ec7cf9505e3e189dc3d6bdf2dc1c8b5f
```

## Stage 3-C Phase 3 — frozen deterministic archives

```text
runtime-base archive
  2ba7c309b1700926dc423eb4305a9eba1a53c023a11617e490b151be71e49743

development-addon archive
  f77ea24c92fdd982cd32e172b2d38134f1d785b1f106d1bfe36a9bffa9cc8eea

test-addon archive
  02a1fad1af5528a4e910f0eb3370f4a2696da4f78067586e8b62f2a10fb4c9b1
```

Validation:

```text
builder                    31/31 PASS
extraction preflight       28/28 PASS
archive verifier           76/76 PASS
safe staging extraction      3/3 PASS
```

Serialization:

```text
POSIX pax tar
gzip level 9
mtime 0
uid/gid 0/0
empty owner names
exact member order
hardlinks forbidden
special entries forbidden
```

## Stage 3-C Phase 4 Gate 1 — installation contract

```text
contract derivation       54/54 PASS
independent verifier      59/59 PASS
registered ownership       2956
structural references         4
contract index
  79e3c173639047bc23b7dbe3c2135abe8f0b868d787735c094cbe06749c7dde3
```

## Stage 3-C Phase 4 Gate 2 — isolated transactions

```text
scenario runner       61/61 PASS
independent verifier  58/58 PASS
scenario logs          25/25
result-index
  0041f1c3c73dc7a62291b6c3b244ac885d9bad6799d4115280febc20f61384da
```

Accepted TGZ:

```text
stage3c-phase4-installation-transaction-results-20260711-230729.tgz
sha256
  9ea7379263711c8501d674e78e25d29ccd1764db30497c5dc2414030d378c005
```

## Stage 3-C Phase 4 Gate 3 — recovery and lock

```text
scenario runner       55/55 PASS
independent verifier  82/82 PASS
scenario logs          40/40 canonical
snapshot pairs           5
result-index
  f5ba124ebb9752b45d60f027474a399adf61fc5db033c1165a79664cbfc743bd
```

Accepted corrected TGZ:

```text
stage3c-phase4-installation-recovery-independent-seed-copy-corrected-results-20260712-004138.tgz
sha256
  3c164f54e4f205ba8ba889274656375ce2c0cf137f65c6ccf6fb2cafab889bd6
```

Preserved failed attempt:

```text
hardlink-based scenario seed clone failed on Termux with EACCES
failure evidence remains tracked
```

## Stage 3-C Phase 4 Gate 4 — durability protocol

```text
scenario runner       64/64 PASS
independent verifier  53/53 PASS
positive traces         7/7
negative controls        2
result-index
  3cb7e83eb6dc6c186a36da512ed41cbba4566abfc4bd4f5f71766ea1fcf075c4
```

Accepted TGZ:

```text
stage3c-phase4-installation-durability-results-20260712-011157.tgz
sha256
  94567ed50f030f3ab1844d81533a2e67eb22e83accabb0753a8501c84fd2ecda
```

## Stage 3-C Phase 4 Gate 5A — production mutation inventory

```text
inventory scenario       32/32 PASS
independent verifier     29/29 PASS
all rows                     81
production rows              67
UNKNOWN                       0
result-index
  ac11225ae6b45ac45f1e378ecf7bba9cd074a1f779009318e001d5694d89ead8
```

Frozen source blobs:

```text
recovery_common.py
  1ba78274c8c56a1b2b6cbd525fb341719a2ce4a7

recovery_operations.py
  119571e8ad8a5663d20beff0ab82c85c14dfc4eb

recovery_engine.py
  9a3f1898c7420198ff33d2b067a6fa2a6ac8618d
```

Accepted corrected TGZ:

```text
stage3c-phase4-recovery-durability-inventory-checkpoint-classification-corrected-results-20260712-020339.tgz
sha256
  c263814a506b7eb145a5fde891bb55ca1eedbb8b992096769f3505be31ce1d62
```

Preserved failed attempt:

```text
add_intent and mark_applied were detected but initially unclassified
UNKNOWN=0 correctly failed
both are now frozen as transaction-metadata
```

## Stage 3-C Phase 4 Gate 5B — integrated durability

```text
source integration             29/29 PASS
recovery replay                55/55 PASS
recovery verifier              82/82 PASS
durability replay              64/64 PASS
durability verifier            53/53 PASS
focused exercises              20/20 PASS
trace verifier                 29/29 PASS
overall verifier               36/36 PASS
result-index
  878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce
```

Accepted final Phase 4 TGZ:

```text
stage3c-phase4-integrated-durability-results-20260712-082135.tgz
sha256
  76bb78f200d9836d96f677cc1eca1e2f1483186f3655efa17a8e1f2361bd0187
size
  23,917,838 bytes
members
  325
indexed files
  294
```

Integrated source blobs:

```text
recovery_common.py
  3183ba0861ef45e7a395201bec0085f3f69fb248

recovery_operations.py
  8a307065e00fd7a7332541f4911c5478945374ee

recovery_engine.py
  aebf5b9a33d163f7f8758f785ca621c94c0e478b

recovery_durability.py
  61bfb859f73acccb0dfcce1d2a630bfd1ffc2d3f
```

Trace evidence:

```text
files                  25
events             42,941
ordering violations     0
```

Phase 4 final status:

```text
STAGE3C_PHASE4=FROZEN
```

## Product lock identity

```text
product kind
  upstream-cpython-android-package

Python
  3.14.6

source head
  c63aec69bd59c55314c06c23f4c22c03de76fe45

host
  aarch64-linux-android

Android API
  24

NDK
  27.3.13750724

source archive
  python-3.14.6-aarch64-linux-android.tar.gz

source archive size
  22,346,066 bytes

source archive sha256
  a16e0433b6f7e69c4634b52ce582d4d387447fbcfed797425f669ac224631f4f

package prefix root
  prefix

SOABI
  cpython-314-aarch64-linux-android

MULTIARCH
  aarch64-linux-android
```

## Active next boundary — Phase 5 Gate 1

```text
status
  ACTIVE — authoritative Termux result pending

workflow
  experiments/stage3c-installed-runtime-baseline/run-installed-runtime-baseline.sh

results
  results/termux/stage3c-phase5-installed-runtime-baseline/

verifier
  80/80 checks
```

Gate 1 must validate the runtime after installation through the frozen Phase 4 engine. Direct use of the Stage 3-B promoted prefix as the runtime under test is forbidden.
