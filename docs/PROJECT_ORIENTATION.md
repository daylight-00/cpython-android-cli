# Project Orientation

This repository is the engineering authority for practical Android/Bionic CPython CLI work under Termux. It keeps launcher behavior, native closure, provenance, archive identity, installation ownership, recovery, cross-version transition, uv consumption, managed-Python distribution, publication, transport, acquisition, cache, and installation as separate authorities.

Epoch 2 adds a new product boundary: the standalone runtime archive becomes the lower-level product authority and the installer becomes its consumer. The repository remains the incubator and evidence archive until the standalone component is mature enough for history-preserving promotion into a separate product repository.

## Governing method

```text
understand -> reproduce -> measure -> compare -> design -> optimize
```

Complete independently audited Termux evidence outranks repository design, local reconstruction, static analysis, and chat memory. Never infer a broader claim from a narrower PASS.

## Current boundary

Epoch 1 is frozen through Stage 3-F. Stage 3-D remains frozen through Gate 6. Stage 3-E is complete with target 37/37 and independent 74/74 evidence. Stage 3-F is complete through Gate 5 after a documentation-integrity correction.

Epoch 2 Phase 0 is active. Its authority is limited to documentation, terminology, repository topology decisions, component ownership, and a no-code-movement directory skeleton. Runtime behavior, archives, installation semantics, target evidence, release assets, and upstream integration remain unchanged.

The final Epoch 1 retained acquisition authority is:

```text
3.14.5  9761545   2edec6cfaf20a44b2458567856c1d505e6942d0e43da0e8ba2a36761ebc05be2
3.14.6  11788907  f0c449f7bc5b5bd740f4776f43bec4418645d5f33da220fa523409b6aa0af208
snapshot body    dbdc0edd20eeca1506066c6ec95078d9ad4fe231b81a13aa1236b480d3faa233
```

Gate 4 actual-byte evidence `6cba95839a5dc05a7d4261467f1b7693e9d232fd44abe21ca4712e09b8e1977b` passes 16/16 target and 31/31 independent checks, with 714/714 strict payload fidelity for each product. Gate 4 repository recording result `daaf64255fce6d9c1ef2f5eb5e57d8dcc85472a4be48e56c47f21b94dee891f8` passes project control 91/91.

The first Gate 5 commit passed marker-based verification but accidentally installed fixture-shortened documentation. Independent post-push diff audit rejected that state. The correction restores the complete production documents and adds preservation sentinels. The historical Gate 2 concrete snapshot remains preserved but unselectable.

No Epoch 1 gate is active. Epoch 2 work must open and close its own bounded phases without treating design documents as runtime or target acceptance.

## Current reading path

```text
docs/CURRENT_CONTEXT.md
docs/epochs/EPOCH2_CHARTER.md
docs/roadmap/EPOCH2_ROADMAP.md
docs/architecture/COMPONENT_OWNERSHIP.md
docs/decisions/
docs/references/
docs/epochs/EPOCH1_CLOSURE.md
docs/PROJECT_CONTEXT_STAGE3F.md
docs/session-operations/README.md
```
