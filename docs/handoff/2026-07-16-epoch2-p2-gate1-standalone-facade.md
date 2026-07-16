# Handoff: E2-P2 Gate 1 Standalone Façade

> **Status:** Gate 1 frozen; Gate 2 next

## Read first

```text
docs/CURRENT_CONTEXT.md
docs/contracts/E2P2_STANDALONE_FACADE_CONTRACT.md
docs/evidence/E2P2_GATE1_STANDALONE_FACADE_RESULT.md
experiments/epoch2-standalone-build-facade/E2P2_GATE1_STANDALONE_FACADE.md
components/standalone/contracts/facade-v1.json
```

## Frozen result

The stable command now exposes `plan`, `build`, `package`, and `verify`. Gate 1 uses synthetic inputs only and freezes no real product bytes.

## Transaction note

The initial application attempt made no commit and no push. It exposed an
over-broad checkout-global bytecode-residue check. The accepted verifier is
bounded to E2-P2-owned paths; do not reintroduce a repository-global cleanliness
claim for ignored interpreter caches.

## Gate 2 preflight correction

A read-only preflight found that the stable shell command did not export tracked defaults or ordinary `.local/env` assignments before execing the Python façade. The preflight performed no build and preserved result SHA-256 `3b11605e4711adde6d52f11c7b38454ee0110528175bc3c74c45664b5dc36361`. The corrected loader and regression must remain intact; do not work around the boundary by injecting target/version variables in an outer shell.

## Next bounded work

Rerun the Gate 2 producer census through the corrected public command. Separate façade-plan readiness from genuine producer inputs such as Stage 3-B provenance, source checkout, SDK/NDK, executable host toolchain, dependency cache, and free space. Only after that census passes may E2-P2 Gate 2 execute the stable build and package operations. Do not call the historical scripts directly unless diagnosing a façade failure. Preserve the generated build receipt, complete release envelope, logs, repository identity, and tool versions.

The Gate 2 envelope must remain:

```text
qualification status  not-qualified
product selectable    false
release selectable    false
publication allowed   false
```

No Android/Termux or installer claim is made until later bounded phases.
