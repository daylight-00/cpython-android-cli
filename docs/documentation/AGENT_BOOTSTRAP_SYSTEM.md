# Agent Bootstrap and Bundle Session System

> **Lifecycle:** stable documentation and collaboration architecture
> **Immutable entrypoint:** [`../../AGENT_BOOTSTRAP.md`](../../AGENT_BOOTSTRAP.md)
> **Machine contract:** [`../agent/BOOTSTRAP_CONTRACT.json`](../agent/BOOTSTRAP_CONTRACT.json)

## Purpose

A project owner should be able to start a new language-model session by supplying a full Git bundle, its SHA-256 sidecar, and naming one document. The named document must deterministically load all mandatory project and collaboration semantics while preventing irrelevant repository history from consuming context.

## Fixed path ABI

```text
AGENT_BOOTSTRAP.md
docs/agent/PROJECT_MODEL.md
docs/agent/SESSION_PROTOCOL.md
docs/current/STATE.json
docs/current/AGENT_TASK.json
```

The root bootstrap is immutable. Project and operating rules evolve at their fixed module paths. Temporal coordinates change only in `STATE.json`. The task manifest is generated from state and the stable task catalog.

## Progressive disclosure

Mandatory reads are small and fixed. Task reads are explicit paths with section boundaries. History, handoffs, stages, unrelated evidence, unrelated experiments, and full plans are default-denied. Generated exhaustive navigation is lookup fallback, not onboarding input.

## Session transport

```text
owner -> agent  full Git bundle + sidecar
agent -> owner  one transaction package + sidecar + runner
owner -> agent  one complete PASS-or-FAIL receipt archive + sidecar
```

Google Drive is the first connector route. GitHub connector/API, network Git, and command-line DNS download workarounds are prohibited.

## Closure

The repository itself replaces the mandatory handoff package. A session closes only after state/task routing, evidence, generated views, verification, commit/push/readback, and clean-main conditions are satisfied. The owner creates the next full bundle with the repository export runner.
