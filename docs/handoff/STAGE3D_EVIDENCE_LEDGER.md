# Stage 3-D Evidence Ledger

```text
Gate 1 commit/tree
  b0b938b6f8d4eea67e2fac1eca83f69c835a9cac
  3b86355f3236a850512e8e1bdb6b3e1df73362f5

Gate 2 recovered archive
  4958b3e669950035f21baf5783fa54029366182cdc36ecf1fb909dfb8276e98c
  61374 bytes
  849 safe members
  780/780 exact index

Gate 2 outputs
  census summary       c36998ad55a9a835afbc5ce10e3cf00a2671cb9586281496ab7853a24cc2fede
  scenario results     d7f9f41bf4370a19c021bfdf23258c124c4d2cf573981c6efdc401b74b602162
  independent verifier e5169e6a4483ae48fb227accb47fe17ba78c3bf6ce9fbd3045b23013ae2a1835

Gate 2 acceptance
  64/64 expectation match
  12/12 strict controls
  25/25 independent checks
  uv 0.11.28 aarch64-linux-android

Gate 3 freeze commit/tree
  64a2066d464e437407bc84c85d21e3f04495d02a
  2063517d5786ba179f71faa121e54c3e9b035239

Gate 3 contract
  c24f8af1d0af8cf2212a1e40ea0887cc7856fbd725e71759e9969ad8e07acb9e

Gate 4 accepted archive
  13ed73fdeaf5ea13339b2df70b69a4c79aa2920fb1d9207229fb64db828b283c
  58525 bytes
  757 safe members
  697/697 exact index

Gate 4 accepted outputs
  validation summary       b1a7864d2144df44ee6cf65e33243592420c659d0069d198f87bc3727566c4a7
  scenario results         d6cd2fe5e751476a2935962f8c0ec88bbb6beb41bf56449e23526d0dd2544def
  independent verification c9361f9c148c3d1a170b940a756b6f6b71d15ca957bb4d37e3ac3ea38664ebe5
  result tree safety       450e8b9c6198885509f0b520a002a3226ce0728f457c0565d792a09b02de969a

Gate 4 acceptance
  48/48 expectation match
  48/48 harness complete
  uv run 8/8 exact product
  uv sync 8/8 exact product
  transition continuity 4/4 exact
  27/27 independent checks
  uv 0.11.28 aarch64-linux-android

Gate 4 correction lineage
  v1 d7ba3e42af9ecefd89475f39c3e7d87e7d5265b0edbd59e42317526d84bdfc4d  45740 bytes  invalid
  v2 5f99ad5f61a6b57768e9631b8955cad8bd4d1bd68697f66ff787cba5f9e31072  58910 bytes  invalid
  v3 13ed73fdeaf5ea13339b2df70b69a4c79aa2920fb1d9207229fb64db828b283c  58525 bytes  accepted
```

Gate 5 freezes the exact system-Python consumer surface for both frozen products and all four topologies. Gate 6 managed-Python feasibility remains deferred and requires a separate authority decision.
