# Stage 3-C Phase 4I: Missing Registered Leaf Repair Intervention

> **Status:** ACTIVE — authoritative Termux rerun pending
> **Authority:** `docs/handoff/PHASE5_GATE3A_INTERVENTION_DECISION_20260712.md`
> **Product acceptance:** not claimed by this workflow

## Intervention question

> Can an absent registered regular or symlink leaf be repaired to the frozen manifest identity while preserving the existing crash-recovery contract?

## Confirmed defect

The frozen engine plans an absent registered non-directory as `repair`, records a `replaced` intent, and attempts to move a nonexistent source to backup. Authoritative Gate 3A0 evidence produced `FileNotFoundError`, a retained `ROLLED_BACK` journal, a retained registry row, and an absent leaf.

Frozen diagnostic evidence:

```text
docs/evidence/STAGE3C_PHASE5_GATE3A_REINSTALL_REPAIR_DIAGNOSTIC_RESULT.md
```

## Candidate correction

The frozen source remains available unchanged. The intervention adapter changes only the execution semantics of a `replaced` intent whose registered source is absent:

```text
existing mismatch
  replaced intent
  backup current path
  publish frozen member

missing registered leaf
  created intent
  skip nonexistent backup move
  publish frozen member
```

Files:

```text
experiments/stage3c-installation-recovery/
├── recovery_operations_missing_leaf.py
└── recovery_engine_missing_leaf.py
```

The adapter reuses the frozen `created` rollback behavior:

```text
created INTENT before publish
  recovery sees no path and performs no removal

created APPLIED after publish
  recovery removes the published path

COMMITTED
  recovery finalizes the transaction and preserves the repaired path
```

No journal schema, recovery operation, registry schema, manifest, archive, ownership, uninstall, or addon-policy change is introduced.

## Success scenarios

Seven independent roots:

```text
exact-noop
regular-bytes
regular-mode
regular-wrong-type
symlink-target
missing-regular
missing-symlink
```

Required missing-leaf result:

```text
pre-verify                  one bad path
install                     PASS
install actions             noop 713 / repair 1
mutation count              2
post-verify                 PASS
registry identity           unchanged
portable payload identity   f860caf... exact
transaction residue         0
final leaf                  exact manifest identity
```

The four existing mismatch classes and exact NOOP are regression controls.

## Crash-recovery matrix

Each missing leaf type is tested at six boundaries:

```text
prepared
intent-1
mutation-1
intent-2
mutation-2
committed
```

Total crash scenarios:

```text
2 leaf types × 6 boundaries = 12
```

Expected pre-commit recovery:

```text
prepared
  mutations []
  restored_count 0

intent-1
  created INTENT
  restored_count 0

mutation-1
  created APPLIED
  restored_count 1

intent-2
  created APPLIED + registry INTENT
  restored_count 2

mutation-2
  created APPLIED + registry APPLIED
  restored_count 2

all pre-commit cases
  ROLLED_BACK
  original missing state restored
  prior registry exact
  second recovery NOOP_ROLLED_BACK
```

Expected committed recovery:

```text
journal COMMITTED
recover FINALIZED_COMMIT
repaired leaf exact
registry exact
transaction removed
second recover transaction_count 0
```

## Verification

```text
scenario runner checks       39
independent verifier checks  51
```

The independent verifier reopens raw process records, engine JSON, journal inventories, clone inode evidence, final candidate identities, and registry and portable fingerprints.

## Run

```sh
cd "$HOME/projects/cpython-android-cli"

git fetch origin agent/phase4-missing-leaf-repair-intervention
git switch --detach origin/agent/phase4-missing-leaf-repair-intervention

git log -1 --oneline

PHASE4_ARCHIVE="$HOME/Downloads/stage3c-phase4-integrated-durability-results-20260712-082135.tgz"
PHASE4_EXTRACT="$PREFIX/tmp/stage3c-phase4-integrated-durability-accepted"

printf '%s  %s\n' \
  '76bb78f200d9836d96f677cc1eca1e2f1483186f3655efa17a8e1f2361bd0187' \
  "$PHASE4_ARCHIVE" | sha256sum -c -

rm -rf "$PHASE4_EXTRACT"
mkdir -p "$PHASE4_EXTRACT"
tar xzf "$PHASE4_ARCHIVE" -C "$PHASE4_EXTRACT"

PHASE4_RESULTS="$(find "$PHASE4_EXTRACT" \
  -type d \
  -path '*/results/termux/stage3c-phase4-integrated-durability' \
  -print -quit)"

test -n "$PHASE4_RESULTS"

PHASE4_RESULTS="$PHASE4_RESULTS" \
  bash experiments/stage3c-missing-leaf-repair-intervention/run-missing-leaf-repair-intervention.sh
```

## Expected markers

```text
PHASE4I_EXACT_REINSTALL_NOOP=PASS
PHASE4I_IN_PLACE_REPAIR_REGRESSION=4/4 PASS
PHASE4I_MISSING_LEAF_REPAIR=2/2 PASS
PHASE4I_CRASH_RECOVERY=12/12 PASS
PHASE4I_INTERVENTION_VERIFICATION=51/51 PASS
PHASE4I_GATE3A_PRODUCT_ACCEPTANCE=NOT_CLAIMED
STAGE3C_PHASE4_MISSING_LEAF_REPAIR_INTERVENTION=PASS
```

## Upload

```sh
RESULTS="$PWD/results/termux/stage3c-phase4-missing-leaf-repair-intervention"
ARCHIVE="$HOME/Downloads/stage3c-phase4-missing-leaf-repair-intervention-results-$(date +%Y%m%d-%H%M%S).tgz"

tar czf "$ARCHIVE" "$RESULTS"
printf 'upload: %s\n' "$ARCHIVE"
```

## Claim boundary

A PASS proves only the candidate intervention behavior and crash recovery matrix. Gate 3A product acceptance, post-repair runtime/HTTPS/uv/native closure, and Gate 1 or Gate 2 regression remain open.
