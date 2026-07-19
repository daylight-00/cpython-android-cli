# Documentation lifecycle and authority constitution

> **Status:** stable governance, version 1
> **Control-plane phase:** registry baseline established; current-state single writer not yet introduced

This document defines how repository documents are classified, updated, superseded, linked, and bound into machine authorities. It governs documentation mechanics only. It does not alter product bytes, experiment results, accepted claims, epoch selection, or release authorization.

## 1. Problem boundary

The repository contains several distinct kinds of documentation:

- stable project rules and architecture;
- live project coordinates and next actions;
- active plans and open work records;
- frozen contracts, evidence, audits, and authorities;
- historical session and stage snapshots;
- generated navigation views;
- interpreted and raw external references.

These kinds have different update frequencies and authority semantics. A document is not authoritative merely because it is recent, heavily linked, or located near the repository root.

## 2. Typed authority

Authority is domain-specific.

```text
question about project rules       -> ADR, charter, architecture, procedure
question about planned gates       -> active versioned plan
question about present coordinates -> current-state source, once introduced
question about a proven claim      -> frozen contract + evidence + machine authority
question about a past session      -> historical snapshot at its recorded commit
question about where to read       -> generated navigation view
question about an external source  -> interpreted reference + raw capture
```

No single global precedence order applies across these domains.

## 3. Lifecycle classes

### `STABLE`

Normative identity, architecture, procedure, or schema. Change only through an explicit policy or version transition.

### `STABLE_WITH_GENERATED_SECTION`

Stable prose containing a mechanically rendered live subsection. Stable prose and generated content must have explicit boundaries.

### `CURRENT_SOURCE`

The sole writable source for current epoch, current gate, next bounded action, active blockers, and latest accepted authority identities. This class is planned for Phase 2 and is not present in the Phase 1 baseline.

### `CURRENT_REGISTRY`

The complete registry of document lifecycle, ownership, update triggers, supersession rules, onboarding visibility, and machine-binding policy.

### `CURRENT_INPUT_LOCK`

A selected product or dependency identity that changes only when the selected input changes.

### `ACTIVE_PLAN`

Research decomposition, gate definitions, stop conditions, and selection criteria. Ordinary gate completion must not require changing a plan unless the plan itself changes.

### `APPEND_ONLY_LOG`

Accepted process lessons and changes. Existing entries are not rewritten.

### `FROZEN_AUTHORITY`

Versioned contracts, evidence, audits, schemas, authorities, and exact claim identities. Never edit in place after freeze. Correct through an amendment or new version.

### `HISTORICAL_SNAPSHOT`

A stage, session, experiment, or project-state narrative valid at a recorded point. Never edit to make it look current. Supersede through registry metadata or a newer snapshot.

### `GENERATED_VIEW`

Navigation or human-readable rendering derived from registry/state. It creates no claim and must not be bound into new historical `file_identities`.

### `REFERENCE`

An interpreted external source or model. Update only on source revision or accepted reinterpretation.

### `RAW_REFERENCE`

A byte-preserved source intake. Never edit; add a new dated capture.

## 4. Registry contract

`docs/documentation/document-registry.json` is the Phase 1 lifecycle registry.

The registry must cover every Git-tracked `.md` and `.json` path exactly once. Every entry records at least:

- lifecycle class;
- authority domain;
- owner;
- mutability;
- update trigger;
- supersession rule;
- onboarding visibility;
- machine-binding policy.

A document addition, removal, rename, lifecycle change, or supersession change requires a registry update in the same transaction.

The registry may describe future migration targets, but planned targets are not treated as existing documents until added to Git and registered as tracked paths.

## 5. Current-state single-writer rule

Phase 2 will introduce `docs/current/STATE.json` as the sole temporal source. After that transition, only that file may directly own:

- current epoch;
- current gate;
- next bounded action;
- current blockers;
- active work-package pointer;
- latest accepted authority identities.

`README.md`, `docs/CURRENT_CONTEXT.md`, `docs/INDEX.md`, and onboarding current sections will become generated renderings. Roadmaps will define gates but will not own live completion state.

Until Phase 2 is complete, existing current documents retain their established behavior. Phase 1 does not rewrite them.

## 6. Historical immutability

Do not mass-edit frozen or historical files to add banners. Existing byte identities and historical meaning must remain intact.

The registry supplies external metadata such as:

```text
lifecycle             HISTORICAL_SNAPSHOT
onboarding visibility history
migration action      mark-superseded-in-registry
planned successor     docs/current/STATE.json
```

Generated indexes will later display snapshot and supersession status without changing historical bytes.

## 7. Machine-binding policy

New authorities may bind stable, frozen, historical, versioned schema, or raw-reference files when semantically required.

New authorities must not bind:

- `GENERATED_VIEW` paths;
- live sections of `STABLE_WITH_GENERATED_SECTION` paths;
- mutable live roadmaps rather than immutable plan snapshots;
- active work records before freeze.

The Phase 1 baseline records pre-existing live-document bindings exactly. Those bindings remain historical facts but are grandfathered only at their existing authority path, target path, and digest. Any additional live/generated binding is a verifier failure.

## 8. Update matrix

| Event | Must update | Generated later | Must not update |
|---|---|---|---|
| Document added/removed | registry | indexes | unrelated frozen history |
| Experiment opened | active workspace; Phase 2 state | current views | frozen evidence |
| Result recorded | result artifacts/workspace | indexes | roadmap unless plan changed |
| Claim frozen | authority set; registry; Phase 2 state | authority/history views | prior authority bytes |
| Plan changed | versioned plan and decision authority | plan/current views | historical snapshots |
| New session | no project-state document by default | onboarding view | current documents manually |
| Session closed | dated handoff and registry | history view | prior handoff |
| External source changed | new raw capture and reference | reference view | old raw capture |

## 9. Migration phases

1. **Control plane:** constitution, registry, schema, verifier, exact legacy-binding baseline.
2. **Single current-state authority:** introduce `STATE.json` and render current views.
3. **Navigation normalization:** generate governance, plans, authorities, history, handoff, and experiment indexes.
4. **Mixed-document correction:** remove unqualified live state from stable/history/plan documents.
5. **Legacy authority decoupling:** make current-view changes independent of historical verifiers.
6. **Optional physical moves:** only after all verifier and link dependencies are decoupled.

## 10. Phase 1 invariants

The Phase 1 verifier fails when:

- a tracked Markdown/JSON file is absent from the registry;
- a registry path is not tracked;
- a path is registered more than once;
- required lifecycle metadata is missing or invalid;
- a current supersession target is declared but absent;
- the exact legacy live-binding baseline changes;
- a new authority binds a forbidden live/generated path;
- the control-plane files or verifier contract do not match the frozen authority.

Phase 1 deliberately does not move documents, rewrite historical bytes, introduce `STATE.json`, or regenerate the current quartet.
