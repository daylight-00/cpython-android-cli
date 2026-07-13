# Stage 3-C Phase 5 Gate 3D Target Implementation Result

> **Status:** IMPLEMENTATION READY — authoritative Termux target evidence pending
> **Scope:** final multi-artifact teardown, runtime-base uninstall, residual ownership, recovery, locking, and evidence packaging

## Repository implementation

Gate 3D now has a target scenario runner, an independent verifier, a result-tree finalizer, and a single Termux wrapper:

```text
experiments/stage3c-installed-runtime-lifecycle/gate3d_final_uninstall_support.py
experiments/stage3c-installed-runtime-lifecycle/run-gate3d-final-uninstall.py
experiments/stage3c-installed-runtime-lifecycle/verify-gate3d-final-uninstall.py
experiments/stage3c-installed-runtime-lifecycle/finalize-gate3d-evidence.py
experiments/stage3c-installed-runtime-lifecycle/run-gate3d-final-uninstall-termux.sh
```

The implementation consumes the frozen Gate 3B and Gate 3C archives as immutable authorities. It does not change the transaction engine, operation layer, registry schema, artifact manifests, preserve-and-report policy, addon dependency policy, or the 44-scenario Gate 3D matrix.

## Implemented target workflow

The Termux wrapper:

```text
verifies exact Gate 3B and Gate 3C archive SHA-256 identities
checks both authority archives for unsafe members before extraction
verifies both authority root result-index identities
creates fresh inode-separated seed and scenario roots
executes all 44 scenarios with real engine return codes
captures raw stdout and stderr for every engine process
runs an independent 138-check verifier
writes result-tree-safety.json before packaging
recomputes the complete root result-index after final status files
creates a .tar.zst archive on PASS or FAIL
preserves workflow, runner, verifier, safety, and index return codes
```

The target wrapper does not enable the local development `GATE3C_FAST_SUCCESS` path.

## Scenario and verifier surface

```text
preflight rejection                 6
valid and guarded teardown          8
residual ownership                 10
crash recovery                     12
lock exclusion                      2
final-state/evidence audit          6
--------------------------------------
total                              44

independent target verifier       138 checks
```

The verifier reopens scenario JSON, raw process records, crash return codes, recovery actions, second-recovery topology, final registry state, exact residual membership, accepted authority identities, and evidence references. It does not trust scenario-level PASS markers alone.

## Local semantic validation

A non-authoritative local engine run completed:

```text
scenario runner                  44/44 PASS
independent verifier           138/138 PASS
registry intent ordinals
  exact-owned                         715
  modified-owned regular             714
  modified-owned symlink             714
  unowned file                        715
```

The local run used the development fast-success path for successful install/uninstall setup operations to keep the non-Android validation tractable. Crash injection, recovery, lock exclusion, registry transitions, residual preservation, canonical evidence, and the independent verifier used the actual frozen engine paths. This local result proves repository implementation consistency only; it is not Termux target acceptance.

## Recovery and final-state contract

The target evidence must distinguish:

```text
registry empty
matching owned payload absent
approved residual inventory exact
prefix root physically empty or non-empty
transaction inventory empty or one accepted ROLLED_BACK tombstone
```

PREPARED and late APPLYING recovery restore the runtime state and retain one `ROLLED_BACK` audit tombstone. COMMITTED recovery finalizes the accepted empty-registry/residual state and removes the transaction. A second recovery must be `NOOP_ROLLED_BACK` for pre-commit tombstones and observe zero transactions after a committed recovery.

## Required authority for Gate 3D closure

Repository readiness does not close Gate 3D. Closure requires one complete Termux archive that independently passes:

```text
44/44 target scenarios
138/138 independent verifier
archive path and member-type safety
root result-index exact membership and identities
raw stdout/stderr and process-return-code consistency
final registry / payload / residual / transaction audit
workflow, archive, index, and upload return codes
```

## Claim boundary

This result proves target implementation readiness only. It does not prove the Termux final uninstall boundary, close Gate 3D, or authorize upgrade/downgrade. Gate 3D remains target-evidence pending until the generated `.tar.zst` archive is independently inspected. Gate 4 remains deferred until a second complete frozen product identity exists.
