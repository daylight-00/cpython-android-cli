# Phase 5 Gate 3D Final Uninstall and Ownership Boundary Handoff — 2026-07-13

> **Status:** TARGET IMPLEMENTATION READY — authoritative Termux evidence pending
> **Prerequisites:** frozen Gate 3B preserve-and-report acceptance and frozen Gate 3C addon lifecycle acceptance
> **Target:** Termux on Android arm64

## Frozen prerequisites

```text
Gate 3B runtime-base preserve-and-report archive
  stage3c-phase5-gate3b-preservation-acceptance-results-20260713-024946.tgz
  sha256 0be850523ddc9b0fcb652d47f4414d0772dea1d8767f23490c3655576683270b
  result-index f3e0bd34c61f5b1e0960d002175478b112641fa71f0e914ec712e6c514e52fe9
  29/29 scenarios + 62/62 verifier PASS

Gate 3C addon lifecycle archive
  stage3c-phase5-gate3c-addon-lifecycle-results-20260713T033412Z.tar.zst
  sha256 43fa4bbbfdfb7fc7562c3881771a625662422980b352482da19ab2b3a07dee7a
  result-index fb51d53ab0a4605159e58208c374017c2de9fed6ba924f08d98cfabf82ce6c7c
  50/50 scenarios + 103/103 verifier + 27/27 external audit PASS
```

## Gate 3D question

> Can the complete frozen three-artifact product be torn down through valid addon removal followed by runtime-base removal while preserving exact ownership, residual reporting, transaction recovery, and final registry/filesystem audit boundaries?

Gate 3D is an integration boundary. It must not reopen Gate 3B's runtime-base preserve-and-report policy or Gate 3C's addon dependency policy.

## Required starting states

At minimum, the design must distinguish:

```text
fully composed
  runtime-base + development-addon + test-addon

runtime plus one addon
  runtime-base + development-addon
  runtime-base + test-addon

runtime-only
  runtime-base
```

Runtime-base uninstall remains invalid until all addons are absent. Both valid addon-removal orders were already accepted by Gate 3C and must be consumed as frozen authorities rather than reinterpreted.

## Required final-state classes

```text
exact-owned teardown
  registry empty
  all matching owned payload absent
  no transaction residue

modified-owned residual
  modified leaf preserved and reported
  registry empty after committed uninstall
  only required non-empty ancestors retained

unowned sentinel residual
  sentinel preserved, unowned, and unchanged
  registry empty
  only required non-empty ancestors retained

rollback recovery
  exact prior product/registry restored
  accepted ROLLED_BACK audit tombstone retained
  second recovery NOOP_ROLLED_BACK

committed recovery
  exact accepted final residual state
  transaction cleaned
  second recovery observes zero transactions
```

“Final empty state” means an empty registry and no remaining matching owned payload. It does not mean deleting contract-approved modified or unowned residuals.

## Design requirements

The Gate 3D matrix must include:

```text
preflight rejection with addons present and zero mutation
both valid composed-product teardown orders
exact runtime-only final uninstall
modified runtime-owned regular and symlink residuals
unowned file and directory sentinels
owned-directory remove-only-when-empty behavior
structural namespace preservation
PREPARED / late APPLYING / COMMITTED recovery
raw stdout/stderr and real return codes
registry, payload, residual, and transaction snapshots
second-recovery idempotence
archive safety and complete root result-index
```

The design must explicitly separate:

```text
registry empty
owned payload absent
approved residuals present
filesystem root physically empty
```

These are not interchangeable states.

## Frozen design result

The repository-side matrix is now frozen at exactly 44 scenarios and the repository verifier passes 108/108 checks:

```text
preflight rejection                6
valid and guarded teardown         8
residual ownership                10
crash recovery                    12
lock exclusion                     2
final-state and evidence audit     6
```

Canonical design files:

```text
experiments/stage3c-installed-runtime-lifecycle/GATE3D_FINAL_UNINSTALL_DESIGN.md
experiments/stage3c-installed-runtime-lifecycle/gate3d-final-uninstall-matrix.json
experiments/stage3c-installed-runtime-lifecycle/verify-gate3d-final-uninstall-design.py
experiments/stage3c-installed-runtime-lifecycle/run-gate3d-final-uninstall-design.sh
```

The target runner, independent verifier, result-tree finalizer, and single Termux wrapper are implemented. Non-authoritative local semantic validation passes 44/44 scenarios and the independent verifier passes 138/138 checks. The local development run used fast-success only for successful setup operations; the target wrapper does not enable it.

Canonical target files:

```text
experiments/stage3c-installed-runtime-lifecycle/gate3d_final_uninstall_support.py
experiments/stage3c-installed-runtime-lifecycle/run-gate3d-final-uninstall.py
experiments/stage3c-installed-runtime-lifecycle/verify-gate3d-final-uninstall.py
experiments/stage3c-installed-runtime-lifecycle/finalize-gate3d-evidence.py
experiments/stage3c-installed-runtime-lifecycle/run-gate3d-final-uninstall-termux.sh
docs/evidence/STAGE3C_PHASE5_GATE3D_TARGET_IMPLEMENTATION_RESULT.md
```

The next task is one complete Termux execution followed by independent archive inspection. Do not authorize a target PASS from console markers alone.

## Claim boundary

Gate 3D does not include upgrade or downgrade. Gate 4 remains deferred until a second complete frozen product identity exists; synthetic version labels are not accepted.
