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

## Opening-preflight correction

The opening transaction committed successfully at `5e8cd1bd1889817d8cdcd0dc4c96574515b6618a`.
Its read-only preflight passed 24 of 25 checks. The sole failure was an
over-strict assertion that every legacy cache entry required both a generated
`configure` variable and `HAVE_*` template mapping.

The retained CPython 3.14.5 A3 result
`bfd241f959cb081a91f4866cb07cf2773d1028919de0ea0959ed0d95c8984202`
shows the actual accepted behavior: `setpwent` is passed as
`ac_cv_func_setpwent=no`, appears as `no` in the build-Python config log, has
no generated `HAVE_SETPWENT` macro, and the complete replay succeeds. The
corrected preflight recognizes this sole inert-cache exception while keeping
exact source mappings mandatory for all other and dynamically added entries.
