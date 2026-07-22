# cpython-android-cli

An evidence-driven research repository for adapting upstream Android/Bionic CPython into a practical standalone CLI runtime and studying its use under Termux and uv.

This repository is the laboratory, governance record, and historical evidence archive. It is not the final release repository, a CPython fork, a replacement for Termux Python, or a claim that every demonstrated capability belongs in the eventual product.

<!-- BEGIN GENERATED CURRENT STATE -->
## Current project coordinates

> Generated from [`docs/current/STATE.json`](docs/current/STATE.json). Do not hand-edit this block.

```text
agent bootstrap       established — AGENT_BOOTSTRAP.md
session transport     full Git bundle -> one runner -> complete receipt
immediate action      resolve-epoch3-release-blocking-experiments
program epoch         E3 — clean upstream-derived Android standalone distribution
program gate          E3/RELEASE-BLOCKERS — Release-blocking evidence, data products, compatibility, runtime contexts, and operations
```

### Current claim boundary

```text
dual-device claim     accepted — AArch64 Termux compatibility
emulator qualified    false
selectable            false
publication           false
Epoch 3 selection     true
```

### Active blockers

- RB-1-component-and-license-closure
- RB-2-ca-and-timezone-data-products
- RB-3-astral-consumer-compatibility
- RB-4-release-security-update-and-revocation-operations
- RB-5-api24-runtime-qualification
- RB-6-real-16k-runtime-qualification
- RB-7-non-termux-android-runtime-qualification

### Unresolved risks

- component-to-license-mapping-incomplete
- CA-and-timezone-production-payload-selection-pending
- astral-consumer-and-uv-managed-compatibility-pending
- API24-runtime-qualification-pending
- runtime-16KiB-device-support-unqualified
- non-Termux-Android-context-unqualified
- support-security-data-update-and-revocation-operations-pending
- emulator-unqualified-and-not-required-for-current-release-blocker-gate
- other-Android-ABIs-explicitly-out-of-scope
- upstream-derived-full-is-not-Astral-producer-object-full
- source-producer-host-isolation-and-libffi-fix-deferred-to-epoch4
- selectability-not-authorized
- publication-not-authorized
- libmpdec-2.5.1-license-source-must-not-use-mpdecimal-4.0.0-spdx-entry
- authoritative-license-payloads-not-yet-integrated-into-release-family
- xz-5.4.6-product-matching-license-evidence-not-yet-bound
- sqlite-public-domain-notice-policy-not-frozen
- android-system-provider-notice-boundary-not-frozen
- hacl-license-header-and-notice-not-yet-frozen
- final-notice-set-not-owner-approved

### Accepted authorities

