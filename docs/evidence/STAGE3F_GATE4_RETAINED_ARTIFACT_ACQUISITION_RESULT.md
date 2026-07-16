# Stage 3-F Gate 4 Retained-Artifact Acquisition Result

> **Status:** ACCEPTED — target evidence and independent archive audit complete
> **Repository input:** `72713db607bbead29f45e86617edc7ca05617fc4`, tree `8c1b67d4dfebbc9266213f8374db0a3cf912fd91`

## Accepted result

```text
work id              20260716-stage3f-gate4a-retained-artifact-acquisition-v2
archive sha256       6cba95839a5dc05a7d4261467f1b7693e9d232fd44abe21ca4712e09b8e1977b
archive size         42968242
safe archive members 62
self-index            46/46 exact
target matrix         16/16 PASS
independent verifier  31/31 PASS
```

## Retained artifact identities

```text
3.14.5 size    9761545
3.14.5 sha256  2edec6cfaf20a44b2458567856c1d505e6942d0e43da0e8ba2a36761ebc05be2
3.14.5 payload 714/714 strict fidelity

3.14.6 size    11788907
3.14.6 sha256  f0c449f7bc5b5bd740f4776f43bec4418645d5f33da220fa523409b6aa0af208
3.14.6 payload 714/714 strict fidelity

snapshot body  dbdc0edd20eeca1506066c6ec95078d9ad4fe231b81a13aa1236b480d3faa233
snapshot file  419a9d4303fd6b3d7686400c7a275117ae6fe3421c93c30ff356529fc483b9e3
snapshot size  2997
```

The result archive contains the exact two verified archive objects, corrected canonical snapshot, transport observations, strict payload-fidelity reports, protected-state snapshots, negative caches proving peer preservation, all logs, and a complete self-index.

## Acceptance

Both complete archives were transferred over `127.0.0.1`, observed independently, promoted to isolated content-addressed paths, and returned as cache hits without further requests. A truncated 3.14.5 transfer and same-size corrupt 3.14.6 transfer failed closed, left no candidates, did not create the bad target object, and preserved the verified peer.

Repository, package inputs, real managed root, global bin, shell state, registries, and journals remained unchanged. uv and the products were not executed. No installation or external network operation occurred.

## Retention correction

The historical Gate 2 snapshot remains preserved as local canonicalization evidence, but it is not selectable for acquisition because its exact artifact bytes were not retained. The retained Gate 4 snapshot explicitly supersedes it as the active acquisition authority. This is a recorded authority repair, not permission for ordinary exact-key mutation.
