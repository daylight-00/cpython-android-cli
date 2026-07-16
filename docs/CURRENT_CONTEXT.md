# Current Project Context

> **Current epoch:** Epoch 2
> **Current phase:** E2-P2 Gate 1 frozen — standalone build/package/verify façade
> **Next phase:** E2-P2 Gate 2 — workstation producer and package execution
> **Frozen predecessor:** Epoch 1 through Stage 3-F
> **Epoch 1 predecessor commit:** `e1de252740a96c40f3d587269136235a2c84ea16`
> **Epoch 2 Phase 0 commit:** `a34e5fdc6224e66aa7ed335e921780fbadd728dc`
> **Epoch 2 Phase 1 commit:** `68828691fcae382cf49b9dbc2b5231f9e21f9282`
> **Primary target:** Android/Bionic arm64, `aarch64-linux-android`, initially API 24+
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

`build` pins and delegates to the frozen Stage 3-B replay, product-promotion, and launcher entry points. `package` emits an E2-P1 envelope from the promoted prefix and canonical launcher, serializes it twice, and requires byte identity. `verify` separates repository façade authority from static release-envelope verification.

Gate 1 uses synthetic producer inputs. It proves fail-closed command routing, deterministic package implementation, exact sidecar linkage, excluded payload policy, and archive mutation rejection. It does not prove a real CPython build or Android execution.

## Current claim boundary

```text
real CPython build       not run through façade
real release envelope    not produced
Android execution        not run
Termux qualification     not run
selectability            false
publication              not permitted
installer conversion     not started
```

## Immediate reading path

1. [`contracts/E2P2_STANDALONE_FACADE_CONTRACT.md`](contracts/E2P2_STANDALONE_FACADE_CONTRACT.md)
2. [`evidence/E2P2_GATE1_STANDALONE_FACADE_RESULT.md`](evidence/E2P2_GATE1_STANDALONE_FACADE_RESULT.md)
3. [`../experiments/epoch2-standalone-build-facade/`](../experiments/epoch2-standalone-build-facade/)
4. [`contracts/E2P1_STANDALONE_ARTIFACT_CONTRACT.md`](contracts/E2P1_STANDALONE_ARTIFACT_CONTRACT.md)
5. [`roadmap/EPOCH2_ROADMAP.md`](roadmap/EPOCH2_ROADMAP.md)
6. [`architecture/COMPONENT_OWNERSHIP.md`](architecture/COMPONENT_OWNERSHIP.md)
7. [`epochs/EPOCH2_CHARTER.md`](epochs/EPOCH2_CHARTER.md)
8. [`epochs/EPOCH1_CLOSURE.md`](epochs/EPOCH1_CLOSURE.md)
9. [`PROJECT_CONTEXT_STAGE3F.md`](PROJECT_CONTEXT_STAGE3F.md) when exact predecessor authority is required

## Next bounded gate

E2-P2 Gate 2 runs the stable `build` and `package` operations on the configured Linux workstation. It must preserve the build receipt, logs, tool identities, complete release envelope, and independent static-verification result. The product remains `not-qualified` and unselectable until E2-P3 target qualification.
