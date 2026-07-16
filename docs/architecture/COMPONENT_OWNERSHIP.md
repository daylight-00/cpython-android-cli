# Epoch 2 Component Ownership

> **Status:** Phase 0 logical map; implementation files do not move in this phase.

## Ownership classes

### Standalone-owned

- CPython source/version selection and Android patches.
- NDK, API level, dependency recipes, and producer provenance.
- Native launcher and prefix relocation behavior.
- Runtime and development payload assembly.
- Native closure, extension inventory, sysconfig, and wheel-tag qualification.
- Archive flavors, metadata, checksums, licenses, symbols, and release index.
- Artifact extraction and standalone-runtime verification.

### Installer-owned

- Release selection, acquisition, and verified cache consumption.
- Project-owned installation root and version layout.
- Ownership registry, journals, locks, transaction, recovery, and residual policy.
- Install, repair, uninstall, upgrade, and downgrade coordination.
- Termux shell exposure and coexistence policy.
- uv discovery integration around installed interpreters.

### Consumer qualification

- uv system-Python discovery and explicit-interpreter workflows.
- uv managed-Python catalog feasibility and downstream integration tests.
- pip, venv, package installation, and Python CLI package scenarios.

Qualification consumes products; it does not own producer or installer internals.

### Historical experiment and evidence

- Existing `experiments/`, `docs/stages/`, `docs/evidence/`, and dated handoffs.
- Failed, superseded, and corrective attempts that explain accepted decisions.

These records remain in their existing paths unless a later evidence-preserving migration is explicitly approved.

### Collaboration infrastructure

- `docs/session-operations/`, collaboration protocols, handoff tooling, and Drive package rules.

This infrastructure is external to product runtime claims.

## Current-to-future map

| Capability | Current location class | Future owner | Phase 0 action |
|---|---|---|---|
| launcher | `src/` and build scripts | standalone | document only |
| CPython/dependency producer | scripts and Stage 3-B experiments | standalone | document only |
| runtime assembly and closure | scripts/experiments | standalone | document only |
| archive and product metadata | Stage 3-C/E/F implementation | standalone | define E2-P1 boundary |
| publication envelope | Stage 3-F | standalone release | preserve predecessor authority |
| acquisition and cache | Stage 3-F | installer | consume release envelope |
| transaction and registry | Stage 3-C/E | installer | preserve frozen semantics |
| cross-version transition | Stage 3-C Gate 4 | installer | preserve frozen semantics |
| uv system-Python workflows | Stage 3-D | consumer qualification | reuse tests |
| managed-Python feasibility | Stage 3-D/E | consumer qualification and installer | refine after artifact contract |

## Migration rule

No implementation files move merely to match this document. Movement begins only after E2-P1 freezes the artifact boundary and a stable façade proves which paths belong to each component.

Avoid permanent `shared` ownership. When both components need one schema, one side owns the versioned contract and the other declares supported versions.
