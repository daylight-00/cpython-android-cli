# Stage 3-F Independent Freeze Handoff — 2026-07-16

## Frozen repository input

```text
branch  agent/stage3f-publication-acquisition
HEAD    1e7797218473463bc85f6413c49080301eda2ad7
tree    a3a1cb90f12b20ab47203b4f6b47d8a9694b0e04
main    b5a2ca39d1250122312355dd3dbc6165b9409786
```

Gate 5 freezes Stage 3-F. The retained acquisition snapshot is `dbdc0edd20eeca1506066c6ec95078d9ad4fe231b81a13aa1236b480d3faa233` and the accepted actual-byte target result is `6cba95839a5dc05a7d4261467f1b7693e9d232fd44abe21ca4712e09b8e1977b`. The repository recording result is `daaf64255fce6d9c1ef2f5eb5e57d8dcc85472a4be48e56c47f21b94dee891f8`.

The historical Gate 2 snapshot remains unselectable, the Gate 4 v1 retention failure remains preserved, and ordinary exact-key redefinition remains forbidden. No gate is active. Any public publication, trust, uv acquisition, execution, installation, lifecycle, concurrency, durability, or third-product work requires a new stage with a new authority design.

A later independent diff audit rejected the initial Gate 5 commit `71ded3869f38ed59118435f119a35591aee29f75` as the final documentation tree because fixture-derived replacements shortened six production documents. See `docs/handoff/2026-07-16-stage3f-gate5-documentation-integrity-correction.md`; the corrective fast-forward commit supersedes the documentation state without rewriting history.


## Correction v1 false-negative

The first documentation-correction wrapper result `69bfe223c5fb4f0dec42cf5b99ac35d346be9aaddb7438b82ce59e1d38af494a` made no repository mutation. Its only failed check treated pre-existing ignored bytecode anywhere in the working tree as newly created residue. Correction v2 captures the preflight bytecode inventory and rejects only new residue; standalone verification falls back to rejecting tracked bytecode.
