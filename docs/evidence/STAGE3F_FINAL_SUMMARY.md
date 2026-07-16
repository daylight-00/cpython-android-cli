# Stage 3-F Final Summary

> **Status:** COMPLETE — frozen through Gate 5 after documentation-integrity correction

Stage 3-F separates product identity, catalog rows, immutable snapshots, endpoint locators, transport observations, acquisition candidates, verified caches, and installation roots.

```text
Gate 1  repository authority design                    frozen
Gate 2  canonical snapshot behavior                    frozen — 18/18
Gate 3  loopback acquisition implementation            frozen — 31/31
Gate 4  retained actual-byte Termux validation          frozen — 16/16 + 31/31
Gate 5  independent publication/acquisition freeze      frozen
```

The final selectable acquisition authority is the retained snapshot `dbdc0edd20eeca1506066c6ec95078d9ad4fe231b81a13aa1236b480d3faa233` over exact archives `2edec6cfaf20a44b2458567856c1d505e6942d0e43da0e8ba2a36761ebc05be2` and `f0c449f7bc5b5bd740f4776f43bec4418645d5f33da220fa523409b6aa0af208`. The accepted target archive is `6cba95839a5dc05a7d4261467f1b7693e9d232fd44abe21ca4712e09b8e1977b`. The accepted Gate 4 repository record archive is `daaf64255fce6d9c1ef2f5eb5e57d8dcc85472a4be48e56c47f21b94dee891f8`.

The original Gate 2 concrete snapshot is historical and unselectable because its exact bytes were not retained. Gate 4 v1 failed closed before acquisition and is preserved. Gate 4A retained exact bytes, proved strict payload fidelity, and completed the isolated loopback matrix.

Public hosting, origin trust, signatures, production redirects or mirrors, uv automatic acquisition, execution, installation, default-root integration, global links, upgrades, recovery, concurrency, durability, third products, and upstream uv Android support remain outside Stage 3-F.

The initial Gate 5 commit `71ded3869f38ed59118435f119a35591aee29f75` is preserved as a failed documentation-integrity attempt. Its marker-based checks passed, but it shortened six production documents. The corrective fast-forward commit restores the complete documents and adds structural preservation checks; it is the accepted final Stage 3-F documentation state.


## Correction v1 false-negative

The first documentation-correction wrapper result `69bfe223c5fb4f0dec42cf5b99ac35d346be9aaddb7438b82ce59e1d38af494a` made no repository mutation. Its only failed check treated pre-existing ignored bytecode anywhere in the working tree as newly created residue. Correction v2 captures the preflight bytecode inventory and rejects only new residue; standalone verification falls back to rejecting tracked bytecode.
