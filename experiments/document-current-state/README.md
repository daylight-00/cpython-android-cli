# Document current-state authority — Phase 2

> **Status:** frozen design and verification authority
> **Predecessor tree:** `3a85792eec9c8e78e4955aa1a227e737d9c4c509`

This experiment establishes `docs/current/STATE.json` as the sole temporal source and makes four current-facing paths deterministic renderings.

## In scope

- versioned state schema;
- one live current source;
- registry v2 with exact tracked Markdown/JSON coverage;
- generated README capsule, current context, top-level index, and onboarding reading block;
- legacy orientation reclassified as a byte-preserved historical snapshot;
- exact grandfathering of 24 legacy live-document bindings;
- immutable baseline state snapshot for historical authority.

## Out of scope

- directory-level exhaustive generated indexes;
- physical path moves;
- mass editing of historical documents;
- legacy verifier decoupling beyond the exact existing compatibility boundary;
- any product, experiment, selectability, publication, or Epoch 3 selection claim.

## Stable commands

```bash
python3 experiments/document-current-state/render-current-views.py --root . --check
python3 experiments/document-current-state/verify-current-state.py --root .
python3 experiments/document-current-state/test-current-state.py
python3 experiments/document-current-state/verify-document-current-state-authority.py --root .
```

## Historical verification decoupling

Phase 2 does not replay the recursive historical E2-P3 verifier chain in a temporary clone. That chain is environment-sensitive because old adjudication layers inspect Git execution context.

Instead, the exact Phase 1 predecessor commit/tree is required, the ten immutable E2-P3 freeze paths are byte-compared with that predecessor, and the bounded current secondary-freeze verifier must pass `28/28`. This preserves frozen authority bytes without making current navigation depend on historical nested replay behavior.

## Fixture materialization

Negative fixtures are materialized once from the staged Git index. One index-only fixture repository is restored before each of the ten cases; it uses `git init` plus `git add` only and creates no commit or background maintenance. Temporary-directory cleanup is best-effort hygiene and cannot change a completed fixture verdict. Ignored `work/` and `results/` trees remain outside the fixture.
