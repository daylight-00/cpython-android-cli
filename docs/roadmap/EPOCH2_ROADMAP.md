# Epoch 2 Roadmap

Each phase defines one bounded authority. A later phase may consume a frozen earlier phase but must not silently broaden its claims.

## E2-P0 — Documentation and component boundaries

> **Status:** FROZEN

**Goal:** define the epoch, terminology, repository topology, artifact authority, installer boundary, and ownership map.

**Deliverables:** charter, ADRs, references, roadmap, navigation, and component README skeleton.

**Acceptance:** exact documentation-only change set; no implementation, experiment, frozen stage, evidence, archive, or target mutation.

## E2-P1 — Canonical standalone artifact contract

> **Status:** FROZEN — 68/68 independent checks and 15/15 negative fixtures

**Goal:** define archive root, payload classes, metadata schema, checksums, licenses, provenance, target/API/profile fields, compatibility rules, selectability, and installer input boundaries.

**Frozen result:** contract version 1 defines `install_only_stripped` with a single `python/` root, `pax-tar+zstd`, runtime plus development payloads, and separate metadata, manifest, provenance, qualification, license, checksum, and release-index authorities.

**Acceptance:** machine-readable JSON Schemas, deterministic safe archive fixture, exact sidecar linkage, independent semantic/archive verification, and mutation-based fail-closed tests. No producer refactor or target execution is required to close design.

## E2-P2 — Standalone build and package façade

> **Status:** ACTIVE — Gate 1 frozen; Gate 2 next

**Goal:** provide stable `build`, `package`, and `verify` entry points over the existing proven producer and runtime assembly.

**Gate 1 frozen result:** the repository command, pinned predecessor entry points, deterministic package implementation, general envelope verifier, synthetic double-build byte identity, drift rejection, and archive-mutation rejection are accepted. No real producer run is claimed.

**Gate 2 next:** execute `build` and `package` on the configured Linux workstation and independently verify the returned unqualified E2-P1 envelope.

**Phase acceptance:** same frozen runtime behavior and closure; deterministic real E2-P1 release-envelope output; internal implementation paths hidden behind the façade; the fixture is never promoted as a product.

## E2-P3 — Metadata and qualification

**Goal:** qualify relocation, ELF closure, extension imports, HTTPS, venv, pip, uv explicit-interpreter workflows, wheel tags, and product fidelity from extracted artifacts.

**Acceptance:** archive-only qualification on emulator and real Termux evidence where the claim is target-specific. Qualification metadata becomes selectable only after all required classes pass.

## E2-P4 — Installer artifact-only conversion

**Goal:** make the installer an artifact-only consumer: installation, acquisition, cache, registry, recovery, uninstall, and version transition consume the release envelope only.

**Acceptance:** producer source and build trees are absent; complete lifecycle and cross-version tests still pass; installer repacking remains forbidden.

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
