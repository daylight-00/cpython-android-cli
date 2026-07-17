# E2-P2 Termux-native CPython 3.14.6 authority opening

The historical Stage 3-B acceptance archive and exact CPython source commit were
reacquired successfully. The only remaining blockers for the original producer
were the unavailable historical Linux host and compiler-byte witness.

The selected resolution is to open a separate Termux-native CPython 3.14.6
producer authority instead of weakening or impersonating the original
Stage 3-B authority.

The retained Gate 4A CPython 3.14.5 work provides a proven Termux execution
pattern. Its final freeze remains separate and is referenced only as evidence
for the bounded shell, host-configure, lld-overlay, isolation, and device-test
methods.

This opening does not claim that a 3.14.6 build has run. The accompanying
preflight records whether the canonical device currently has the exact source,
dependency lock, SDK/NDK inputs, tools, storage, and reusable adaptation support
needed to start a clean replay.
