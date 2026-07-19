# Current-state authority and generated-view contract

> **Status:** stable governance, version 1
> **Lifecycle phase:** Phase 2 single current-state authority established
> **Predecessor:** [`DOCUMENT_LIFECYCLE.md`](DOCUMENT_LIFECYCLE.md)

This document extends the Phase 1 documentation lifecycle constitution without modifying its frozen bytes. It defines the temporal single-writer and deterministic rendering boundary.

## 1. Sole temporal writer

[`../current/STATE.json`](../current/STATE.json) is the only repository document that may directly own:

- immediate repository action;
- current research epoch and program gate;
- program action held ready while control work is active;
- active blockers and unresolved risks;
- current accepted authority identities;
- current bounded claim flags.

A transaction that changes any of those facts must update `STATE.json`. A new session does not update state merely because a session began.

## 2. No self-referential commit identity

The state records its predecessor HEAD/tree, a monotonic state revision, and the transaction class that created it. It does not attempt to contain the SHA of the commit that contains itself.

The containing repository commit and tree are derived from Git and transaction receipts.

## 3. Program work and control work

The state separates:

```text
program gate
  E2-R1 / UT-0 held ready

repository control work
  documentation lifecycle migration Phase 3 next
```

This prevents a documentation or governance transaction from erasing the research gate that must resume afterward.

## 4. Generated views

The following paths are deterministic render targets:

- `README.md` — generated current-state capsule inside stable prose;
- `docs/CURRENT_CONTEXT.md` — complete generated temporal view;
- `docs/INDEX.md` — generated top-level registry/state navigation;
- `docs/SESSION_ONBOARDING.md` — generated current reading block inside stable procedure.

Run:

```bash
python3 experiments/document-current-state/render-current-views.py --root .
python3 experiments/document-current-state/render-current-views.py --root . --check
```

Generated content must never be hand-edited. Stable text outside generated markers remains independently governed. Legacy files coupled to historical verifiers are reclassified through registry metadata rather than rewritten.

## 5. Machine binding

New historical authorities must not bind live state, the live registry, generated views, or stable documents' generated sections. The exact 24 legacy bindings remain grandfathered only as historical facts.

A historical authority may bind an immutable state snapshot, such as `experiments/document-current-state/baseline-current-state.json`, but not `docs/current/STATE.json`.

## 6. Update transaction

A temporal transition must perform, in one transaction:

1. update `STATE.json`;
2. update the lifecycle registry when the document inventory or lifecycle metadata changes;
3. render all targets;
4. run the current-state and registry verifier;
5. run negative fixtures;
6. verify frozen historical authority bytes against the exact predecessor and run the current bounded freeze verifier;
7. commit and verify the exact remote tree.

## 7. Remaining migration boundary

Phase 2 does not yet generate directory-level history, evidence, handoff, experiment, governance, or reference indexes. It does not move historical files or rewrite their bytes. Those are Phase 3 and later responsibilities.

## Fixture isolation

Negative fixtures must operate on the tracked document inventory rather than copying ignored runtime trees. The fixture Git repository requires only an index (`git init` plus `git add`), not a commit. Cleanup of temporary fixture directories is non-authoritative and must not turn a completed verification result into a failure.
