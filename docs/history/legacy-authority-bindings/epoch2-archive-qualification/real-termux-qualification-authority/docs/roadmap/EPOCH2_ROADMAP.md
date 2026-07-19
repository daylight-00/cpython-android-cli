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

> **Status:** FROZEN — Gate 1, producer authority/binding, real façade execution, deterministic envelope, and independent review accepted

**Goal:** provide stable `build`, `package`, and `verify` entry points over the existing proven producer and runtime assembly.

**Gate 1 frozen result:** the repository command, pinned predecessor entry points, deterministic package implementation, general envelope verifier, synthetic double-build byte identity, drift rejection, and archive-mutation rejection are accepted. No real producer run is claimed.

**Producer authority and binding result:** a new CPython 3.14.6 producer was executed directly in Termux under the exact custom-NDK r27d binary authority. Clean replay, canonical-host adjudication, three-artifact materialization, standalone validation, and invariant closure are frozen. The stable façade is now explicitly bound to that authority while the Stage 3-B Linux producer remains unchanged historical provenance.

**Real façade execution authority frozen:** canonical and replay package executions produced an exact 8-file unqualified E2-P1 envelope. Repository verification passed 20/20 before and after, both envelope verifiers passed 52/52, the independent review passed 27/27, and private authority readback was byte-identical.

**Next bounded gate:** consume the frozen envelope authority in E2-P3 archive-only target qualification. Do not rerun or relabel E2-P2 producer/package authority as qualification evidence.

**Phase acceptance:** same frozen runtime behavior and closure; deterministic real E2-P1 release-envelope output; internal implementation paths hidden behind the façade; the fixture is never promoted as a product.

## E2-P3 — Metadata and qualification

> **Status:** ACTIVE — real Termux profile frozen; emulator qualification next

**Goal:** qualify relocation, ELF closure, extension imports, HTTPS, venv, pip, uv explicit-interpreter workflows, wheel tags, and product fidelity from extracted artifacts.

**Gate 1 frozen result:** the exact private E2-P2 envelope input, stable qualification command, static/real/emulator profile matrices, independent result verifier, 19/19 regression behavior, and 9/9 static replay with 19/19 result verification are accepted. No Android target execution is claimed.

**Qualification harness correction frozen:** the first real-Termux execution reached 33/35. The two failures were adjudicated as venv-symlink containment and base-pip wheel-tag source defects in the harness. The corrected semantics pass 21/21 regression while preserving the exact 35-check matrix and all frozen product identities. No target profile is qualified by the correction.

**Real-Termux authority frozen:** the corrected retry passed 35/35, result verification passed 19/19, and independent review passed 38/38 on a real aarch64 Android API 36 Termux host. The result remains individually unselectable and claims no emulator or combined qualification.

**Next bounded gate:** run only the separate `termux-emulator` profile with the same frozen envelope and harness. Do not rerun the accepted real-device profile or begin metadata finalization.

**Acceptance:** archive-only qualification on emulator and real Termux evidence where the claim is target-specific. Qualification metadata becomes selectable only after all required classes pass and a separate metadata-finalization gate succeeds.

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
