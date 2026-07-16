# ADR-0004: Make the Standalone Archive the Product Authority

- **Status:** Accepted
- **Date:** 2026-07-16

## Context

Epoch 1 proved archives, lifecycle, publication, and acquisition, but the installation system and produced runtime remain closely represented inside one project model. Epoch 2 needs a product that can be consumed by the installer, uv integration, direct users, and potentially other downstream systems.

## Decision

The canonical standalone release consists of immutable archive bytes plus versioned machine-readable metadata, checksums, licenses, provenance, and qualification results.

Planned archive classes are:

```text
install_only_stripped  primary runnable distribution artifact
install_only           unstripped installed tree when required
full                   producer/downstream reconstruction artifact when retained inputs permit
symbols                 matching external debug information where applicable
```

Initial implementation focuses on one runnable stripped artifact. Supporting every flavor is not a Phase 0 requirement.

## Consequences

- Release bytes, not an installer workspace, define product identity.
- The installer must not silently repack or mutate runtime identity.
- Build provenance and debug material can be distributed separately from the normal runtime.
- Archive and metadata schema changes require explicit versioning and compatibility policy.
