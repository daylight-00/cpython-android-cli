# Gate 4 Cross-Version Transition

## Current state

```text
Gate 4A  second-product authority                 FROZEN PASS
Gate 4B  transition contract design               DESIGN FROZEN — 66 scenarios
Gate 4C  transition coordinator implementation    pending
Gate 4D  bidirectional Termux validation           pending
Gate 4E  independent transition freeze             pending
```

Gate 4B freezes a dedicated whole-product transition contract between the exact CPython 3.14.5 and 3.14.6 authorities. Ordinary artifact installation remains same-product only.

The design preserves the frozen registry schema and Phase 4 engine sources. A future coordinator uses one recovery-compatible transaction over the complete selected artifact topology, rejects modified source-owned content before mutation, preserves non-colliding unowned descendants, and supports exact rollback or target finalization.

Files:

```text
GATE4B_TRANSITION_CONTRACT_DESIGN.md
gate4b-cross-version-inventory.json
gate4b-transition-matrix.json
verify-gate4b-transition-design.py
run-gate4b-transition-design.sh
```

Run the repository design verifier:

```sh
bash experiments/stage3c-gate4-transition/run-gate4b-transition-design.sh
```

No upgrade or downgrade is executed by the design verifier.

Frozen design records:

```text
docs/evidence/STAGE3C_PHASE5_GATE4B_TRANSITION_CONTRACT_DESIGN_RESULT.md
experiments/stage3c-gate4-transition/gate4b-transition-design-authority.json
```
