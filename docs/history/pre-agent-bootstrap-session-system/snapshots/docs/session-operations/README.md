# Session Operations

This directory is the canonical home for cross-session operating rules external to the project's experimental claims.

It covers responsibility split, Drive/local-Git transport, package classes, selective evidence inspection, session start/close, and connector lessons. It does not define project architecture, gate status, product identity, runtime behavior, provenance, or acceptance claims.

## Maintenance

- Update these files whenever collaboration mechanics or tooling lessons change, even if no gate changes.
- Put changing project state in a dated `docs/handoff/` file.
- Put frozen experimental conclusions in `docs/evidence/` and the relevant experiment directory.
- A dated handoff may override a stable default only for one explicitly named work item.

## Documents

- `COLLABORATION_AND_TRANSPORT.md`: roles, Drive layout, package taxonomy, Git and connector rules.
- `AGENT_WORK_METHOD.md`: scope, implementation, audit, failure, and reporting discipline.
- `SESSION_CYCLE.md`: the complete receive-to-next-handoff cycle.
- `SESSION_CLOSE_INITIALIZATION.md`: canonical close instruction.
- `HANDOFF_PACKAGE_SPEC.md`: machine- and human-readable handoff package contract.
- `LESSONS_AND_CHANGELOG.md`: accumulated operational lessons and changes.
- `templates/`: reusable dated-handoff and manifest starting points.

## Documentation lifecycle control

- [`../documentation/DOCUMENT_LIFECYCLE.md`](../documentation/DOCUMENT_LIFECYCLE.md): lifecycle classes, typed authority, update triggers, supersession, and machine-binding policy.
- [`../documentation/document-registry.json`](../documentation/document-registry.json): complete tracked Markdown/JSON registry.
- [`../../experiments/document-lifecycle-control/`](../../experiments/document-lifecycle-control/): verifier, negative fixtures, authority, and external audit.

The lifecycle registry changes with the document set. Frozen and historical content remains byte-preserved unless an explicit later migration proves an edit safe.
