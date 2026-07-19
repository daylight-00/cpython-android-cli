# Epoch 2 upstream-thin detailed plan authority

This experiment directory machine-checks ADR-0007 and the canonical detailed work/gate plan.

## Verify

```bash
python experiments/epoch2-upstream-thin-plan/verify-plan.py --root .
python experiments/epoch2-upstream-thin-plan/test-verifier.py
```

The verifier checks:

- exact raw-plan identity;
- mandatory API-36 Epoch 2 research;
- absence of automatic Epoch 3 adoption;
- UT-0 through UT-7;
- E2-G1 through E2-G8;
- E3-I1 through E3-I4;
- E3-G1 through E3-G10;
- charters, roadmap, context, ownership, intake, and index agreement;
- deferred Note9 and waived emulator boundaries;
- Epoch 4 source-producer ownership.