- [`experiments/epoch2-recalibration/recalibration-authority.json`](experiments/epoch2-recalibration/recalibration-authority.json): program architecture and epoch boundary (`24578fea080cf700d2bbdd607b448fd48fd6f759250d4a9a49986f8cb4e37c01`)
- [`experiments/epoch2-upstream-thin-plan/plan-authority.json`](experiments/epoch2-upstream-thin-plan/plan-authority.json): active research plan and completion gates (`62b3b07f37a90b497747562bb00a9db5a3d78b3b2cb45df8f66db22818f5eafa`)
- [`experiments/epoch2-archive-qualification/secondary-real-device-qualification-authority.json`](experiments/epoch2-archive-qualification/secondary-real-device-qualification-authority.json): bounded dual-real-device compatibility evidence (`e380198cda8c49cad704483e3edc33c2d745cc65857155b3a7edb1887410f06c`)
- [`experiments/document-lifecycle-control/document-lifecycle-control-authority.json`](experiments/document-lifecycle-control/document-lifecycle-control-authority.json): documentation lifecycle registry control plane (`d8e71c1c9ba387a17323fafc7c16a0c3fe5002cdac5045c76aa6e86282bc08cf`)
- [`experiments/document-current-state/document-current-state-authority.json`](experiments/document-current-state/document-current-state-authority.json): single current-state authority and generated-view contract (`77345393b51d1f7807f77884990838598d2520c6dca3426107c580a1fcb041b6`)
- [`experiments/document-navigation/document-navigation-authority.json`](experiments/document-navigation/document-navigation-authority.json): complete generated documentation navigation and reachability (`28faa2ba26dbded39ecd581a849288d87f030a25b81a1639796f863db86b1f23`)
- [`experiments/document-mixed-correction/document-mixed-correction-authority.json`](experiments/document-mixed-correction/document-mixed-correction-authority.json): stable/current/plan/history layer separation and snapshot interpretation (`45df6e86f0164df8c1d81746af9ca5c44f7921e5a14fc17967213d65a4a43aaf`)
- [`experiments/document-legacy-authority-decoupling/legacy-authority-decoupling-authority.json`](experiments/document-legacy-authority-decoupling/legacy-authority-decoupling-authority.json): legacy authority compatibility snapshots and completed documentation lifecycle migration (`c24beeaf69bcdbbc1f73fabc7ec1195b6f0b5a416b33ad2bfa0c7f386c70f924`)
- [`experiments/agent-bootstrap/agent-bootstrap-authority.json`](experiments/agent-bootstrap/agent-bootstrap-authority.json): immutable one-document agent onboarding, bundle-native session transport, and mandatory session-operation protocol (`86f80a2325003d47884c81f5a03c13ad5a5cacb5fa124937124c4c371b668f79`)
- [`experiments/agent-task-completion/agent-task-completion-authority.json`](experiments/agent-task-completion/agent-task-completion-authority.json): task PASS/FAIL/update routing, successor readiness, and state/module/plan identity enforcement (`c45411577e916f3b3fe95e98fd4de439d81ca4858deeb29b21df177e298a5539`)
- [`experiments/epoch2-upstream-thin-control/upstream-control-authority.json`](experiments/epoch2-upstream-thin-control/upstream-control-authority.json): exact official Python.org Android package, topology, dependency, and provenance control (`6cc0acee911239eb2e82267dbb2d2de0043260fe482d45e10d6aeebffebe540c`)
- [`experiments/epoch2-upstream-thin-artifact-prototype/artifact-prototype-authority.json`](experiments/epoch2-upstream-thin-artifact-prototype/artifact-prototype-authority.json): truthful Astral-style local artifact and metadata prototype for the official binary-derived package (`387f0b68be2069fa36227dc80982ffe1371e79b2a35076ef0b09380ec7c7c306`)
- [`experiments/epoch2-upstream-thin-loader-relocation/loader-relocation-authority.json`](experiments/epoch2-upstream-thin-loader-relocation/loader-relocation-authority.json): bounded Android/Bionic loader, launcher, getpath, native closure, and whole-prefix relocation evidence (`05a6a21d9803d01880c6a81e0a33785edfd2b0b27b1ca4b508bd23f42219a6d2`)
- [`experiments/epoch2-upstream-thin-sysconfig-sdk/sysconfig-sdk-authority.json`](experiments/epoch2-upstream-thin-sysconfig-sdk/sysconfig-sdk-authority.json): relocation-aware sysconfig, consumer metadata, on-device native-extension SDK, and Android wheel evidence (`6cff1984d4601a37e8b57762bb170a57e695cb64d516c1dab0023b7e809dc808`)
- [`experiments/epoch2-upstream-thin-android-data-policy/android-data-policy-authority.json`](experiments/epoch2-upstream-thin-android-data-policy/android-data-policy-authority.json): host-neutral CA, timezone, temporary, cache, bytecode, user-site, venv, read-only-install, and independent data-update policy (`be25e52aba1d6c9d0b2e25fec2bd1d8a0a0d9eb870436f00e81f347e90d012b7`)
- [`experiments/epoch2-upstream-thin-feature-qualification/feature-qualification-authority.json`](experiments/epoch2-upstream-thin-feature-qualification/feature-qualification-authority.json): explicit evidence-backed subprocess, venv, pip, uv, console-script, and multiprocessing support boundaries (`3b56a38898a3a2384cf9419fe3cd124faa8dbf367cdd5532724b3424092a62e5`)
- [`experiments/epoch2-upstream-thin-platform-portability/platform-portability-authority.json`](experiments/epoch2-upstream-thin-platform-portability/platform-portability-authority.json): bounded current-target platform evidence, static 16 KiB compatibility, and explicit withheld claims (`b21eddfee574343772d0875a7b6f26aa7b5dd494ccf0a5f1be9b8c09201276f4`)
- [`experiments/epoch2-upstream-thin-upstream-evolution/upstream-evolution-authority.json`](experiments/epoch2-upstream-thin-upstream-evolution/upstream-evolution-authority.json): official patch-update rehearsal, Python 3.15 preview delta, maintenance burden, and security ownership (`a45566c4ea0e9dbb1aed53e27d07398e81835f6221da2ce28f78471c2467ace5`)
- [`experiments/epoch2-upstream-thin-api36-controlled-comparison/api36-controlled-comparison-authority.json`](experiments/epoch2-upstream-thin-api36-controlled-comparison/api36-controlled-comparison-authority.json): API-24 official and API-36 source-equivalent three-class controlled comparison (`576f0f833164a2748a5c494780f429b4c22af5cb07d331248ac7572611b1339e`)
- [`experiments/epoch2-upstream-thin-closure/closure-authority.json`](experiments/epoch2-upstream-thin-closure/closure-authority.json): Epoch 2 closure, accepted upstream-derived seed, selection inputs, and Epoch 3 initialization boundary (`8f3ed1fffb15fcc4302653176086797cbe0d64a30fe51f79570f11a4639e9fdc`)
- [`experiments/epoch3-upstream-thin-initialization/initialization-authority.json`](experiments/epoch3-upstream-thin-initialization/initialization-authority.json): complete Epoch 3 selection register, clean repository boundary, product contract freeze, independent audit, and canonical full implementation start (`901cd0ecde47ce3fc15f256976d2075db714c2003a51e996b5c278a1d1e22f3b`)
- [`experiments/epoch3-upstream-thin-full/full-authority.json`](experiments/epoch3-upstream-thin-full/full-authority.json): canonical deterministic Astral-structured upstream-thin full archive, Android/Bionic qualification, projection invariant, and install-only start authority (`a29064602ad2fa612eba516cc09ab49334f7d8ec4aec04f3c9e2e0827afec9d0`)
- [`experiments/epoch3-upstream-thin-install-only/install-only-authority.json`](experiments/epoch3-upstream-thin-install-only/install-only-authority.json): canonical exact full projection, Android/Bionic qualification, and stripped start authority (`7f27a85ce283e0283bb7e7cf0e4aace8282d7cfd0d37c732b23188c8b318018d`)
- [`experiments/epoch3-upstream-thin-stripped/stripped-authority.json`](experiments/epoch3-upstream-thin-stripped/stripped-authority.json): canonical bounded install-only-stripped derivation, Android/Bionic qualification, and artifact-family start authority (`bf985a2cfc5446f7deab36d853f27ac439c30ba2b85b761546d919fe411a2d25`)
- [`experiments/epoch3-upstream-thin-artifact-family/artifact-family-authority.json`](experiments/epoch3-upstream-thin-artifact-family/artifact-family-authority.json): canonical deterministic three-artifact release family, exact artifact identities, sidecars, checksums, release index, reproducibility, and release-blocker start authority (`102ea6c02198885a08328d821511a10b8043510095970dfde17d8c8ef18e276e`)
- [`experiments/epoch3-upstream-thin-release-blockers/rb1-baseline-authority.json`](experiments/epoch3-upstream-thin-release-blockers/rb1-baseline-authority.json): frozen exact component/license baseline, explicit 12-gap register, and source-provenance resolution start authority (`12c97e50fb1333c9f6094649dd8d19170df6f04c7c9168f88041cc321a982a0e`)
- [`experiments/epoch3-upstream-thin-release-blockers/rb1-source-provenance-authority.json`](experiments/epoch3-upstream-thin-release-blockers/rb1-source-provenance-authority.json): frozen exact six-dependency source provenance, libffi resolution, CPython source identity, mismatch quarantine, and license-payload acquisition start authority (`e538a19afb768b923cde46b9a7f5fe563b02988195b9fbb4d81106d5333ee467`)
- [`experiments/epoch3-upstream-thin-release-blockers/rb1-license-payload-authority.json`](experiments/epoch3-upstream-thin-release-blockers/rb1-license-payload-authority.json): frozen exact five-source license payload acquisition, 13-component expansion, eight-gap boundary, and legal-overlay evidence synthesis start authority (`20e74380a24b2868320290286841f97c7e847c133ecb6b29db430513ad99abba`)

