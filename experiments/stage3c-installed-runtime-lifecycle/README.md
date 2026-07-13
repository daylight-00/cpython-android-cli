# Stage 3-C Phase 5 Installed Runtime Lifecycle

> **Current boundary:** Gate 3C addon lifecycle design frozen; target implementation pending

Current authority:

```text
Gate 3B preserve-and-report product acceptance   FROZEN
Gate 3C design verifier                          73/73 PASS
Gate 3C target matrix                            50 scenarios
Gate 3D final runtime-base uninstall             DEFERRED
upgrade/downgrade                                DEFERRED
```

Gate 3C design files:

```text
GATE3C_ADDON_LIFECYCLE_DESIGN.md
gate3c-addon-lifecycle-matrix.json
verify-gate3c-addon-lifecycle-design.py
run-gate3c-addon-lifecycle-design.sh
```

The two addons independently require exact runtime-base and do not depend on each other. Target acceptance must test both install and removal orders.

---

The remaining Gate 3A diagnostic section is retained as historical workflow text. Its old `ACTIVE` marker is superseded by the frozen Gate 3A, Gate 2R, Gate 3B0, and Gate 3B results listed above.

# Stage 3-C Phase 5 Gate 3A: Reinstall and Repair Diagnostic Census

> **Status:** ACTIVE — authoritative Termux diagnostic pending
> **Prerequisites:** frozen Phase 5 Gates 1–2 and frozen Phase 4 engine
> **This workflow is diagnostic evidence, not Gate 3A product acceptance.**

## Diagnostic question

> Which same-version reinstall and registered-corruption classes are actually supported by the frozen Phase 4 engine, and what durable recovery state remains when a registered leaf is missing?

## Why this census precedes product acceptance

Static audit of the frozen engine shows two different repair paths:

```text
registered path exists but differs
  → repair / repair-dir

registered non-directory path is absent
  → repair plan
  → durable_move(absent path, backup)
  → expected FileNotFoundError
```

The second behavior was not closed by prior target evidence. Gate 3A must record it before deciding whether an architecture intervention is required.

A diagnostic PASS means the target observations match the source-derived classifications. It does **not** mean missing-leaf repair works or Gate 3A is frozen.

## Scenario matrix

Seven independent installation roots are cloned from one fresh frozen runtime-base installation. Clone inode separation is verified.

```text
exact-noop
regular-bytes
regular-mode
symlink-target
regular-wrong-type
missing-regular
missing-symlink
```

Expected classifications:

```text
exact-noop
  exact-same-version-noop

regular-bytes
regular-mode
symlink-target
regular-wrong-type
  in-place-registered-repair-supported

missing-regular
missing-symlink
  missing-leaf-repair-unsupported
```

## Exact NOOP requirements

```text
noop                         true
action_counts                {noop: 714}
mutation_count               0
registry identity            unchanged
portable identity            unchanged
transactions                 empty
engine verify                PASS
```

## In-place repair requirements

For each supported scenario:

```text
pre-repair engine verify     exactly one bad path
install action_counts        {noop: 713, repair: 1}
mutation_count               2
post-repair engine verify    PASS
registry identity            unchanged
portable identity            restored to f860caf...
transactions                 empty
final path                   exact manifest identity
```

## Missing-leaf diagnostic requirements

For each missing regular or symlink leaf, the source-derived expectation is:

```text
pre-repair verify            exactly one missing bad path
install                      rc=44 / FileNotFoundError
journal before recovery      APPLYING
first recover                ROLLED_BACK
journal after recovery       ROLLED_BACK and retained
second recover               NOOP_ROLLED_BACK
post-recovery verify         same missing bad path
registry row                 still present
leaf                         still absent
```

This is an expected diagnostic classification, not an accepted product property.

## Independent verification

```text
scenario runner checks       17
independent verifier checks  31
```

The verifier reopens raw engine outputs and scenario journals rather than trusting scenario-level `pass` fields.

## Run

Use a fresh extraction of the accepted Phase 4 archive:

```sh
cd "$HOME/projects/cpython-android-cli"

git fetch origin agent/phase5-gate3a-reinstall-repair-diagnostic
git switch --detach origin/agent/phase5-gate3a-reinstall-repair-diagnostic

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
  bash experiments/stage3c-installed-runtime-lifecycle/run-gate3a-reinstall-repair-diagnostic.sh
```

## Expected markers

```text
GATE3A_EXACT_REINSTALL_NOOP=714/714 PASS
GATE3A_IN_PLACE_REPAIRS=4/4 CLASSIFIED
GATE3A_MISSING_LEAF_REPAIR=2/2 UNSUPPORTED_CLASSIFIED
GATE3A_RECOVERY_RESIDUE=2/2 CLASSIFIED
GATE3A_DIAGNOSTIC_VERIFICATION=31/31 PASS
GATE3A_PRODUCT_ACCEPTANCE=NOT_CLAIMED
STAGE3C_PHASE5_GATE3A_REINSTALL_REPAIR_DIAGNOSTIC=PASS
```

## Results and upload

```sh
RESULTS="$PWD/results/termux/stage3c-phase5-gate3a-reinstall-repair-diagnostic"
ARCHIVE="$HOME/Downloads/stage3c-phase5-gate3a-reinstall-repair-diagnostic-results-$(date +%Y%m%d-%H%M%S).tgz"

tar czf "$ARCHIVE" "$RESULTS"
printf 'upload: %s\n' "$ARCHIVE"
```

## Decision after target evidence

```text
missing-leaf behavior matches source-derived unsupported classification
  → preserve evidence
  → decide whether explicit Phase 4 architecture intervention is required
  → do not call Gate 3A frozen

missing-leaf repair unexpectedly succeeds
  → inspect exact target evidence and source-path assumptions
  → do not broaden the claim without an independent explanation
```

## Claim boundary

A diagnostic PASS proves only that exact NOOP, supported in-place repairs, and missing-leaf failure/recovery behavior have been classified on Termux.

It does not prove Gate 3A product acceptance, preservation policy, addon lifecycle, uninstall, upgrade, or downgrade.
