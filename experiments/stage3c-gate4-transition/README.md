# Gate 4 Cross-Version Transition

## Current state

```text
Gate 4A  second-product authority                 FROZEN PASS
Gate 4B  transition contract design               DESIGN FROZEN — 66 scenarios
Gate 4C  transition coordinator implementation    IMPLEMENTED — 69/69
Gate 4D  bidirectional Termux validation           READY — not started
Gate 4E  independent transition freeze             pending
```

Gate 4B freezes a dedicated whole-product transition contract between the exact CPython 3.14.5 and 3.14.6 authorities. Ordinary artifact installation remains same-product only.

Gate 4C implements that contract with a dedicated coordinator. It preserves the frozen registry schema and Phase 4 engine sources, uses one recovery-compatible transaction over the complete selected artifact topology, rejects modified source-owned content before mutation, preserves non-colliding unowned descendants, and supports exact rollback or target finalization. Real target transition acceptance remains Gate 4D work.

Files:

```text
GATE4B_TRANSITION_CONTRACT_DESIGN.md
gate4b-cross-version-inventory.json
gate4b-transition-matrix.json
verify-gate4b-transition-design.py
run-gate4b-transition-design.sh

GATE4C_TRANSITION_COORDINATOR_IMPLEMENTATION.md
gate4c-transition-authorities.json
transition_coordinator.py
verify-gate4c-transition-implementation.py
run-gate4c-transition-implementation.sh
```

Run the repository design verifier:

```sh
bash experiments/stage3c-gate4-transition/run-gate4b-transition-design.sh
```

No upgrade or downgrade is executed by the design verifier. The Gate 4C verifier uses synthetic authorities and does not claim target behavior.

Run the implementation verifier:

```sh
bash experiments/stage3c-gate4-transition/run-gate4c-transition-implementation.sh
```

Authority records:

```text
docs/evidence/STAGE3C_PHASE5_GATE4B_TRANSITION_CONTRACT_DESIGN_RESULT.md
experiments/stage3c-gate4-transition/gate4b-transition-design-authority.json

docs/evidence/STAGE3C_PHASE5_GATE4C_TRANSITION_COORDINATOR_IMPLEMENTATION_RESULT.md
experiments/stage3c-gate4-transition/gate4c-transition-implementation-authority.json
```
