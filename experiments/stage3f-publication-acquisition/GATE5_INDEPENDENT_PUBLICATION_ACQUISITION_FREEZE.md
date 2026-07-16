# Stage 3-F Gate 5 Independent Publication/Acquisition Freeze

> **Status:** FROZEN
> **Repository input:** `1e7797218473463bc85f6413c49080301eda2ad7`, tree `a3a1cb90f12b20ab47203b4f6b47d8a9694b0e04`
> **Gate 4 record result:** `daaf64255fce6d9c1ef2f5eb5e57d8dcc85472a4be48e56c47f21b94dee891f8`

## Decision

Gate 5 closes Stage 3-F. The independent freeze accepts the corrected authority lineage, retained snapshot, Gate 4 target evidence, repository recording, canonical authorship, remote readback, and clean post-state.

```text
Gate 1  authority separation                         FROZEN
Gate 2  canonical snapshot contract                  FROZEN WITH RETENTION CORRECTION
Gate 3  fail-closed loopback acquisition engine      FROZEN — 31/31
Gate 4  retained actual-byte Termux acquisition      FROZEN — 16/16 + 31/31
Gate 5  independent publication/acquisition freeze   FROZEN
```

## Active retained authority

```text
3.14.5  9761545   2edec6cfaf20a44b2458567856c1d505e6942d0e43da0e8ba2a36761ebc05be2
3.14.6  11788907  f0c449f7bc5b5bd740f4776f43bec4418645d5f33da220fa523409b6aa0af208
snapshot body    dbdc0edd20eeca1506066c6ec95078d9ad4fe231b81a13aa1236b480d3faa233
snapshot file    419a9d4303fd6b3d7686400c7a275117ae6fe3421c93c30ff356529fc483b9e3
```

The historical Gate 2 concrete snapshot remains preserved but unselectable because its exact bytes were not retained. The retained Gate 4 snapshot is selectable. This is one explicit repair after preserved fail-closed evidence, not ordinary exact-key mutation.

## Accepted evidence

```text
Gate 4 target archive      6cba95839a5dc05a7d4261467f1b7693e9d232fd44abe21ca4712e09b8e1977b
archive size               42968242
safe members               62
self-index                 46/46
raw target matrix          16/16 PASS
independent target audit   31/31 PASS
payload fidelity           714/714 strict per product

Gate 4 record archive      daaf64255fce6d9c1ef2f5eb5e57d8dcc85472a4be48e56c47f21b94dee891f8
archive size               20514
safe members               49
self-index                 46/46
project control            91/91 PASS
```

## Boundary

No public endpoint, origin authentication, signature policy, production redirect or mirror policy, uv automatic acquisition, product execution, installation, default-root adoption, global link, upgrade, recovery, concurrency, durability, third-product, or upstream-support claim is accepted. Any such work requires a new stage authority.
