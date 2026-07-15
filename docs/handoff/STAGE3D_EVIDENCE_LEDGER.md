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
```

Gate 3 freezes only the exact system-Python contract for `uv python find` and `uv venv`. Gate 4 must supply target evidence for `uv run` and `uv sync`.
