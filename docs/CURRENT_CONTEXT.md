# Current Project Context

> **Current epoch:** Epoch 2
> **Current phase:** E2-P2 Termux-native CPython 3.14.6 producer authority frozen
> **Next phase:** explicit façade producer-binding transition on `main`
> **Frozen predecessor:** Epoch 1 through Stage 3-F
> **Epoch 1 predecessor commit:** `e1de252740a96c40f3d587269136235a2c84ea16`
> **Epoch 2 Phase 0 commit:** `a34e5fdc6224e66aa7ed335e921780fbadd728dc`
> **Epoch 2 Phase 1 commit:** `68828691fcae382cf49b9dbc2b5231f9e21f9282`
> **Primary target:** Android/Bionic arm64, `aarch64-linux-android`, API 24+
> **Primary execution profile:** `termux-cli`

## Frozen E2-P1 artifact contract

```text
contract version       1
primary flavor         install_only_stripped
archive format         pax-tar+zstd
archive/install root   python/
payload classes        runtime + development
excluded classes       tests + build + debug_symbols
target triple          aarch64-linux-android
Android ABI            arm64-v8a
minimum API            24
wheel platform         android_24_arm64_v8a
primary profile        termux-cli
```

## Frozen E2-P2 Gate 1 façade

```text
stable command
  components/standalone/bin/cpython-android-standalone

operations
  plan
  build
  package
  verify --scope repository
  verify --scope envelope
```

Gate 1 remains frozen at repository and synthetic-envelope authority. Its producer binding has not yet been changed.

## Frozen Termux-native CPython 3.14.6 producer authority

```text
Python              3.14.6
source commit       c63aec69bd59c55314c06c23f4c22c03de76fe45
target              aarch64-linux-android
canonical host      aarch64-unknown-linux-android
Android API         24
NDK                 27.3.13750724
SOABI               cpython-314-aarch64-linux-android
package SHA-256     517f4b0d113c4c1cf6931c230b6b517bee7a2b7f8b4f0f099a148260fa3ac8e7
prefix snapshot     3081a1b150473ff6d6896589a2898cb38baf831e0f811af2bd0447c29b36bb89
```

Frozen three-artifact set:

```text
runtime-base        7119e97cb43fb19ef4dce3eec145bb867b8070b9f8b7772c74a5885f4fe53c03
development-addon   73dc90a8ead6c58d040a2fc31386f1c00ff38ce84fd4507229e8e9bc18902b6f
test-addon          5bb4c1a45a2c04031c8c8c1a0be05fc02ad4653f21492b63559039105be5ce03
```

Accepted evidence:

```text
clean replay core                 33/34 plus canonical-host adjudication
canonical identity adjudication   24/24 + 10/10
materialization core              25/25
materialization adjudication      23/23 + 12/12
standalone candidate              10/10
standalone verifier               41/41
standalone invariant closure      21/21
façade invariant closure          24/24 before and after
custom-NDK invariant closure      49/49 before and after
external freeze audit             23/23
```

## Current claim boundary

```text
producer authority       frozen
three-artifact authority frozen
standalone Termux        accepted
façade producer binding  unchanged
real E2-P1 envelope      not produced through façade
E2-P3 qualification      not started
selectability            false
publication              not permitted
transition behavior      not reopened
```

## Immediate reading path

1. [`contracts/E2P2_TERMUX_NATIVE_CPYTHON3146_PRODUCER_AUTHORITY.md`](contracts/E2P2_TERMUX_NATIVE_CPYTHON3146_PRODUCER_AUTHORITY.md)
2. [`evidence/E2P2_TERMUX_NATIVE_CPYTHON3146_PRODUCER_AUTHORITY_FREEZE.md`](evidence/E2P2_TERMUX_NATIVE_CPYTHON3146_PRODUCER_AUTHORITY_FREEZE.md)
3. [`../experiments/epoch2-termux-native-cpython3146-producer/producer-authority.json`](../experiments/epoch2-termux-native-cpython3146-producer/producer-authority.json)
4. [`contracts/E2P2_STANDALONE_FACADE_CONTRACT.md`](contracts/E2P2_STANDALONE_FACADE_CONTRACT.md)
5. [`evidence/E2P2_GATE1_STANDALONE_FACADE_RESULT.md`](evidence/E2P2_GATE1_STANDALONE_FACADE_RESULT.md)
6. [`roadmap/EPOCH2_ROADMAP.md`](roadmap/EPOCH2_ROADMAP.md)
7. [`epochs/EPOCH2_CHARTER.md`](epochs/EPOCH2_CHARTER.md)

## Next bounded gate

Perform one explicit producer-binding transaction on `main`. It must replace the façade's frozen Stage 3-B producer input only after verifying this authority, preserve Gate 1 command semantics, and remain separate from real E2-P1 envelope production.
