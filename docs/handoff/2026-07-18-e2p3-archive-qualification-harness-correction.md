# Handoff — E2-P3 Archive Qualification Harness Correction

## Frozen state

- E2-P3 contract version 1 and its 35-check real/emulator matrices are unchanged.
- The first real-Termux execution reached 33/35.
- `venv_relocation` and `wheel_tag_android24` were adjudicated as harness false negatives.
- Venv identity is now symlink-aware and lexical.
- Wheel tags are collected from pip's vendored packaging in the created venv.
- Product, envelope, producer, package, and private authority bytes are unchanged.

## Next bounded gate

Retry only the `termux-real` archive qualification against the exact frozen private envelope. Do not combine the retry with repository freeze, emulator execution, combined qualification, metadata finalization, selectability, publication, installer conversion, or transitions.
