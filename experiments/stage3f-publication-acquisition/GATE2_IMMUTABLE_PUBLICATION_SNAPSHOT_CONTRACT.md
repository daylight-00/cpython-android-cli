# Stage 3-F Gate 2: Immutable Publication Snapshot Contract

> **Status:** CONTRACT FROZEN — local behavior verified
> **Class:** L — repository-local deterministic behavior
> **Selected next gate:** Gate 3 loopback transport and acquisition implementation

## Input authority

```text
Stage 3-F Gate 1 commit
  39e5c6d56a45495a4f23b73b6fa0704ba28fbc74

Stage 3-F Gate 1 tree
  7a0c476e60280c23dd8edd2627b25b42e3fa1429

Gate 1 result archive
  eb6f1356fa09473bc4564e0e3a1ae1d7940ecac287d69baa2abf4bd8c494a438

Stage 3-E dual-version evidence archive
  3fe68808e2a770f93a6cfe2feba2517b9ac7a42be04c22349fd1c6f375b6cac2
```

Gate 2 uses the exact runtime-only artifact identities preserved in the accepted Stage 3-E evidence. It does not create, transform, or repackage product bytes.

## Frozen exact rows

```text
cpython-3.14.5-linux-aarch64-none
  size    9761522
  sha256  18832bb7982a679fcee067e2d33e106dac84307687b63803be105714596d422f
  source  research/derived-145.json

cpython-3.14.6-linux-aarch64-none
  size    11789074
  sha256  9575edef24d84b2fce32c55093ab01cb8b2b1a41b521d2011653fae87b5bcb64
  source  research/derived-146.json
```

Each source member is itself bound by the Stage 3-E result index. Locators remain non-authoritative metadata.

## Canonical document

The tracked document has exactly three top-level fields:

```text
schema_version
snapshot
snapshot_sha256
```

Canonical bytes are UTF-8 JSON with:

```text
sorted object keys
no insignificant whitespace
no ASCII escaping requirement for Unicode
one trailing newline
```

`snapshot_sha256` is SHA-256 over the canonical bytes of the `snapshot` object, including its trailing newline. It is not the SHA-256 of the complete envelope and is not an artifact digest.

The snapshot body contains exactly:

```text
format
frozen_inputs
rows
```

Rows are ordered lexically by exact key. The accepted snapshot is a complete two-row set; missing, duplicate, reordered, or redefined rows fail verification.

## Row contract

Every row contains exactly:

```text
key
version
platform
artifact
locators
provenance
```

`artifact` contains exact `size` and `sha256`. `locators` may identify candidate locations but may not carry or replace identity fields. `provenance` binds the row to the accepted Stage 3-E authority, evidence archive, exact member, and member digest.

## Candidate-observation decision

Gate 2 models the decision boundary after transport has independently produced an observed size and SHA-256:

```text
valid canonical snapshot
exact snapshot binding
exact key present
observed size == expected size
observed SHA-256 == expected SHA-256
  -> promotable to a later verified cache operation
```

The Gate 2 model never writes a cache object and always reports installation as not permitted. Actual file hashing, transport, cache promotion, and installation remain later gates.

## Fixture census

Success:

```text
tracked snapshot verifies
tracked bytes are canonical
tracked snapshot equals generated snapshot
two repeated generations are byte-identical
both exact candidate observations are promotable
```

Expected negative:

```text
duplicate key
exact-key redefinition
snapshot digest mismatch
missing size
locator-only identity
candidate size mismatch
candidate SHA-256 mismatch
candidate snapshot-binding mismatch
```

Incomplete:

```text
missing row
missing artifact SHA-256
missing provenance member digest
missing snapshot digest
```

## Frozen result

```text
snapshot body SHA-256  a00027a81956ef175bf537eff3a92286e26c1120fa536d0a8ad6a096a1760f8c
snapshot file SHA-256  c942b9863e33c2edf7d628780bfeef0957b427fb12259ba49e708cb4858c52bc
snapshot file size    2328
rows                  2
verification          18/18 PASS
```

## Non-reopening boundary

Gate 2 opens no socket, invokes no uv command, executes no CPython product, writes no cache, and mutates no managed root. It proves no endpoint availability, DNS/TLS/origin authenticity, signature policy, redirect or mirror policy, resumable transfer, automatic acquisition, installation behavior, recovery, concurrency, durability, third-product compatibility, or upstream uv Android support.
