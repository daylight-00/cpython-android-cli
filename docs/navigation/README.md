# Documentation Navigation

> **Generated root:** registry v5 + [`docs/current/STATE.json`](../current/STATE.json).
> Start with the stable project guide, then use typed indexes for current state, plans, authority, and history.

## Primary entry

- [`docs/PROJECT_GUIDE.md`](../PROJECT_GUIDE.md)

## Current coordinates

```text
immediate action  execute-e2-r1-ut0-exact-official-upstream-control
program gate      E2-R1/UT-0 — exact official upstream control
tracked docs      501
index targets     15
```

## Lifecycle distribution

- `ACTIVE_PLAN`: 2
- `APPEND_ONLY_LOG`: 1
- `CURRENT_INPUT_LOCK`: 2
- `CURRENT_REGISTRY`: 1
- `CURRENT_SOURCE`: 1
- `FROZEN_AUTHORITY`: 258
- `GENERATED_VIEW`: 18
- `HISTORICAL_SNAPSHOT`: 170
- `RAW_REFERENCE`: 5
- `REFERENCE`: 5
- `STABLE`: 36
- `STABLE_WITH_GENERATED_SECTION`: 2

## Generated entrypoints

- [`docs/current/README.md`](../current/README.md) — current-state directory index
- [`docs/documentation/README.md`](../documentation/README.md) — documentation governance index
- [`docs/decisions/README.md`](../decisions/README.md) — decision index
- [`docs/epochs/README.md`](../epochs/README.md) — epoch charter and history index
- [`docs/architecture/README.md`](../architecture/README.md) — architecture index
- [`docs/roadmap/README.md`](../roadmap/README.md) — current plans and historical plan snapshots
- [`docs/contracts/README.md`](../contracts/README.md) — contract index
- [`docs/evidence/README.md`](../evidence/README.md) — evidence index
- [`docs/stages/README.md`](../stages/README.md) — stage snapshot index
- [`docs/handoff/README.md`](../handoff/README.md) — handoff index
- [`docs/history/README.md`](../history/README.md) — legacy context and orientation history
- [`docs/history/legacy-authority-bindings/README.md`](../history/legacy-authority-bindings/README.md) — legacy authority compatibility snapshot index
- [`docs/references/README.md`](../references/README.md) — reference index
- [`experiments/README.md`](../../experiments/README.md) — experiment index

## Other canonical roots

- [`README.md`](../../README.md) — `STABLE_WITH_GENERATED_SECTION` · `public_orientation` · owner `project-governance`
- [`components/README.md`](../../components/README.md) — `STABLE` · `component_contract` · owner `component-governance`
- [`components/installer/README.md`](../../components/installer/README.md) — `STABLE` · `component_contract` · owner `installer-component`
- [`components/standalone/README.md`](../../components/standalone/README.md) — `STABLE` · `component_contract` · owner `standalone-component`
- [`components/standalone/contracts/facade-v1.json`](../../components/standalone/contracts/facade-v1.json) — `FROZEN_AUTHORITY` · `machine_contract` · owner `standalone-component`
- [`components/standalone/contracts/qualification-v1.json`](../../components/standalone/contracts/qualification-v1.json) — `FROZEN_AUTHORITY` · `machine_contract` · owner `standalone-component`
- [`components/standalone/contracts/termux-native-cpython3146-producer-binding-v1.json`](../../components/standalone/contracts/termux-native-cpython3146-producer-binding-v1.json) — `FROZEN_AUTHORITY` · `machine_contract` · owner `standalone-component`
- [`components/standalone/schemas/qualification-result-v1.schema.json`](../../components/standalone/schemas/qualification-result-v1.schema.json) — `STABLE` · `machine_contract` · owner `standalone-component`
- [`config/dependencies/android-source-deps-aarch64-linux-android.lock.json`](../../config/dependencies/android-source-deps-aarch64-linux-android.lock.json) — `CURRENT_INPUT_LOCK` · `program_input` · owner `product-input-governance`
- [`config/products/cpython-3.14.6-aarch64-linux-android.lock.json`](../../config/products/cpython-3.14.6-aarch64-linux-android.lock.json) — `CURRENT_INPUT_LOCK` · `program_input` · owner `product-input-governance`
- [`docs/CURRENT_CONTEXT.md`](../CURRENT_CONTEXT.md) — `GENERATED_VIEW` · `temporal_state_view` · owner `program-governance`
- [`docs/GITHUB_COLLABORATION_WORKFLOW.md`](../GITHUB_COLLABORATION_WORKFLOW.md) — `STABLE` · `session_operations` · owner `session-operations`
- [`docs/INDEX.md`](../INDEX.md) — `GENERATED_VIEW` · `navigation` · owner `program-governance`
- [`docs/PROJECT_GUIDE.md`](../PROJECT_GUIDE.md) — `STABLE` · `project_orientation` · owner `architecture-governance`
- [`docs/SESSION_ONBOARDING.md`](../SESSION_ONBOARDING.md) — `STABLE_WITH_GENERATED_SECTION` · `session_operations` · owner `session-operations`
- [`docs/session-operations/AGENT_WORK_METHOD.md`](../session-operations/AGENT_WORK_METHOD.md) — `STABLE` · `session_operations` · owner `session-operations`
- [`docs/session-operations/COLLABORATION_AND_TRANSPORT.md`](../session-operations/COLLABORATION_AND_TRANSPORT.md) — `STABLE` · `session_operations` · owner `session-operations`
- [`docs/session-operations/HANDOFF_PACKAGE_SPEC.md`](../session-operations/HANDOFF_PACKAGE_SPEC.md) — `STABLE` · `session_operations` · owner `session-operations`
- [`docs/session-operations/LESSONS_AND_CHANGELOG.md`](../session-operations/LESSONS_AND_CHANGELOG.md) — `APPEND_ONLY_LOG` · `session_operations` · owner `session-operations`
- [`docs/session-operations/README.md`](../session-operations/README.md) — `STABLE` · `session_operations` · owner `session-operations`
- [`docs/session-operations/SESSION_CLOSE_INITIALIZATION.md`](../session-operations/SESSION_CLOSE_INITIALIZATION.md) — `STABLE` · `session_operations` · owner `session-operations`
- [`docs/session-operations/SESSION_CYCLE.md`](../session-operations/SESSION_CYCLE.md) — `STABLE` · `session_operations` · owner `session-operations`
- [`docs/session-operations/templates/DATED_HANDOFF_TEMPLATE.md`](../session-operations/templates/DATED_HANDOFF_TEMPLATE.md) — `STABLE` · `session_operations` · owner `session-operations`
- [`docs/session-operations/templates/HANDOFF_MANIFEST.example.json`](../session-operations/templates/HANDOFF_MANIFEST.example.json) — `STABLE` · `session_operations` · owner `session-operations`

## Interpretation rule

`STATE.json` owns present coordinates. Active plans own future structure. Frozen authority owns accepted claims. Historical status language is snapshot-relative and never overrides current state.
