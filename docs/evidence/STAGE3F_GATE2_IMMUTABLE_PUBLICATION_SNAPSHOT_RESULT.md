# Stage 3-F Gate 2 Immutable Publication Snapshot Result

> **Status:** FROZEN — local deterministic behavior verified
> **Class:** L — repository-local

## Result

Gate 2 freezes one canonical two-row publication snapshot for the exact Stage 3-E runtime-only products. The artifact identities are traced to the accepted Stage 3-E dual-version evidence and are not derived from locators.

```text
3.14.5 size / SHA-256
  9761522
  18832bb7982a679fcee067e2d33e106dac84307687b63803be105714596d422f

3.14.6 size / SHA-256
  11789074
  9575edef24d84b2fce32c55093ab01cb8b2b1a41b521d2011653fae87b5bcb64

snapshot body SHA-256
  a00027a81956ef175bf537eff3a92286e26c1120fa536d0a8ad6a096a1760f8c

canonical file SHA-256 / size
  c942b9863e33c2edf7d628780bfeef0957b427fb12259ba49e708cb4858c52bc
  2328
```

## Verification

```text
success and canonical checks  6/6
expected-negative fixtures    8/8
incomplete fixtures           4/4
total                         18/18 PASS
```

Repeated generation is byte-identical. Duplicate or redefined keys, digest mismatch, missing identity, locator-only identity, and mismatched candidate observations fail closed.

## Boundary

This result opens no socket, invokes no uv command, executes no target product, writes no verified cache, and changes no installation state. Gate 3 is the next boundary for a loopback transport/acquisition implementation.
