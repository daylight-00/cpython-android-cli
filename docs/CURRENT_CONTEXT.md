# Current Project Context

> **Generated view:** [`docs/current/STATE.json`](current/STATE.json) is the sole temporal authority.
> **State revision:** 16
> **Agent sessions:** start at [`AGENT_BOOTSTRAP.md`](../AGENT_BOOTSTRAP.md).
> **Do not hand-edit.**

## Current agent route

```text
bootstrap       AGENT_BOOTSTRAP.md
task manifest   docs/current/AGENT_TASK.json
action          initialize-epoch3-from-accepted-evidence-export
work gate       E3/INIT — Epoch 3 initialization decisions and contract freeze
```

## Mandatory project and session modules

- [`docs/agent/PROJECT_MODEL.md`](agent/PROJECT_MODEL.md)
- [`docs/agent/SESSION_PROTOCOL.md`](agent/SESSION_PROTOCOL.md)
- [`docs/current/STATE.json`](current/STATE.json)
- [`docs/current/AGENT_TASK.json`](current/AGENT_TASK.json)

## Program position

```text
epoch   E3 — clean upstream-derived Android standalone distribution
gate    E3/INIT — Epoch 3 initialization decisions and contract freeze
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
18. [`experiments/epoch2-upstream-thin-upstream-evolution/upstream-evolution-authority.json`](../experiments/epoch2-upstream-thin-upstream-evolution/upstream-evolution-authority.json) — official patch-update rehearsal, Python 3.15 preview delta, maintenance burden, and security ownership
19. [`experiments/epoch2-upstream-thin-api36-controlled-comparison/api36-controlled-comparison-authority.json`](../experiments/epoch2-upstream-thin-api36-controlled-comparison/api36-controlled-comparison-authority.json) — API-24 official and API-36 source-equivalent three-class controlled comparison
20. [`experiments/epoch2-upstream-thin-closure/closure-authority.json`](../experiments/epoch2-upstream-thin-closure/closure-authority.json) — Epoch 2 closure, accepted upstream-derived seed, selection inputs, and Epoch 3 initialization boundary

## Blockers

None.

## Unresolved risks

- minimum-supported-Android-API-unselected
- runtime-16KiB-device-support-unqualified
- ADB-root-APK-and-non-Termux-contexts-unqualified
- emulator-unqualified-and-waived
- other-Android-ABIs-unqualified
- CA-and-timezone-payload-provider-and-update-policy-unselected
- multiprocessing-environment-inadequate
- pre-existing-venv-after-base-relocation-fails
- install_only_stripped-duplicates-install_only
- runtime-only-versus-on-device-SDK-versus-cross-SDK-unselected
- uv-system-versus-managed-contract-unselected
- API36-production-input-would-require-stable-official-NDK-reproduction
- upstream-derived-full-differs-from-Astral-source-producer-full
- supported-version-release-cadence-security-and-data-update-operations-unselected
- source-producer-host-isolation-and-libffi-fix-deferred
- publication-not-authorized

History, handoffs, stages, unrelated evidence, unrelated experiments, and unselected roadmap sections are excluded from onboarding unless the generated task manifest requires them.
