# Stage 3-F Scope: Publication and Acquisition Boundaries

> **Status:** FROZEN — Gate 5 independent publication/acquisition freeze complete
> **Input:** frozen Stage 3-E Gate 5 exact-key local managed-Python distribution
> **Canonical branch:** `agent/stage3f-publication-acquisition`

## Final result

Stage 3-F accepts one corrected retained-snapshot acquisition authority for the frozen CPython 3.14.5 and 3.14.6 runtime-only products. It preserves eight separate authorities: product identity, catalog row, publication snapshot, endpoint locator, transport observation, acquisition candidate, verified cache, and installation root.

```text
Gate 1  authority design                       FROZEN
Gate 2  canonical snapshot contract            FROZEN — 18/18
Gate 3  loopback acquisition engine            FROZEN — 31/31
Gate 4  retained actual-byte target validation FROZEN — 16/16 + 31/31
Gate 5  independent freeze                     FROZEN
```

## Selectable authority

```text
3.14.5  size 9761545   sha256 2edec6cfaf20a44b2458567856c1d505e6942d0e43da0e8ba2a36761ebc05be2
3.14.6  size 11788907  sha256 f0c449f7bc5b5bd740f4776f43bec4418645d5f33da220fa523409b6aa0af208
snapshot body sha256   dbdc0edd20eeca1506066c6ec95078d9ad4fe231b81a13aa1236b480d3faa233
snapshot file sha256   419a9d4303fd6b3d7686400c7a275117ae6fe3421c93c30ff356529fc483b9e3
```

The original Gate 2 concrete snapshot is historical and unselectable. Gate 4 v1 failure is preserved. The retained Gate 4 snapshot is selectable because its exact bytes are retained in accepted evidence. Ordinary exact-key mutation remains forbidden.

## Accepted evidence

```text
Gate 4 target result       6cba95839a5dc05a7d4261467f1b7693e9d232fd44abe21ca4712e09b8e1977b
Gate 4 target matrix       16/16 PASS
Gate 4 independent audit   31/31 PASS
payload fidelity           714/714 strict per product
Gate 4 record result       daaf64255fce6d9c1ef2f5eb5e57d8dcc85472a4be48e56c47f21b94dee891f8
Gate 4 record control      91/91 PASS
```

## Explicit nonclaims

No public availability, performance, DNS/TLS/origin authenticity, signature policy, production redirect or mirror policy, uv automatic acquisition, product execution, installation, resumable or concurrent download, cache eviction, default managed root, global link, upgrade, recovery, concurrency, power-loss durability, third-product compatibility, or upstream uv Android support is accepted.

A new stage authority is required for any further publication or acquisition work.
