# Raw external research archives — Epoch 2 to Epoch 4 recalibration

> **Captured:** 2026-07-19
> **Authority class:** immutable research input; adjudicated decisions live in repository ADRs and charters

This directory preserves the four archives supplied by the project owner after an external research session. The ZIP bytes are intentionally retained without normalization or extraction into the active documentation tree.

## Why raw bytes are retained

- preserve the exact external-session input;
- allow later independent review of conclusions and citations;
- separate source material from project-owned decisions;
- make superseded or rejected proposals auditable;
- avoid silently rewriting external research as repository authority.

## Intake result

Each ZIP has one safe top-level root, no absolute or traversal paths, no duplicate members, and no link or special-file members. `SHA256SUMS` identifies the exact retained bytes. `MANIFEST.json` records size, member count, root, and adjudicated role.

## Adjudication boundary

The archives contain facts, proposals, and unresolved alternatives. They do not independently override frozen repository evidence. Their accepted conclusions are recorded in:

- `docs/decisions/ADR-0006-UPSTREAM-DERIVED-EPOCH3-AND-SOURCE-PRODUCER-EPOCH4.md`;
- `docs/roadmap/EPOCH2_TO_EPOCH4_RECALIBRATED_ROADMAP.md`;
- the Epoch 2, Epoch 3, and Epoch 4 charters.
