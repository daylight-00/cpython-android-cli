# Stage 3-C Phase 5 Installed Runtime Lifecycle

> **Current boundary:** Gate 3D frozen; Gate 4 second-product authority and design pending

Current authority:

```text
Gate 3B preserve-and-report product acceptance   FROZEN
Gate 3C design verifier                          FROZEN 73/73
Gate 3C target matrix                            50 scenarios
Gate 3C target runner/verifier                   FROZEN 50/50 + 103/103 + 27/27
Gate 3D final runtime-base uninstall design      FROZEN 108/108, 44 scenarios
Gate 3D target acceptance                        FROZEN 44/44 + 138/138 + 37/37
upgrade/downgrade                                ACTIVE — second product authority/design pending
```


Gate 3D design files:

```text
GATE3D_FINAL_UNINSTALL_DESIGN.md
gate3d-final-uninstall-matrix.json
verify-gate3d-final-uninstall-design.py
run-gate3d-final-uninstall-design.sh
```

The Gate 3D matrix contains 44 scenarios across preflight rejection, valid/guarded teardown, residual ownership, crash recovery, locking, and final-state/evidence audit. It explicitly separates an empty registry, absence of matching owned payload, approved residual presence, transaction/tombstone state, and whether the prefix root is physically empty.

Gate 3D target files:

```text
gate3d_final_uninstall_support.py
run-gate3d-final-uninstall.py
verify-gate3d-final-uninstall.py
finalize-gate3d-evidence.py
run-gate3d-final-uninstall-termux.sh
```

The authoritative Termux workflow consumed both frozen archives, executed all 44 scenarios with raw process evidence, passed 138 independent checks, and emitted a safe `.tar.zst` archive with an exact 845-file root index. External audit passed 37/37. The accepted archive SHA-256 is `579b880495098e9a46b40e2d96c9555178d0ad8c725d40768e6b854227d66143`; the root result-index SHA-256 is `5f9aa64cb4e0679a4784c9c3b8ebd6d8d91829704984672186dc9f9c0d96ed60`.

Gate 4 is open only for second-product authority acquisition and design. No upgrade/downgrade policy or target claim is frozen.

Gate 3C implementation files:

```text
GATE3C_ADDON_LIFECYCLE_DESIGN.md
gate3c-addon-lifecycle-matrix.json
gate3c_addon_lifecycle_support.py
run-gate3c-addon-lifecycle.py
verify-gate3c-addon-lifecycle.py
finalize-gate3c-evidence.py
run-gate3c-addon-lifecycle-termux.sh
```

The target wrapper consumes the byte-exact frozen Gate 3B archive, independently verifies its root index and three artifact identities, executes all 50 scenarios, then emits a `.tar.zst` archive on PASS or FAIL. The two addons independently require exact runtime-base and do not depend on each other.

The first complete target execution passed all 50 scenarios and all 102 repository verifier checks, but independent archive inspection did not accept it. The archive contained one external absolute venv symlink and omitted one symlink-directory entry from the root result-index. The correction moves smoke-test scratch state outside the evidence tree, adds a pre-archive result-tree safety gate, and indexes symlinks before directory classification. The corrected verifier surface is 103 checks. The corrected authoritative archive is `stage3c-phase5-gate3c-addon-lifecycle-results-20260713T033412Z.tar.zst` with SHA-256 `43fa4bbbfdfb7fc7562c3881771a625662422980b352482da19ab2b3a07dee7a`; its root result-index is `fb51d53ab0a4605159e58208c374017c2de9fed6ba924f08d98cfabf82ce6c7c`, and the external acceptance audit passed 27/27.

Recovery retention follows the frozen engine: PREPARED/APPLYING rollback retains one `ROLLED_BACK` audit tombstone; COMMITTED recovery cleans its transaction. Normal successful lifecycle roots still require zero transaction residue.

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
