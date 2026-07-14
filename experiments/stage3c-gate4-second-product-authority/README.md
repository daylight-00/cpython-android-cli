# Gate 4 Second-Product Authority

This directory contains the authority-acquisition work that must finish before any cross-version transition design.

## Current state

```text
A1 selection and design          DESIGN FROZEN
A2 input capture                 FROZEN PASS
  A2a remote inputs              FROZEN PASS — 81/81 external audit
  A2b Termux-native toolchain    FROZEN PASS — 46/46 combined audit
A3 upstream replay               FROZEN PASS
A4 three-artifact materialize    FROZEN PASS — static adjudication 26/26
A5 standalone Termux validate    READY — not started
A6 independent freeze            pending
```

Selected second product:

```text
CPython 3.14.5
v3.14.5
5607950ef232dad16d75c0cf53101d9649d89115
aarch64-linux-android / API 24 / NDK 27.3.13750724
```

Run the repository design verifier:

```sh
bash experiments/stage3c-gate4-second-product-authority/run-gate4a-second-product-authority-design.sh
```

A4 froze the exact runtime-base, development-addon, and test-addon materialization identities after an independent static adjudication isolated the archived `archive_payload_matches_manifests` failure as a verifier false negative. The next operation is A5 standalone Termux validation. A6 remains required before the second product itself is frozen, and all upgrade/downgrade or mixed-version work remains closed.

A4 authority record:

```text
docs/evidence/STAGE3C_PHASE5_GATE4A_A4_MATERIALIZATION_RESULT.md
experiments/stage3c-gate4-second-product-authority/gate4a-a4-materialization-authority.json
```

Audit an A2a result archive:

```sh
bash experiments/stage3c-gate4-second-product-authority/run-gate4a-a2a-remote-input-capture-audit.sh /path/to/result.tar.zst
```

Verify the A2b authority decision:

```sh
bash experiments/stage3c-gate4-second-product-authority/run-gate4a-a2b-termux-native-toolchain-authority.sh
```
