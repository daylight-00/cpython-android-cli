# ADR-0001: Begin a New Architecture Epoch

- **Status:** Accepted
- **Date:** 2026-07-16

## Context

Epoch 1 is complete through Stage 3-F. The new direction changes the central product from a Termux installation-oriented adaptation to an Android/Bionic standalone runtime with a separate installer consumer.

Continuing with another ordinary Stage 3 gate would hide the identity change. Rewriting existing stage documents would damage frozen evidence.

## Decision

Start **Epoch 2** with its own phase sequence. Preserve every existing Stage 1–3-F document and authority as the frozen Epoch 1 predecessor.

## Alternatives considered

1. Extend the existing stage sequence without an epoch boundary.
2. Rewrite the repository immediately around standalone terminology.
3. Create an unrelated standalone repository immediately.
4. Incubate the new architecture in the current repository, then promote it after the product boundary is stable.

Alternative 4 is accepted.

## Consequences

- Existing stage and evidence paths remain stable.
- Epoch 2 can change product decomposition without rewriting prior claims.
- Documentation must clearly distinguish predecessor evidence from active design.
- No runtime or target claim follows from opening the epoch.
