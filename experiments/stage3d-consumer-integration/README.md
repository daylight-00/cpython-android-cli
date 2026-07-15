# Stage 3-D Consumer Integration

```text
Gate 1  scope and consumer authority design             FROZEN
Gate 2  read-only Termux consumer discovery census      FROZEN — 64/64
Gate 3  system-Python integration contract              FROZEN
Gate 4  target implementation and validation            ACTIVE NEXT — 48 scenarios
Gate 5  independent consumer-integration freeze         pending
Gate 6  optional managed-Python feasibility research    deferred
```

Run the Gate 3 repository verifier:

```bash
bash experiments/stage3d-consumer-integration/run-gate3-system-python-contract.sh
```

The exact contract covers `uv python find` and `uv venv` with an absolute interpreter path. `uv run` and `uv sync` are Gate 4 obligations.
