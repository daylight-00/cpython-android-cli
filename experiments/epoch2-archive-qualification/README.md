# E2-P3 Archive-Only Qualification

This experiment owns the qualification contract verifier and self-contained regression tests.

Stable target command:

```text
components/standalone/bin/cpython-android-qualify
```

Gate 1 freezes design and harness behavior only. The frozen E2-P2 private envelope is the sole product input. The qualifier supports a host-independent `static` profile and separate `termux-real` and `termux-emulator` target profiles.

Individual results are deliberately unselectable. Combined qualification and metadata finalization are later bounded gates.

The first real-Termux execution reached 33/35. Harness correction v1 freezes lexical venv-symlink identity and created-venv pip wheel-tag discovery; product bytes and the 35-check target matrix are unchanged. The corrected retry passed 35/35, its result verifier passed 19/19, and independent review passed 38/38. That primary real-Termux authority is frozen and remains unselectable. Native ARM64 emulator execution is infeasible on the available x86_64 workstation, so an explicit amendment waives the emulator objective and substitutes a second physical-device run on the Exynos 9810 Galaxy Note9 at Android API 29. The qualifier still executes the unchanged `termux-real` 35-check matrix; the target wrapper owns the exact secondary-device identity and authority label.


## Secondary real-device freeze

The Note9/API 29/Exynos 9810 execution passed 35/35 qualification, 19/19 result verification, and 41/41 independent review. Target authority index `6f869abe00b6e5fd50d85965dea84a12f7b6ce4c90ef20182f24831ed4b03d5d` was promoted and read back. Together with the primary S22 Ultra result, this freezes bounded dual-real-device AArch64 Termux compatibility for the same product bytes. Emulator qualification, original combined acceptance, selectability, publication, installer conversion, metadata finalization, and transitions remain unclaimed.
