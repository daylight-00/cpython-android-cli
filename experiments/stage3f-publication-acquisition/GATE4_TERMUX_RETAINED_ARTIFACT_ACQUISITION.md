# Stage 3-F Gate 4 Termux Retained-Artifact Acquisition

> **Status:** FROZEN — corrected retained-byte target evidence independently audited
> **Target:** Termux on Android arm64
> **Transport:** HTTP on `127.0.0.1` only
> **Installation:** none

## Correction lineage

The first Gate 4 attempt failed closed at derivation. Gate 2 had recorded hashes for transient managed-download archives but had not retained those exact bytes, and byte-identical regeneration was not part of the frozen contract. The failure archive is `2a076288652f1c342da49eccbe4507291df05d1d596b5c6f1d5646610b5990be`; no target acquisition or repository mutation occurred.

Gate 4A repairs the authority by retaining the exact archive bytes inside the result evidence, verifying each regenerated payload against its frozen runtime-base source with 714/714 strict entries, constructing a corrected retained snapshot, and executing the bounded loopback matrix against those exact bytes.

## Accepted identities

```text
cpython-3.14.5-linux-aarch64-none
  size    9761545
  sha256  2edec6cfaf20a44b2458567856c1d505e6942d0e43da0e8ba2a36761ebc05be2

cpython-3.14.6-linux-aarch64-none
  size    11788907
  sha256  f0c449f7bc5b5bd740f4776f43bec4418645d5f33da220fa523409b6aa0af208

retained snapshot body sha256
  dbdc0edd20eeca1506066c6ec95078d9ad4fe231b81a13aa1236b480d3faa233

retained snapshot file sha256
  419a9d4303fd6b3d7686400c7a275117ae6fe3421c93c30ff356529fc483b9e3
```

## Accepted matrix

The target result passes 16/16 raw checks and the independent archive verifier passes 31/31. It proves exact snapshot fetch, both actual archive transfers, independent transport observations, content-addressed promotion, repeat cache no-op, corrupt and truncated rejection, peer preservation, candidate cleanup, and protected-state identity.

## Boundary

The accepted cache is evidence retained inside the result archive, not an installation source adopted by uv. No public endpoint, external network, uv invocation, product execution, installation, managed-root mutation, global exposure, origin authentication, recovery, concurrency, or durability claim is made.
