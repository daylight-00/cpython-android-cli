# Legacy Authority Decoupling

> **Lifecycle:** stable documentation governance
> **Resolution map:** [`legacy-authority-decoupling-map.json`](legacy-authority-decoupling-map.json)
> **Original baseline:** [`legacy-live-binding-baseline.json`](legacy-live-binding-baseline.json)

## Problem

Six historical authorities contain 24 `file_identities` entries whose recorded paths are now live or generated documents. The authority bytes and recorded digests are valid historical facts, but treating those digests as requirements on today's live paths couples current navigation to old experimental boundaries.

## Resolution

Every grandfathered tuple

```text
(authority path, target path, recorded SHA-256)
```

is resolved to a byte-exact immutable snapshot under:

```text
docs/history/legacy-authority-bindings/
```

The original authority JSON is not rewritten. The original baseline is not rewritten. New verification interprets the old target path symbolically through the frozen decoupling map and verifies the snapshot bytes instead of comparing the recorded digest with the current live document.

## Ongoing rules

- new authorities must not bind current state, the live registry, generated views, or generated sections;
- the 24 old bindings may exist only as the exact baseline tuples;
- each old tuple must resolve to exactly one immutable snapshot;
- changing a live generated document does not alter historical compatibility evidence;
- changing a compatibility snapshot, map entry, or original authority tuple invalidates the decoupling authority;
- historical verifier replay against later current trees is not required;
- bulk physical document relocation is not required for lifecycle correctness.

This policy closes the documentation lifecycle migration. Current work resumes at the program action declared by `docs/current/STATE.json`.