### Agent entry

- [`AGENT_BOOTSTRAP.md`](AGENT_BOOTSTRAP.md)
- [`docs/current/AGENT_TASK.json`](docs/current/AGENT_TASK.json)
- [`docs/agent/PROJECT_MODEL.md`](docs/agent/PROJECT_MODEL.md)
- [`docs/agent/SESSION_PROTOCOL.md`](docs/agent/SESSION_PROTOCOL.md)
<!-- END GENERATED CURRENT STATE -->

## Agent session entry

A new agent session starts from the full Git bundle at [`AGENT_BOOTSTRAP.md`](AGENT_BOOTSTRAP.md). The owner does not need to provide a separate handoff package or a large prompt.

## Stable human entry points

- [`docs/agent/PROJECT_MODEL.md`](docs/agent/PROJECT_MODEL.md) — project philosophy, epoch roles, authority, and reading discipline
- [`docs/agent/SESSION_PROTOCOL.md`](docs/agent/SESSION_PROTOCOL.md) — mandatory bundle, Drive, Git, runner, evidence, and session rules
- [`docs/current/STATE.json`](docs/current/STATE.json) — sole current-state authority
- [`docs/current/AGENT_TASK.json`](docs/current/AGENT_TASK.json) — generated current task and section-level read manifest
- [`docs/navigation/README.md`](docs/navigation/README.md) — exhaustive lookup, excluded from ordinary onboarding

## Authority model

```text
present coordinates   -> docs/current/STATE.json
agent task routing    -> docs/current/AGENT_TASK.json
program design        -> canonical active plan + ADRs + epoch charters
proven result         -> frozen contract + evidence + machine authority
past statement        -> historical snapshot at its recorded boundary
where to read         -> generated navigation
```

## Engineering principle

```text
understand -> reproduce -> measure -> compare -> design -> optimize
```

Complete independently audited target evidence outranks design intent, local reconstruction, static inspection, and chat memory. Narrow evidence must not be expanded into a broader claim.
