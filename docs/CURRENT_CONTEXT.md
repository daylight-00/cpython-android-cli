# Current Project Context

> **Current epoch:** Epoch 2
> **Current phase:** E2-P1 frozen — canonical standalone artifact contract
> **Next phase:** E2-P2 — standalone build and package façade
> **Frozen predecessor:** Epoch 1 through Stage 3-F
> **Epoch 1 predecessor commit:** `e1de252740a96c40f3d587269136235a2c84ea16`
> **Epoch 2 Phase 0 commit:** `a34e5fdc6224e66aa7ed335e921780fbadd728dc`
> **Primary target:** Android/Bionic arm64, `aarch64-linux-android`, initially API 24+
> **Primary execution profile:** `termux-cli`

## Frozen E2-P1 contract

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

The release envelope consists of immutable archive bytes, artifact metadata, an exact payload manifest, provenance, qualification, license inventory, `SHA256SUMS`, and a release-index body digest.

Termux remains the primary qualification profile but is not part of binary identity. A uv catalog key is a consumer mapping, not canonical product identity.

## Accepted repository verification

```text
independent verifier   68/68 PASS
negative fixtures      15/15 PASS
```

The deterministic fixture is intentionally not CPython and remains unqualified and unselectable. No runtime, target, release, installer, or upstream-support claim is made by E2-P1.

## Immediate reading path

1. [`contracts/E2P1_STANDALONE_ARTIFACT_CONTRACT.md`](contracts/E2P1_STANDALONE_ARTIFACT_CONTRACT.md)
2. [`evidence/E2P1_STANDALONE_ARTIFACT_CONTRACT_RESULT.md`](evidence/E2P1_STANDALONE_ARTIFACT_CONTRACT_RESULT.md)
3. [`../experiments/epoch2-standalone-artifact-contract/`](../experiments/epoch2-standalone-artifact-contract/)
4. [`roadmap/EPOCH2_ROADMAP.md`](roadmap/EPOCH2_ROADMAP.md)
5. [`architecture/COMPONENT_OWNERSHIP.md`](architecture/COMPONENT_OWNERSHIP.md)
6. [`epochs/EPOCH2_CHARTER.md`](epochs/EPOCH2_CHARTER.md)
7. [`epochs/EPOCH1_CLOSURE.md`](epochs/EPOCH1_CLOSURE.md)
8. [`PROJECT_CONTEXT_STAGE3F.md`](PROJECT_CONTEXT_STAGE3F.md) when exact predecessor authority is required

## Next bounded phase

E2-P2 introduces stable `build`, `package`, and `verify` façades over the existing proven producer and runtime assembly. The façades must emit an E2-P1-conforming release envelope without changing frozen runtime behavior, moving installer code, or treating the contract fixture as a product.
