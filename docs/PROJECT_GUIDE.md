# Project Guide

> **Lifecycle:** stable project orientation
> **Temporal authority:** [`current/STATE.json`](current/STATE.json)
> **Complete navigation:** [`navigation/README.md`](navigation/README.md)

## Project identity

This repository investigates an upstream-derived, Android/Bionic-native standalone CPython CLI product and the adaptations required for practical Termux and uv consumption. It separates research evidence, product selection, source production, distribution, and consumer integration instead of treating them as one implementation problem.

The repository is:

- a laboratory for controlled Android/Bionic experiments;
- an evidence and authority archive;
- a place to define producer-independent product contracts;
- a staging area for later clean product repositories.

It is not, by repository existence alone, a release, a selectable catalog product, a CPython fork, or a replacement for Termux Python.

## Governing method

```text
understand -> reproduce -> measure -> compare -> design -> optimize
```

Authority is typed:

```text
project rule          -> ADR, epoch charter, architecture policy
program design        -> canonical active plan
present coordinates   -> current/STATE.json
proven claim          -> frozen contract, evidence, audit, authority
past session or stage -> historical snapshot
external source       -> interpreted reference plus raw capture
```

## Product boundary

Epoch 2 establishes feasibility, adaptation requirements, failures, and evidence dispositions. Epoch 3 selects the clean upstream-derived product. Epoch 4 may replace the selected binary-derived input with a full source producer without silently changing the consumer-visible contract.

Experiment success is evidence, not automatic product inclusion. Optional capabilities require an explicit selection decision.

## Reading rule

1. Read [`current/STATE.json`](current/STATE.json) for present coordinates.
2. Read [`CURRENT_CONTEXT.md`](CURRENT_CONTEXT.md) for the generated human view.
3. Read [`roadmap/EPOCH2_PROGRAM_PLAN.md`](roadmap/EPOCH2_PROGRAM_PLAN.md) and its detailed plan for program structure.
4. Use [`navigation/README.md`](navigation/README.md) to locate governance, evidence, experiments, references, and history.
5. Interpret every `HISTORICAL_SNAPSHOT` statement only at its recorded boundary.

Temporal coordinates, execution state, blockers, and completion status are intentionally outside this guide.
