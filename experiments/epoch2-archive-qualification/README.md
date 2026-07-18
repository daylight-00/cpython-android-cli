# E2-P3 Archive-Only Qualification

This experiment owns the qualification contract verifier and self-contained regression tests.

Stable target command:

```text
components/standalone/bin/cpython-android-qualify
```

Gate 1 freezes design and harness behavior only. The frozen E2-P2 private envelope is the sole product input. The qualifier supports a host-independent `static` profile and separate `termux-real` and `termux-emulator` target profiles.

Individual results are deliberately unselectable. Combined qualification and metadata finalization are later bounded gates.
