# Handoff: E2-P2 Termux-native CPython 3.14.6 producer

Stop boundary: the producer authority is opened for preflight only.

Base repository coordinate:

- branch `agent/epoch2-p2-standalone-build-facade`
- head `c70d5a8e3f07e3c6892459a5390ab284521b3868`
- tree `5010c35ec3de20336d39f7344a1dd92dde7231f9`

Required local authority root:

`$HOME/.cache/hw-t-authorities/cpython-android-cli/stage3b-producer-reacquired-v1`

Do not run E2-P2 Gate 2 yet. Review the opening preflight first. If it is ready,
the next bounded operation is the clean Termux-native CPython 3.14.6 replay.

## Corrected preflight boundary

The original 24/25 result was a verifier-model false blocker for `setpwent`.
After the correction transaction, require 25/25, zero blockers, and
`NEXT_ACTION_CLASS=run-termux-native-cpython3146-clean-replay` before starting
the clean replay. The façade producer binding remains unchanged.
