# Standalone Component Incubator

Future ownership:

- CPython Android producer and dependency recipes;
- launcher and relocatable runtime core;
- runtime/development assembly;
- archive flavors and metadata;
- native closure and product qualification;
- release automation and public standalone assets.

E2-P1 freezes contract version 1 in:

```text
docs/contracts/E2P1_STANDALONE_ARTIFACT_CONTRACT.md
experiments/epoch2-standalone-artifact-contract/
```

The primary flavor is `install_only_stripped`, with a single `python/` root and runtime plus development payloads. E2-P2 may introduce stable build/package/verify façades, but implementation files do not move merely to populate this directory.
