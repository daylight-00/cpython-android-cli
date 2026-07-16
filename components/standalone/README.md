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

The primary flavor is `install_only_stripped`, with a single `python/` root and runtime plus development payloads.

E2-P2 Gate 1 adds the stable façade:

```text
components/standalone/bin/cpython-android-standalone
components/standalone/contracts/facade-v1.json
components/standalone/lib/
```

Gate 1 verifies synthetic orchestration and deterministic envelope generation. Gate 2 must execute the real producer through this façade. Existing producer implementation files remain in their proven locations and are not moved merely to populate this directory.
