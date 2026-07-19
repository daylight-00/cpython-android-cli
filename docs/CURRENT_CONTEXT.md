# Current Project Context

> **Generated view:** [`current/STATE.json`](current/STATE.json) is the sole temporal authority.
> **State revision:** 1
> **Do not hand-edit this file.** Run `render-current-views.py` after a state transition.

## Immediate repository work

```text
control work        documentation lifecycle migration
completed phase     2
next phase          3
next action         execute-document-lifecycle-phase3-generated-navigation
```

## Program position held ready

```text
current epoch       E2 — upstream-thin research program
program status      active-recalibrated
program gate        E2-R1/UT-0 — exact official upstream control
gate status         ready-held-during-document-migration
resume action       execute-e2-r1-ut0-exact-official-upstream-control
```

Documentation control work does not close, advance, or replace the research gate. After the lifecycle migration is complete, the program resumes at E2-R1 / UT-0.

## Current E2-P3 claim boundary

```text
S22 Ultra / API 36 / qcom     accepted and frozen
Galaxy Note9 / API 29 / Exynos 9810  accepted and frozen
dual-device claim     accepted — AArch64 Termux compatibility
Android Emulator      waived, unqualified, unclaimed
selectability         false
publication           not authorized
```

## Active plan

- [`roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md`](roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md)
- SHA-256: `81fc0baaa996952c3caab86ea4abc7168b04e4aea357bc98530a332ea3ceef0a`

## Accepted authorities

1. [`epoch2-epoch4-recalibration`](../experiments/epoch2-recalibration/recalibration-authority.json) — program architecture and epoch boundary
2. [`epoch2-remaining-work-and-epoch3-completion-gates`](../experiments/epoch2-upstream-thin-plan/plan-authority.json) — active research plan and completion gates
3. [`e2p3-secondary-real-device-qualification-freeze`](../experiments/epoch2-archive-qualification/secondary-real-device-qualification-authority.json) — bounded dual-real-device compatibility evidence
4. [`document-lifecycle-control-plane-phase1`](../experiments/document-lifecycle-control/document-lifecycle-control-authority.json) — documentation lifecycle registry control plane
5. [`document-current-state-authority-phase2`](../experiments/document-current-state/document-current-state-authority.json) — single current-state authority and generated-view contract

## Blockers

None.

## Unresolved risks

- official upstream package and BeeWare dependency identities are not yet frozen under UT-0
- directory-level generated navigation and historical indexes remain Phase 3 work
- mixed legacy documents remain byte-preserved historical snapshots pending Phase 4 normalization

## Immediate reading path

1. [`current/STATE.json`](current/STATE.json)
2. [`documentation/CURRENT_STATE_AUTHORITY.md`](documentation/CURRENT_STATE_AUTHORITY.md)
3. [`roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md`](roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md)
4. [`INDEX.md`](INDEX.md)

## Update rule

Change temporal facts only in `current/STATE.json`, update the registry if inventory or lifecycle metadata changes, then render and verify all views in the same transaction.
