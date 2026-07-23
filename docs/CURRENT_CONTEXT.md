# Current Project Context

> **Generated view:** [`docs/current/STATE.json`](current/STATE.json) is the sole temporal authority.
> **State revision:** 44
> **Agent sessions:** start at [`AGENT_BOOTSTRAP.md`](../AGENT_BOOTSTRAP.md).
> **Do not hand-edit.**

## Current agent route

```text
bootstrap       AGENT_BOOTSTRAP.md
task manifest   docs/current/AGENT_TASK.json
action          resolve-epoch3-release-blocking-experiments
work gate       E3/RELEASE-BLOCKERS — Release-blocking evidence, data products, compatibility, runtime contexts, and operations
```

## Mandatory project and session modules

- [`docs/agent/PROJECT_MODEL.md`](agent/PROJECT_MODEL.md)
- [`docs/agent/SESSION_PROTOCOL.md`](agent/SESSION_PROTOCOL.md)
- [`docs/current/STATE.json`](current/STATE.json)
- [`docs/current/AGENT_TASK.json`](current/AGENT_TASK.json)

## Program position

```text
epoch   E3 — clean upstream-derived Android standalone distribution
gate    E3/RELEASE-BLOCKERS — Release-blocking evidence, data products, compatibility, runtime contexts, and operations
status  in-progress
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
21. [`experiments/epoch3-upstream-thin-initialization/initialization-authority.json`](../experiments/epoch3-upstream-thin-initialization/initialization-authority.json) — complete Epoch 3 selection register, clean repository boundary, product contract freeze, independent audit, and canonical full implementation start
22. [`experiments/epoch3-upstream-thin-full/full-authority.json`](../experiments/epoch3-upstream-thin-full/full-authority.json) — canonical deterministic Astral-structured upstream-thin full archive, Android/Bionic qualification, projection invariant, and install-only start authority
23. [`experiments/epoch3-upstream-thin-install-only/install-only-authority.json`](../experiments/epoch3-upstream-thin-install-only/install-only-authority.json) — canonical exact full projection, Android/Bionic qualification, and stripped start authority
24. [`experiments/epoch3-upstream-thin-stripped/stripped-authority.json`](../experiments/epoch3-upstream-thin-stripped/stripped-authority.json) — canonical bounded install-only-stripped derivation, Android/Bionic qualification, and artifact-family start authority
25. [`experiments/epoch3-upstream-thin-artifact-family/artifact-family-authority.json`](../experiments/epoch3-upstream-thin-artifact-family/artifact-family-authority.json) — canonical deterministic three-artifact release family, exact artifact identities, sidecars, checksums, release index, reproducibility, and release-blocker start authority
26. [`experiments/epoch3-upstream-thin-release-blockers/rb1-baseline-authority.json`](../experiments/epoch3-upstream-thin-release-blockers/rb1-baseline-authority.json) — frozen exact component/license baseline, explicit 12-gap register, and source-provenance resolution start authority
27. [`experiments/epoch3-upstream-thin-release-blockers/rb1-source-provenance-authority.json`](../experiments/epoch3-upstream-thin-release-blockers/rb1-source-provenance-authority.json) — frozen exact six-dependency source provenance, libffi resolution, CPython source identity, mismatch quarantine, and license-payload acquisition start authority
28. [`experiments/epoch3-upstream-thin-release-blockers/rb1-license-payload-authority.json`](../experiments/epoch3-upstream-thin-release-blockers/rb1-license-payload-authority.json) — frozen exact five-source license payload acquisition, 13-component expansion, eight-gap boundary, and legal-overlay evidence synthesis start authority
29. [`experiments/epoch3-upstream-thin-release-blockers/rb1-license-payload-authority-verification-amendment.json`](../experiments/epoch3-upstream-thin-release-blockers/rb1-license-payload-authority-verification-amendment.json) — non-claiming correction binding the payload authority to the actual 23-check acceptance verifier output
30. [`experiments/epoch3-upstream-thin-release-blockers/rb1-legal-overlay-authority.json`](../experiments/epoch3-upstream-thin-release-blockers/rb1-legal-overlay-authority.json) — frozen deterministic 72-file legal evidence overlay, exact four-gap boundary, and legal-integration start authority
31. [`experiments/epoch3-upstream-thin-release-blockers/rb1-legal-integration-authority.json`](../experiments/epoch3-upstream-thin-release-blockers/rb1-legal-integration-authority.json) — frozen exact 128-file legally integrated family candidate and final owner-notice approval start authority
32. [`experiments/epoch3-upstream-thin-release-blockers/rb2-data-product-authority.json`](../experiments/epoch3-upstream-thin-release-blockers/rb2-data-product-authority.json) — frozen deterministic current and rollback CA/timezone data products, update/rollback lifecycle, exact Android runtime qualification, and RB-2 closure authority
33. [`experiments/epoch3-upstream-thin-release-blockers/rb3-sysconfig-profile-selection-authority.json`](../experiments/epoch3-upstream-thin-release-blockers/rb3-sysconfig-profile-selection-authority.json) — Selected profile M authority; preserves upstream producer metadata while authorizing only measured consumer/toolchain adaptations.
34. [`experiments/epoch3-upstream-thin-release-blockers/rb3-distributor-responsibility-reassessment.json`](../experiments/epoch3-upstream-thin-release-blockers/rb3-distributor-responsibility-reassessment.json) — distributor artifact responsibility, external user-wheel repair boundary, and Android 16 KiB SDK obligation
35. [`experiments/epoch3-upstream-thin-release-blockers/rb3-successor-full-m-r1-return-inspection.json`](../experiments/epoch3-upstream-thin-release-blockers/rb3-successor-full-m-r1-return-inspection.json) — exact failed successor-full r1 receipt, rollback, and deterministic receipt correction boundary
36. [`experiments/epoch3-upstream-thin-release-blockers/rb3-successor-full-m-r2-return-inspection.json`](../experiments/epoch3-upstream-thin-release-blockers/rb3-successor-full-m-r2-return-inspection.json) — exact reproducible successor r2 failure receipt, truthful host-triple correction, and uv-managed sysconfig rewrite correction boundary
37. [`experiments/epoch3-upstream-thin-release-blockers/rb3-successor-full-m-r3-return-inspection.json`](../experiments/epoch3-upstream-thin-release-blockers/rb3-successor-full-m-r3-return-inspection.json) — exact successful successor r3 product qualification evidence and bounded managed-find verifier observation-order correction
38. [`experiments/epoch3-upstream-thin-release-blockers/rb3-successor-full-m-acceptance-r1-return-inspection.json`](../experiments/epoch3-upstream-thin-release-blockers/rb3-successor-full-m-acceptance-r1-return-inspection.json) — exact failed acceptance-r1 unit receipt, clean rollback, and tracked-committed-tree negative-test isolation correction boundary
39. [`experiments/epoch3-upstream-thin-release-blockers/rb3-successor-full-m-authority.json`](../experiments/epoch3-upstream-thin-release-blockers/rb3-successor-full-m-authority.json) — accepted deterministic profile-M successor full r5 with structural, Android runtime, uv system/managed, direct/managed native SDK 16 KiB, protected-state, and independent acceptance evidence
40. [`experiments/epoch3-upstream-thin-release-blockers/rb3-successor-full-m-acceptance-r2-return-inspection.json`](../experiments/epoch3-upstream-thin-release-blockers/rb3-successor-full-m-acceptance-r2-return-inspection.json) — exact successful acceptance-r2 receipt, pushed full-r5 acceptance, and successor install-only derivation start boundary
41. [`experiments/epoch3-upstream-thin-release-blockers/rb3-successor-install-only-m-r1-return-inspection.json`](../experiments/epoch3-upstream-thin-release-blockers/rb3-successor-install-only-m-r1-return-inspection.json) — frozen successful target qualification and failed audit receipt-schema mismatch boundary
42. [`experiments/epoch3-upstream-thin-release-blockers/rb3-successor-install-only-m-r2-return-inspection.json`](../experiments/epoch3-upstream-thin-release-blockers/rb3-successor-install-only-m-r2-return-inspection.json) — exact successful r2 owner receipt, deterministic install-only candidate identity, complete Android/uv/native-SDK qualification, and bounded acceptance input
43. [`experiments/epoch3-upstream-thin-release-blockers/rb3-successor-install-only-m-authority.json`](../experiments/epoch3-upstream-thin-release-blockers/rb3-successor-install-only-m-authority.json) — accepted deterministic successor install-only r5 with exact full projection, Android runtime, uv system/managed, direct/managed native SDK 16 KiB, protected-state, and independent acceptance evidence

## Blockers

- RB-1-component-and-license-closure
- RB-3-sysconfig-sdk-and-astral-consumer-boundary
- RB-4-release-security-update-and-revocation-operations
- RB-5-api24-runtime-qualification
- RB-6-real-16k-runtime-qualification
- RB-7-non-termux-android-runtime-qualification

## Unresolved risks

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
- final-notice-set-not-owner-approved
- owner-approval-must-bind-exact-release-and-notice-hashes
- rb1-owner-review-result-receipt-index-incomplete-dossier-valid
- zero-producer-path-rule-not-derived-from-astral-golden-contract
- frozen-predecessor-family-not-superseded
- rb3-closure-requires-successor-full-install-only-stripped-family-and-legal-data-rebinding
- user-built-wheel-portability-and-repair-explicitly-out-of-scope
- predecessor-family-remains-canonical-until-successor-family-acceptance-and-explicit-supersession
- successor-install-only-r5-accepted-successor-stripped-derivation-pending

History, handoffs, stages, unrelated evidence, unrelated experiments, and unselected roadmap sections are excluded from onboarding unless the generated task manifest requires them.
