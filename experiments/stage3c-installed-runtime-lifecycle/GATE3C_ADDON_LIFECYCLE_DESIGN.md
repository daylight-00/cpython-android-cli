# Stage 3-C Phase 5 Gate 3C: Addon Lifecycle and Dependency Enforcement Design

> **Status:** FROZEN PASS — design and corrected Termux target evidence accepted
> **Prerequisite:** frozen Gate 3B preserve-and-report product acceptance
> **Target:** Termux on Android arm64

## Product question

> Can the frozen development-addon and test-addon compose over the exact runtime-base, enforce only their declared dependency and ownership boundaries, recover transactionally, and leave runtime-base exact and functional after either addon removal order?

## Frozen dependency boundary

Both addons require only the exact runtime-base identity.

```text
development-addon -> runtime-base
test-addon        -> runtime-base
```

`test-addon` does not depend on `development-addon`. In plain terms: test-addon does not depend on development-addon. Gate 3C therefore must not invent such an edge. It must prove both composition orders and both addon-removal orders:

```text
runtime -> development -> test
runtime -> test -> development

composed -> remove test -> runtime + development
composed -> remove development -> runtime + test
```

Runtime-base uninstall remains blocked while any addon is installed. Gate 3D final runtime-base uninstall remains deferred.

## Frozen identities

```text
artifact               archive sha256                                                     manifest sha256                                                   owned
runtime-base            2ba7c309b1700926dc423eb4305a9eba1a53c023a11617e490b151be71e49743  ce48849c9c88c9296264d6a917c3b55b0433e0d67bdda06579d6f18d701f285a   714
development-addon       f77ea24c92fdd982cd32e172b2d38134f1d785b1f106d1bfe36a9bffa9cc8eea  9a01655d63044ab126fd71236ca2cb814221317ee9b6b44fd2417fa5535a8b2a   454
test-addon              02a1fad1af5528a4e910f0eb3370f4a2696da4f78067586e8b62f2a10fb4c9b1  47d9f2e24e74b23e34ae6bfa95a0df22ec7cf9505e3e189dc3d6bdf2dc1c8b5f  1788
```

```text
manifest index
  540adfaacf9387e80a258dfa3db8c299ad775d99e771c475a89dfc61de6868c1

installation contract index
  79e3c173639047bc23b7dbe3c2135abe8f0b868d787735c094cbe06749c7dde3

Gate 3B archive
  0be850523ddc9b0fcb652d47f4414d0772dea1d8767f23490c3655576683270b

Gate 3B root result-index
  f3e0bd34c61f5b1e0960d002175478b112641fa71f0e914ec712e6c514e52fe9
```

## Registry states

```text
empty                    0 artifacts      0 owned paths
runtime                  1 artifact     714 owned paths
runtime + development    2 artifacts   1168 owned paths
runtime + test           2 artifacts   2502 owned paths
composed                 3 artifacts   2956 owned paths
```

The shared namespace is exactly:

```text
lib
lib/python3.14
```

These directories are owned by runtime-base and are non-owning structural references for both addons.

## Acceptance matrix

The machine matrix contains exactly 50 scenarios:

```text
preflight and rejection       10
composition and repair        10
addon uninstall                9
crash recovery                12
lock exclusion                 2
behavior and final audit       7
```

Canonical matrix:

```text
experiments/stage3c-installed-runtime-lifecycle/gate3c-addon-lifecycle-matrix.json
```

### Preflight

Gate 3C rejects before mutation:

```text
addon install without runtime-base
addon install with the wrong runtime-base artifact identity
runtime-base uninstall while development-addon is installed
runtime-base uninstall while test-addon is installed
runtime-base uninstall while both addons are installed
unowned required-leaf collision
adversarial other-owner collision
```

Every rejection records before/after snapshots, registry state, transaction inventory, raw process output, and the real return code.

### Composition and repair

Gate 3C proves:

```text
runtime-only                         1 / 714
runtime + development               2 / 1168
runtime + test                      2 / 2502
full composition in both orders     3 / 2956
exact addon reinstall               NOOP / zero mutations
runtime reinstall with addons       714 NOOP / addon registry unchanged
one development mismatch            one repair
one missing test leaf               one corrected repair
```

### Addon uninstall and preservation

Either addon may be removed first because there is no inter-addon prerequisite.

Modified addon-owned leaves are preserved, reported, and deregistered. Unowned file and directory sentinels remain unowned and unchanged. Owned directories are removed only when empty. Shared structural namespace remains runtime-owned and is never adopted by an addon.

A later addon reinstall over a preserved modified residual must reject it as an unowned collision rather than silently adopt or overwrite it.

### Crash recovery

The matrix covers four addon operations at three accepted crash boundaries:

```text
install development-addon
install test-addon
uninstall development-addon
uninstall test-addon

PREPARED       rc 90
late APPLYING  rc 93
COMMITTED      rc 92
```

PREPARED and late APPLYING restore the exact prior payload and registry. The frozen engine then retains one `ROLLED_BACK` transaction tombstone as durable audit state; the second recovery reports `NOOP_ROLLED_BACK`. COMMITTED finalizes the exact new state, removes its transaction, and the second recovery observes zero transactions. The implementation must preserve this already accepted Gate 3B engine behavior rather than rewriting it to satisfy an over-broad zero-residue interpretation.

### Behavior probes

Target acceptance must prove:

```text
development-addon
  include/python3.14/Python.h present

test-addon
  import test.support
  selected offline tests: test_json and test_hashlib

after test-addon removal
  test payload absent

after development-addon removal
  development payload absent

after all addon removals
  complete frozen runtime regression
  exact 1 artifact / 714 owned rows
  zero transaction residue
```

## Evidence contract

One Termux wrapper must verify accepted input hashes, extract inputs freshly, create inode-separated roots, capture stdout and stderr synchronously, preserve real process return codes, write canonical JSON, reject external/special result-tree entries, recompute a complete root result-index including safe symlinks, and create a new `.tar.zst` archive on PASS or FAIL.

Historical `.tgz` evidence remains immutable.

## Local design verification

```text
bash experiments/stage3c-installed-runtime-lifecycle/run-gate3c-addon-lifecycle-design.sh
```

Expected markers:

```text
GATE3C_ADDON_LIFECYCLE_DESIGN_VERIFICATION=73/73 PASS
STAGE3C_PHASE5_GATE3C_ADDON_LIFECYCLE_DESIGN=PASS
```

## Claim boundary

The design PASS freezes the policy-bounded matrix and verifies its consistency with frozen Phase 2, Phase 3, Phase 4, corrected-engine, and Gate 3B authorities.

The independently inspected corrected Termux archive closes the target addon lifecycle, recovery, dependency-enforcement, and post-addon runtime regression claims. Final multi-artifact/runtime-base uninstall, upgrade, and downgrade remain separate Gate 3D and Gate 4 boundaries.
