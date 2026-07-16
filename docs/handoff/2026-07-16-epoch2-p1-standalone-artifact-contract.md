# Epoch 2 Phase 1 Standalone Artifact Contract Handoff — 2026-07-16

## Frozen boundary

E2-P1 freezes contract version 1 for one primary runnable artifact:

```text
cpython-<version>-aarch64-linux-android<api>-install_only_stripped
```

The release envelope consists of immutable archive bytes, five versioned sidecars, `SHA256SUMS`, and a release index body digest. The primary archive has a single `python/` root and combines runtime and development payloads while excluding tests, producer build state, and detached debug symbols.

## Authority

```text
contract document   docs/contracts/E2P1_STANDALONE_ARTIFACT_CONTRACT.md
machine authority   experiments/epoch2-standalone-artifact-contract/e2p1-authority.json
verifier            experiments/epoch2-standalone-artifact-contract/verify-e2p1-standalone-artifact-contract.py
negative tests       experiments/epoch2-standalone-artifact-contract/test-verify-e2p1-standalone-artifact-contract.py
result               docs/evidence/E2P1_STANDALONE_ARTIFACT_CONTRACT_RESULT.md
```

## Non-reopening rules

- Do not rename the target to `arm64-termux`, `arm64-bionic`, or `bionic-linux`.
- Do not make Termux application-private absolute paths part of binary identity.
- Do not make a uv catalog alias canonical product identity.
- Do not allow selectable products without passed qualification and complete exact bytes.
- Do not let the installer repackage or infer producer workspace layout.
- Do not move implementation merely to match the component skeleton.

## Next bounded phase

E2-P2 introduces stable build, package, and verify façades over the existing proven producer and runtime assembly. It must emit an envelope conforming to E2-P1 without changing frozen runtime behavior or pretending the fixture is a product.
