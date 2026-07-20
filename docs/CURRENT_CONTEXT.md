# Current Project Context

> **Generated view:** [`docs/current/STATE.json`](current/STATE.json) is the sole temporal authority.
> **State revision:** 13
> **Agent sessions:** start at [`AGENT_BOOTSTRAP.md`](../AGENT_BOOTSTRAP.md).
> **Do not hand-edit.**

## Current agent route

```text
bootstrap       AGENT_BOOTSTRAP.md
task manifest   docs/current/AGENT_TASK.json
action          execute-e2-r1-ut7-upstream-evolution-and-maintenance-portability
work gate       E2-R1/UT-7 — Upstream evolution and maintenance portability
```

## Mandatory project and session modules

- [`docs/agent/PROJECT_MODEL.md`](agent/PROJECT_MODEL.md)
- [`docs/agent/SESSION_PROTOCOL.md`](agent/SESSION_PROTOCOL.md)
- [`docs/current/STATE.json`](current/STATE.json)
- [`docs/current/AGENT_TASK.json`](current/AGENT_TASK.json)

## Program position

```text
epoch   E2 — upstream-thin research program
gate    E2-R1/UT-7 — Upstream evolution and maintenance portability
status  ready
```

## Accepted authorities

1. [`experiments/epoch2-recalibration/recalibration-authority.json`](../experiments/epoch2-recalibration/recalibration-authority.json) — program architecture and epoch boundary
2. [`experiments/epoch2-upstream-thin-plan/plan-authority.json`](../experiments/epoch2-upstream-thin-plan/plan-authority.json) — active research plan and completion gates
3. [`experiments/epoch2-archive-qualification/secondary-real-device-qualification-authority.json`](../experiments/epoch2-archive-qualification/secondary-real-device-qualification-authority.json) — bounded dual-real-device compatibility evidence
4. [`experiments/document-lifecycle-control/document-lifecycle-control-authority.json`](../experiments/document-lifecycle-control/document-lifecycle-control-authority.json) — documentation lifecycle registry control plane
5. [`experiments/document-current-state/document-current-state-authority.json`](../experiments/document-current-state/document-current-state-authority.json) — single current-state authority and generated-view contract
6. [`experiments/document-navigation/document-navigation-authority.json`](../experiments/document-navigation/document-navigation-authority.json) — complete generated documentation navigation and reachability
7. [`experiments/document-mixed-correction/document-mixed-correction-authority.json`](../experiments/document-mixed-correction/document-mixed-correction-authority.json) — stable/current/plan/history layer separation and snapshot interpretation
8. [`experiments/document-legacy-authority-decoupling/legacy-authority-decoupling-authority.json`](../experiments/document-legacy-authority-decoupling/legacy-authority-decoupling-authority.json) — legacy authority compatibility snapshots and completed documentation lifecycle migration
9. [`experiments/agent-bootstrap/agent-bootstrap-authority.json`](../experiments/agent-bootstrap/agent-bootstrap-authority.json) — immutable one-document agent onboarding, bundle-native session transport, and mandatory session-operation protocol
10. [`experiments/agent-task-completion/agent-task-completion-authority.json`](../experiments/agent-task-completion/agent-task-completion-authority.json) — task PASS/FAIL/update routing, successor readiness, and state/module/plan identity enforcement
11. [`experiments/epoch2-upstream-thin-control/upstream-control-authority.json`](../experiments/epoch2-upstream-thin-control/upstream-control-authority.json) — exact official Python.org Android package, topology, dependency, and provenance control
12. [`experiments/epoch2-upstream-thin-artifact-prototype/artifact-prototype-authority.json`](../experiments/epoch2-upstream-thin-artifact-prototype/artifact-prototype-authority.json) — truthful Astral-style local artifact and metadata prototype for the official binary-derived package
13. [`experiments/epoch2-upstream-thin-loader-relocation/loader-relocation-authority.json`](../experiments/epoch2-upstream-thin-loader-relocation/loader-relocation-authority.json) — bounded Android/Bionic loader, launcher, getpath, native closure, and whole-prefix relocation evidence
14. [`experiments/epoch2-upstream-thin-sysconfig-sdk/sysconfig-sdk-authority.json`](../experiments/epoch2-upstream-thin-sysconfig-sdk/sysconfig-sdk-authority.json) — relocation-aware sysconfig, consumer metadata, on-device native-extension SDK, and Android wheel evidence
15. [`experiments/epoch2-upstream-thin-android-data-policy/android-data-policy-authority.json`](../experiments/epoch2-upstream-thin-android-data-policy/android-data-policy-authority.json) — host-neutral CA, timezone, temporary, cache, bytecode, user-site, venv, read-only-install, and independent data-update policy
16. [`experiments/epoch2-upstream-thin-feature-qualification/feature-qualification-authority.json`](../experiments/epoch2-upstream-thin-feature-qualification/feature-qualification-authority.json) — explicit evidence-backed subprocess, venv, pip, uv, console-script, and multiprocessing support boundaries
17. [`experiments/epoch2-upstream-thin-platform-portability/platform-portability-authority.json`](../experiments/epoch2-upstream-thin-platform-portability/platform-portability-authority.json) — bounded current-target platform evidence, static 16 KiB compatibility, and explicit withheld claims

## Blockers

None.

## Unresolved risks

- UT-7 must rehearse an official 3.14 patch update and bound Python 3.15 preview deltas without converting preview evidence into a release claim.
- UT-6 withholds a minimum release API and runtime 16 KiB support until direct target evidence exists.

History, handoffs, stages, unrelated evidence, unrelated experiments, and unselected roadmap sections are excluded from onboarding unless the generated task manifest requires them.
