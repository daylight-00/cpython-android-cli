# Document lifecycle control-plane authority freeze

> **Status:** frozen Phase 1 pass
> **Authority SHA-256:** `d8e71c1c9ba387a17323fafc7c16a0c3fe5002cdac5045c76aa6e86282bc08cf`
> **External audit SHA-256:** `f678d50518b015220611eb438b591629105d5f749d83ea1f21a8a2a8cd9c6d0c`

The repository now has a machine-verifiable lifecycle registry covering every tracked Markdown and JSON path. The control plane introduces no document move, no historical-byte rewrite, no current-state single writer, and no product or experiment claim change.

## Frozen result

```text
predecessor HEAD       e4e684ae8488df6e7b991d34c1da222c1ce3b900
predecessor tree       2df6889f498df57eceadaf57d24771c8b26e56c3
tracked Markdown/JSON  415
legacy documents       405
new control documents  10
lifecycle classes      12
registry verifier      24/24
negative fixtures      8/8
legacy live bindings   24 exact grandfathered bindings
new live binding       forbidden
live registry binding  forbidden; immutable Phase 1 snapshot bound instead
```

## Boundary

Phase 1 preserves current document paths and content semantics. `README.md`, `CURRENT_CONTEXT.md`, `INDEX.md`, and the roadmaps are not converted or regenerated. Historical and frozen files are not mass-edited. The active product gate remains E2-R1 / UT-0, while the next documentation migration action is Phase 2: introduce a single current-state authority and render live views from it.
