# Stage 3-D Gate 2 Read-Only Consumer Census Result

> **Status:** TARGET EVIDENCE ACCEPTED

```text
archive sha256            4958b3e669950035f21baf5783fa54029366182cdc36ecf1fb909dfb8276e98c
archive size              61374
safe members              849
self-index                780/780 exact
scenario results          64/64 expectation match
strict controls           12/12 PASS
independent verification  25/25 PASS
uv                         0.11.28 (aarch64-linux-android)
```

Both products and all four topologies were selected by the explicit absolute-path control. Natural and project requests selected the expected isolated candidate, and transition continuity selected the current exact product before and after both directions. Download-disabled negative requests failed as expected.

The archive also proves a coverage boundary: only `uv python find` and `uv venv` were executed. It does not accept `uv run`, `uv sync`, global interpreter links, unrestricted PATH behavior, or managed-Python integration.
