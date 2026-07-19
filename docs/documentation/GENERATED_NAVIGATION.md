# Generated navigation and complete-document reachability contract

> **Status:** stable governance, version 1
> **Lifecycle phase:** Phase 3 generated navigation established
> **Predecessors:** [`DOCUMENT_LIFECYCLE.md`](DOCUMENT_LIFECYCLE.md), [`CURRENT_STATE_AUTHORITY.md`](CURRENT_STATE_AUTHORITY.md)

This contract establishes deterministic, registry-derived navigation without moving or rewriting frozen historical documents.

## 1. Canonical navigation root

[`../navigation/README.md`](../navigation/README.md) is the generated root for documentation discovery. It separates current coordinates, stable governance, active plans, frozen authority, historical snapshots, experiments, and references.

## 2. Directory entrypoints

The following natural directory entrypoints are generated from the registry:

- `docs/current/README.md`
- `docs/documentation/README.md`
- `docs/decisions/README.md`
- `docs/epochs/README.md`
- `docs/architecture/README.md`
- `docs/roadmap/README.md`
- `docs/contracts/README.md`
- `docs/evidence/README.md`
- `docs/stages/README.md`
- `docs/handoff/README.md`
- `docs/references/README.md`
- `experiments/README.md`

Every tracked Markdown or JSON document is either one of these generated entrypoints or has one canonical generated index assignment.

## 3. Historical preservation

Replacing the stale `docs/handoff/README.md` entrypoint does not discard its Stage 3-F content. Its exact predecessor bytes are retained at `docs/handoff/2026-07-16-stage3f-successor-session-reading-path-snapshot.md` and classified as `HISTORICAL_SNAPSHOT`.

Generated indexes may describe lifecycle and supersession metadata, but they do not reinterpret evidence or create claims.

## 4. Update rule

A document inventory or lifecycle change must update the live registry and state, then rerender all current and navigation targets in the same transaction. Hand editing generated indexes is forbidden.

## 5. Machine-binding boundary

Generated views, the live registry, and the live state remain forbidden targets for new historical `file_identities`. A frozen authority may bind the renderer, verifier, schemas, and immutable navigation target manifest.

## 6. Recursive authority boundary

Phase 3 preserves the exact Phase 2 authority and its recorded Phase 1 and E2-P3 verification results. It does not rerun older live-tree navigation checks against the new generated navigation tree. Historical verification is recursive by frozen authority identity, not by forcing every old verifier to accept every later current view.

## 6. Remaining migration boundary

Phase 3 does not normalize mixed legacy documents or remove snapshot-relative words such as `active`, `next`, and `pending`. That is Phase 4 work. No product, experiment, selection, publication, or Epoch 3 claim changes are introduced here.
