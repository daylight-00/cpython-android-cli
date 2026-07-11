# Stage 3-C Phase 4 Installation Recovery Result

> **Status:** PASS — Gate 3 abrupt recovery and lock contention closed
> **Target:** Termux on Android arm64
> **Result archive:** `stage3c-phase4-installation-recovery-independent-seed-copy-corrected-results-20260712-004138.tgz`

## Result archive identity

```text
sha256
  3c164f54e4f205ba8ba889274656375ce2c0cf137f65c6ccf6fb2cafab889bd6

size
  22,902,773 bytes

members
  151

regular files
  137

directories
  14

symlinks / hardlinks / special entries
  0 / 0 / 0

unsafe member names
  0
```

## Machine result

```text
recovery scenarios       55/55 PASS
independent verifier     82/82 PASS
workflow return codes     all 0
failed checks                 []
```

```text
STAGE3C_PHASE4_RECOVERY_SCENARIOS=PASS
STAGE3C_PHASE4_INSTALLATION_RECOVERY=PASS
```

## Result index

```text
sha256
  f5ba124ebb9752b45d60f027474a399adf61fc5db033c1165a79664cbfc743bd

indexed files
  134

independent hash, size, and mode mismatches
  0
```

## Accepted input identities

```text
Gate 2 result index
  0041f1c3c73dc7a62291b6c3b244ac885d9bad6799d4115280febc20f61384da

Gate 1 contract index
  79e3c173639047bc23b7dbe3c2135abe8f0b868d787735c094cbe06749c7dde3

runtime-base archive
  2ba7c309b1700926dc423eb4305a9eba1a53c023a11617e490b151be71e49743

development-addon archive
  f77ea24c92fdd982cd32e172b2d38134f1d785b1f106d1bfe36a9bffa9cc8eea

test-addon archive
  02a1fad1af5528a4e910f0eb3370f4a2696da4f78067586e8b62f2a10fb4c9b1
```

## Corrected scenario isolation

The first target attempt failed while creating hardlinked seed copies. The corrected target result uses independent regular-file copies and preserves symlinks without sharing regular-file inodes between seed and scenario roots.

Preserved failure record:

```text
docs/evidence/STAGE3C_PHASE4_RECOVERY_SEED_CLONE_FAILURE.md
```

## Abrupt process-exit matrix

```text
exit 90
  journal state PREPARED
  mutations 0
  recovery ROLLED_BACK
  restored 0

exit 93
  journal state APPLYING
  one durable INTENT
  filesystem mutation not observed
  recovery ROLLED_BACK
  restored 0

exit 91 — install
  five APPLIED created mutations
  recovery ROLLED_BACK
  restored 5

exit 91 — uninstall
  five APPLIED removed mutations
  recovery ROLLED_BACK
  restored 5

exit 91 — registry pre-commit
  repaired payload APPLIED
  registry APPLIED
  recovery ROLLED_BACK
  restored 2

exit 92 — committed pre-cleanup
  state COMMITTED
  recovery FINALIZED_COMMIT
  rollback not performed
```

All injected crash processes exited without producing a normal operation result, proving that recovery occurred in a later process rather than through an in-process exception handler.

## Registry pre-commit recovery

The registered development path used for repair was:

```text
include/openssl/aes.h
```

After the payload and registry were both APPLIED but before COMMITTED:

```text
recovery restored prior payload and registry
post-recovery verification detected the original intentional corruption
normal repair then produced
  NOOP 453
  repair 1
  mutations 2
final registry
  artifacts 2
  owned paths 1168
  bad paths 0
```

## COMMITTED cleanup

A crash after the durable COMMITTED journal left the transaction directory present. Recovery classified it as committed, removed transaction staging and backup state, and preserved the committed payload and registry.

```text
recovery action
  FINALIZED_COMMIT

final registry
  artifacts 2
  owned paths 1168
  bad paths 0
```

## Lock contention

```text
holder
  exclusive flock acquired
  ready marker observed
  exit 0

nonblocking contender
  installation lock busy
  rejected
  no mutation

post-release development install
  create 454
  mutations 455
  registry 1168
  bad paths 0
```

## Idempotence

A retained ROLLED_BACK transaction was recovered a second time:

```text
action
  NOOP_ROLLED_BACK

restored
  0
```

## Final snapshots

```text
prepared-final
  runtime-base
  714/714 observed paths match

intent-final
  runtime-base
  714/714 observed paths match

applying-install-final
  runtime-base + development-addon
  1168/1168 observed paths match

applying-uninstall-final
  runtime-base + development-addon
  1168/1168 observed paths match

registry-crash-final
  runtime-base + development-addon
  1168/1168 observed paths match
```

Final installation fingerprints:

```text
runtime-only roots
  1c2e32b620ca3f6b2099b5133aa77b135521ccabd60bb9c243d51996f62113f0

runtime + development roots
  0ad59be690d47b02d07dcad380e101453070fca7240745efef47e7ab2bc70e41
```

## Retained evidence

```text
scenario logs
  40/40 canonical JSON

registry snapshots
  5

independently observed path snapshots
  5

snapshot mismatches
  0
```

## Input mutation

```text
input entries before/after
  87 / 87

input fingerprint before/after
  5abf67d8e4d8b23ce569b61aba8ce1e96e69d6c894afcb7e6078ef9842d59d0a

special paths
  0
```

## Closed claims

This result proves recovery for the tested isolated PREPARED, durable INTENT, durable APPLYING, registry-applied pre-commit, and COMMITTED-before-cleanup process-exit boundaries. It also proves retained ROLLED_BACK idempotence and rejection of a nonblocking concurrent contender while the installation lock is held.

## Claim boundary

This result does not prove persistence across kernel panic, sudden power loss, storage-controller failure, or a crash inside one non-atomic filesystem primitive. It also does not prove adversarial external mutation, lock fairness, upgrade or downgrade, or installed runtime behavior.
