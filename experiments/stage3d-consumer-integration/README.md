# Stage 3-D Consumer Integration

This experiment family begins only after Stage 3-C Gate 4E froze exact two-product transition behavior.

## Current state

```text
Gate 1  scope and consumer authority design             FROZEN
Gate 2  read-only Termux consumer discovery census      pending
Gate 3  system-Python integration contract              pending
Gate 4  target implementation and validation            pending
Gate 5  independent consumer-integration freeze         pending
Gate 6  optional managed-Python feasibility research    deferred
```

Run the repository design verifier:

```bash
bash experiments/stage3d-consumer-integration/run-gate1-consumer-authority-design.sh
```

Gate 1 is design-only. It does not create interpreter links, modify uv state, or claim target discovery behavior.
