# Gate 2 Read-Only Termux Consumer Census

> **Status:** TARGET EVIDENCE ACCEPTED

The accepted result archive is `4958b3e669950035f21baf5783fa54029366182cdc36ecf1fb909dfb8276e98c` (61374 bytes). It is a one-root, no-link archive with 849 members and an exact self-excluding 780-entry index.

```text
scenario rows             64/64 expectation match
strict controls           12/12 PASS
independent verifier      25/25 PASS
uv                         0.11.28 (aarch64-linux-android)
repository/global state   unchanged
```

Observed command coverage was narrower than the Gate 1 surface list:

```text
uv python find   72 process records
uv venv          14 process records
uv run            0
uv sync           0
```

Therefore Gate 2 accepts the discovery census, not a complete uv workflow contract. `uv run` and `uv sync` remain Gate 4 target obligations.

The first packaging attempt failed only because temporary uv virtual environments and copied prefixes contained normal symlinks, while project result archives prohibit links. Packaging recovery preserved 734 evidence files exactly, removed only transient workspaces, and did not rerun or re-adjudicate the census.
