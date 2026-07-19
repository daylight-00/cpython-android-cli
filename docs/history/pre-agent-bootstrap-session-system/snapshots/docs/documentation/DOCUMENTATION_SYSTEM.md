# Documentation System

> **Lifecycle:** stable governance
> **Current source:** [`../current/STATE.json`](../current/STATE.json)
> **Registry:** [`document-registry.json`](document-registry.json)

## Layer model

```text
stable governance
  identity, architecture, procedures, schemas

current source
  one machine-readable temporal record

generated views
  human current context and navigation

active plans
  work decomposition, gates, stop conditions

frozen authority
  contracts, evidence, audits, exact identities

historical snapshots
  byte-preserved statements valid at past boundaries
```

## Single-writer rules

Only `docs/current/STATE.json` owns present epoch, gate, immediate repository action, blockers, accepted authority identities, and current claim flags. Generated views are rendered from state and registry and must not be hand-edited.

Only canonical active plans own future work decomposition and acceptance conditions. Ordinary progress updates change state, evidence, or history—not the plan unless the design itself changes.

## Historical interpretation

Historical bytes are not rewritten to look current. Snapshot-relative words such as `active`, `next`, and `pending` describe the original boundary only. Generated history views expose lifecycle and successor metadata without changing old evidence.

## Machine binding

New authorities may bind immutable governance, versioned schemas, frozen authority, historical snapshots, and raw references when required. They must not bind live state, the live registry, generated views, or mutable sections of mixed documents.

Legacy bindings remain historical facts, but their verifier assumptions are resolved through `legacy-authority-decoupling-map.json`. Historical recorded digests bind immutable compatibility snapshots, not today's live paths.

## Update transaction

A documentation transition must update all affected sources, registry metadata, generated views, verification fixtures, and authority records in one exact repository transaction. A new session alone does not change project state.

Completed migration-phase contracts remain frozen at their original paths. Bulk physical relocation is not required: registry classification, generated navigation, immutable snapshots, and explicit successor metadata provide the canonical layer structure. This document is the stable successor for ongoing documentation-system rules.
