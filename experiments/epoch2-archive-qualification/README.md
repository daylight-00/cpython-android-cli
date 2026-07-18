# E2-P3 Archive-Only Qualification

This experiment owns the qualification contract verifier and self-contained regression tests.

Stable target command:

```text
components/standalone/bin/cpython-android-qualify
```

Gate 1 freezes design and harness behavior only. The frozen E2-P2 private envelope is the sole product input. The qualifier supports a host-independent `static` profile and separate `termux-real` and `termux-emulator` target profiles.

Individual results are deliberately unselectable. Combined qualification and metadata finalization are later bounded gates.

The first real-Termux execution reached 33/35. Harness correction v1 freezes lexical venv-symlink identity and created-venv pip wheel-tag discovery; product bytes and the 35-check target matrix are unchanged. The corrected retry passed 35/35, its result verifier passed 19/19, and independent review passed 38/38. That individual real-Termux authority is frozen and remains unselectable; the separate emulator profile is next.
