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
A5 standalone Termux validate    FROZEN PASS — independent audit 34/34
A6 independent freeze            FROZEN PASS — external audit 28/28
```

Selected and frozen second product:

```text
CPython 3.14.5
v3.14.5
5607950ef232dad16d75c0cf53101d9649d89115
aarch64-linux-android / API 24 / NDK 27.3.13750724
```

Gate 4A is complete. The exact runtime-base, development-addon, and test-addon artifacts, standalone Termux behavior, product lock, manifests, ownership registry, recovery semantics, and byte identities are frozen. Transition-policy design may begin, but no upgrade, downgrade, mixed-version, migration, collision, or transition-recovery behavior is accepted yet.

Authority records:

```text
docs/evidence/STAGE3C_PHASE5_GATE4A_A4_MATERIALIZATION_RESULT.md
docs/evidence/STAGE3C_PHASE5_GATE4A_A5_STANDALONE_VALIDATION_RESULT.md
docs/evidence/STAGE3C_PHASE5_GATE4A_A6_SECOND_PRODUCT_FREEZE.md
experiments/stage3c-gate4-second-product-authority/gate4a-a4-materialization-authority.json
experiments/stage3c-gate4-second-product-authority/gate4a-a5-standalone-authority.json
experiments/stage3c-gate4-second-product-authority/gate4a-a6-external-audit.json
experiments/stage3c-gate4-second-product-authority/gate4a-a6-second-product-authority.json
```

Run the repository design verifier:

```sh
bash experiments/stage3c-gate4-second-product-authority/run-gate4a-second-product-authority-design.sh
```

Audit an A2a result archive:

```sh
bash experiments/stage3c-gate4-second-product-authority/run-gate4a-a2a-remote-input-capture-audit.sh /path/to/result.tar.zst
```

Verify the A2b authority decision:

```sh
bash experiments/stage3c-gate4-second-product-authority/run-gate4a-a2b-termux-native-toolchain-authority.sh
```
