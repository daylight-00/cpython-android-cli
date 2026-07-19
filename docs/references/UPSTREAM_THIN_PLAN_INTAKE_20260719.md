# Upstream-Thin Plan Intake — 2026-07-19

The owner supplied a detailed external-session research and design document for the upstream-derived Android/Bionic standalone distribution.

## Preserved raw file

```text
docs/references/raw/2026-07-19-upstream-thin-plan/
  UPSTREAM_THIN_RESEARCH_AND_DESIGN_PLAN.md
```

```text
SHA-256  bebc4dc1fcd793775eb2a8a50c9d0b58e738f1e2f83282c597255aae196500ea
size     41858 bytes
```

The raw file is retained unchanged.

## Authority treatment

The raw document is not itself the final decision authority. It is adjudicated through:

- ADR-0007;
- `EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md`;
- the updated Epoch 2 and Epoch 3 charters;
- the recalibrated roadmap;
- the machine-readable plan authority and verifier.

## Important adjudications

1. API 36 is mandatory Epoch 2 research because the project reuses upstream-published sources, patches, recipes, module decisions, topology, and toolchain identity as practical while changing compile API.
2. API-36 output does not automatically become an Epoch 3 product input.
3. Experiment success does not imply product inclusion.
4. Epoch 3 must explicitly adopt, redesign, exclude, or defer every selectable result.
5. Full CPython/dependency source production remains Epoch 4.
