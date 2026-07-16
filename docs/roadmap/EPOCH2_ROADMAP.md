# Epoch 2 Roadmap

Each phase defines one bounded authority. A later phase may consume a frozen earlier phase but must not silently broaden its claims.

## E2-P0 — Documentation and component boundaries

**Goal:** define the epoch, terminology, repository topology, artifact authority, installer boundary, and ownership map.

**Deliverables:** charter, ADRs, references, roadmap, navigation, and component README skeleton.

**Acceptance:** exact documentation-only change set; no implementation, experiment, frozen stage, evidence, archive, or target mutation.

## E2-P1 — Canonical standalone artifact contract

**Goal:** define archive root, payload classes, metadata schema, checksums, licenses, provenance, target/API/profile fields, and compatibility rules.

**Acceptance:** machine-readable fixtures and independent schema verification. No producer refactor is required to close design.

## E2-P2 — Standalone build and package façade

**Goal:** provide stable `build`, `package`, and `verify` entry points over the existing proven producer and runtime assembly.

**Acceptance:** same frozen runtime behavior and closure; deterministic release-envelope output; internal implementation paths hidden behind the façade.

## E2-P3 — Metadata and qualification

**Goal:** qualify relocation, ELF closure, extension imports, HTTPS, venv, pip, uv explicit-interpreter workflows, wheel tags, and product fidelity from extracted artifacts.

**Acceptance:** archive-only qualification on emulator and real Termux evidence where the claim is target-specific.

## E2-P4 — Installer artifact-only conversion

**Goal:** make the installer an artifact-only consumer: installation, acquisition, cache, registry, recovery, uninstall, and version transition consume the release envelope only.

**Acceptance:** producer source and build trees are absent; complete lifecycle and cross-version tests still pass.

## E2-P5 — Automated prerelease

**Goal:** produce reproducible GitHub prerelease assets from an exact tag or release authority.

**Acceptance:** archives, metadata, checksums, licenses, static verification, emulator smoke, and asset upload are automated. Stable promotion remains explicit until real-device policy is accepted.

## E2-P6 — Standalone repository promotion

**Goal:** extract the standalone component into a focused product repository with relevant history preserved.

**Acceptance:** independent clone can build, package, verify, and prerelease; installer consumes published artifacts; no repository-relative dependency remains.

## E2-P7 — uv managed-Python integration

**Goal:** map the stable Android product into upstream or downstream uv download metadata and managed-Python workflows.

**Acceptance:** exact catalog identity, acquisition, discovery, launch, venv, package installation, reinstall, uninstall, and claim boundaries on supported Android/Termux targets.

## Phase rule

```text
design authority
  -> independent verifier
  -> implementation
  -> target evidence where required
  -> freeze
```
