# Document lifecycle control plane

> **Status:** frozen Phase 1 control-plane authority

This experiment establishes a non-disruptive lifecycle registry over every tracked Markdown and JSON document.

## Scope

- classify all pre-existing 405 Markdown/JSON documents;
- add the lifecycle constitution, registry schema, registry, and exact legacy live-binding baseline;
- require all tracked Markdown/JSON paths to be registered exactly once;
- reject missing metadata and invalid lifecycle values;
- grandfather exactly 24 pre-existing live-document `file_identities` bindings;
- reject any new binding to a forbidden live/generated path;
- preserve all historical and frozen document bytes;
- do not introduce `docs/current/STATE.json` yet;
- do not move paths or regenerate the current quartet.

## Stable commands

```bash
python3 experiments/document-lifecycle-control/verify-document-registry.py --root .
python3 experiments/document-lifecycle-control/test-document-registry.py
```

Phase 2 will introduce the single temporal state authority and render current views from it.
