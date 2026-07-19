# cpython-android-cli

An evidence-driven research repository for adapting upstream Android/Bionic CPython into a practical standalone CLI runtime and studying its use under Termux and uv.

This repository is the laboratory, governance record, and historical evidence archive. It is not the final release repository, a CPython fork, a replacement for Termux Python, or a claim that every demonstrated capability belongs in the eventual product.

<!-- BEGIN GENERATED CURRENT STATE -->
## Current project coordinates

> Generated from [`docs/current/STATE.json`](docs/current/STATE.json). Do not hand-edit this block.

```text
immediate repository action  execute-e2-r1-ut0-exact-official-upstream-control
document migration           Phase 5 complete; migration closed
program epoch                E2 — upstream-thin research program
program gate held ready      E2-R1/UT-0 — exact official upstream control
program resume action        execute-e2-r1-ut0-exact-official-upstream-control
```

### Current claim boundary

```text
dual-device claim     accepted — AArch64 Termux compatibility
emulator qualified    false
selectable            false
publication           false
Epoch 3 selection     false
```

### Active blockers

none

### Unresolved risks

- official upstream package and BeeWare dependency identities are not yet frozen under UT-0

### Accepted authorities

- [`experiments/epoch2-recalibration/recalibration-authority.json`](experiments/epoch2-recalibration/recalibration-authority.json): program architecture and epoch boundary (`24578fea080cf700d2bbdd607b448fd48fd6f759250d4a9a49986f8cb4e37c01`)
- [`experiments/epoch2-upstream-thin-plan/plan-authority.json`](experiments/epoch2-upstream-thin-plan/plan-authority.json): active research plan and completion gates (`62b3b07f37a90b497747562bb00a9db5a3d78b3b2cb45df8f66db22818f5eafa`)
- [`experiments/epoch2-archive-qualification/secondary-real-device-qualification-authority.json`](experiments/epoch2-archive-qualification/secondary-real-device-qualification-authority.json): bounded dual-real-device compatibility evidence (`e380198cda8c49cad704483e3edc33c2d745cc65857155b3a7edb1887410f06c`)
- [`experiments/document-lifecycle-control/document-lifecycle-control-authority.json`](experiments/document-lifecycle-control/document-lifecycle-control-authority.json): documentation lifecycle registry control plane (`d8e71c1c9ba387a17323fafc7c16a0c3fe5002cdac5045c76aa6e86282bc08cf`)
- [`experiments/document-current-state/document-current-state-authority.json`](experiments/document-current-state/document-current-state-authority.json): single current-state authority and generated-view contract (`77345393b51d1f7807f77884990838598d2520c6dca3426107c580a1fcb041b6`)
- [`experiments/document-navigation/document-navigation-authority.json`](experiments/document-navigation/document-navigation-authority.json): complete generated documentation navigation and reachability (`28faa2ba26dbded39ecd581a849288d87f030a25b81a1639796f863db86b1f23`)
- [`experiments/document-mixed-correction/document-mixed-correction-authority.json`](experiments/document-mixed-correction/document-mixed-correction-authority.json): stable/current/plan/history layer separation and snapshot interpretation (`45df6e86f0164df8c1d81746af9ca5c44f7921e5a14fc17967213d65a4a43aaf`)
- [`experiments/document-legacy-authority-decoupling/legacy-authority-decoupling-authority.json`](experiments/document-legacy-authority-decoupling/legacy-authority-decoupling-authority.json): legacy authority compatibility snapshots and completed documentation lifecycle migration (`c24beeaf69bcdbbc1f73fabc7ec1195b6f0b5a416b33ad2bfa0c7f386c70f924`)

### Current entry points

- [`docs/PROJECT_GUIDE.md`](docs/PROJECT_GUIDE.md)
- [`docs/CURRENT_CONTEXT.md`](docs/CURRENT_CONTEXT.md)
- [`docs/INDEX.md`](docs/INDEX.md)
- [`docs/navigation/README.md`](docs/navigation/README.md)
- [`docs/SESSION_ONBOARDING.md`](docs/SESSION_ONBOARDING.md)
<!-- END GENERATED CURRENT STATE -->

## Stable entry points

- [`docs/PROJECT_GUIDE.md`](docs/PROJECT_GUIDE.md) — project identity, authority model, and reading rules
- [`docs/documentation/DOCUMENTATION_SYSTEM.md`](docs/documentation/DOCUMENTATION_SYSTEM.md) — lifecycle, update, supersession, and machine-binding rules
- [`docs/navigation/README.md`](docs/navigation/README.md) — exhaustive generated navigation
- [`docs/SESSION_ONBOARDING.md`](docs/SESSION_ONBOARDING.md) — successor-session procedure

## Authority model

```text
present coordinates   -> docs/current/STATE.json
program design        -> canonical active plan + ADRs + epoch charters
proven result         -> frozen contract + evidence + machine authority
past statement        -> historical snapshot at its recorded boundary
where to read         -> generated navigation
```

Current state and navigation are generated views. Historical documents may contain words such as `active`, `next`, or `pending`; those words remain relative to the document's original snapshot and never override `docs/current/STATE.json`.

## Engineering principle

```text
understand -> reproduce -> measure -> compare -> design -> optimize
```

Complete independently audited target evidence outranks design intent, local reconstruction, static inspection, and chat memory. Narrow evidence must not be expanded into a broader claim.
