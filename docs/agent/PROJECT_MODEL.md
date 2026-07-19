# Project Model

> **Revision:** 1
> **Role:** mandatory stable semantics for every agent session
> **Temporal authority:** [`../current/STATE.json`](../current/STATE.json)

## PM-01 — Project identity

This repository is the evidence-driven research and governance environment for producing an upstream-derived, Android/Bionic-native standalone CPython CLI runtime and for determining the adaptations required by Termux, uv, ADB, root-shell, and application consumers.

It is not the final release repository, a CPython fork, a replacement for Termux Python, or proof that every demonstrated capability belongs in the product.

## PM-02 — Governing method

```text
understand -> reproduce -> measure -> compare -> design -> optimize
```

Upstream design is the default reference. Android-specific divergence must be proven necessary, bounded, and documented. Existing implementation is evidence, not automatic product selection.

## PM-03 — Epoch roles

```text
Epoch 2  experiments, failure discovery, adaptation evidence, and decision inputs
Epoch 3  clean Astral-like product assembly and explicit feature selection
Epoch 4  optional source-producer replacement under the frozen consumer contract
```

Epoch 2 must finish required experiments before Epoch 3 structural assembly. Epoch 3 must not silently inherit every successful experiment.

## PM-04 — Typed authority

```text
project rule          -> ADR, epoch charter, stable project model
current coordinates   -> docs/current/STATE.json
current agent task    -> docs/current/AGENT_TASK.json
program structure     -> canonical active plan
accepted claim        -> frozen contract + evidence + audit + machine authority
past statement        -> historical snapshot at its recorded boundary
external source       -> interpreted reference plus exact raw capture
where to find a file  -> generated navigation
```

No global newest-file rule exists across authority domains.

## PM-05 — Documentation lifecycle

Stable rules, current state, active plans, generated views, frozen authority, and history have different owners and update triggers. `STATE.json` is the sole temporal source. Generated views never create claims. Historical words such as `active`, `next`, or `pending` remain relative to their snapshot and never override current state.

New authorities must not bind mutable current sources or generated views. Historical bindings are resolved through immutable compatibility snapshots.

## PM-06 — Evidence and claim discipline

Complete independently audited target evidence outranks local reconstruction, static inspection, design intent, and chat memory. A structural PASS can validate a failure archive without making the product stage PASS. Narrow evidence must not be expanded into device, architecture, selectability, publication, or release claims that were not tested.

## PM-07 — Reading discipline

Every session starts at the immutable root bootstrap, reads the mandatory closure, then follows the generated task manifest at section granularity. Exhaustive navigation, history, unrelated evidence, and unrelated experiments are default-denied because language-model context is a bounded project resource.

The agent records every read outside the task manifest and its justification.

## PM-08 — Product and collaboration boundary

The project owner controls canonical scope, the S22 main checkout, device execution, and final integration. The agent reconstructs exact bundle state, performs bounded analysis and implementation, writes verification, and delivers a one-runner package. Tooling convenience never substitutes for authority identity, target evidence, or owner control.
