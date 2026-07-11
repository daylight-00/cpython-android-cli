# Stage 3-C Phase 2 Scope: Archive Ownership and Manifest Model

> **Status:** FROZEN
> **Input:** frozen Stage 3-C Phase 1 component and runtime identities
> **Primary target:** Termux on Android arm64

## Phase question

> How are runtime-base, development-addon, and test-addon represented as disjoint exact payload owners with explicit shared structural namespace and deterministic schema-v1 manifests?

## Frozen result

```text
runtime-base exact owned entries       714
development-addon exact owned entries  454
test-addon exact owned entries        1788
selected total                        2956
unsupported GUI excluded               199
exact owned overlap                      0
```

Shared namespace:

```text
lib
lib/python3.14
```

Both directories are exactly owned by runtime-base and structurally consumed by both addons.

Ownership manifests:

```text
owned paths
  ab2c7374d2a70c7eb48db72dbfd1de86b708167efef151519f25b6a5a65023ea

structural directories
  9481da6ffa6bf0f54a10b631a31b81252580e2323bd1c8a92c6899aff26b78b3

shared namespace
  cc40599da21dbef18e48b940b77143e44479e821b3273946843a89340052956e
```

Schema-v1 manifest identities:

```text
manifest index
  540adfaacf9387e80a258dfa3db8c299ad775d99e771c475a89dfc61de6868c1

runtime-base
  714 entries
  ce48849c9c88c9296264d6a917c3b55b0433e0d67bdda06579d6f18d701f285a

development-addon
  456 entries
  9a01655d63044ab126fd71236ca2cb814221317ee9b6b44fd2417fa5535a8b2a

test-addon
  1790 entries
  47d9f2e24e74b23e34ae6bfa95a0df22ec7cf9505e3e189dc3d6bdf2dc1c8b5f
```

## Validation ledger

```text
ownership analyzer              64/64 PASS
structural verifier             74/74 PASS
safety verifier                   9/9 PASS
manifest generator              42/42 PASS
independent manifest verifier   48/48 PASS
source mutation controls              PASS
```

## Frozen contract

```text
ownership unit
  exact OWNED_PAYLOAD path

STRUCTURAL_PARENT
  non-owning directory representation

runtime-base
  only standalone artifact

addons
  require exact matching runtime-base identity

license installed owner
  runtime-base only

canonical JSON
  UTF-8, sorted keys, two-space indentation, one trailing newline
```

Directory `st_size` and source mtimes are excluded from schema-v1 product identity.

## Authoritative final record

```text
docs/stages/STAGE3C_PHASE2_FINAL.md
docs/evidence/STAGE3C_PHASE2_ARCHIVE_OWNERSHIP_RESULT.md
docs/evidence/STAGE3C_PHASE2_ARTIFACT_MANIFEST_SCHEMA_RESULT.md
```

## Non-reopening rule

Archive and installer phases must consume the exact frozen ownership and manifest identities. A change to path ownership, shared namespace semantics, artifact identity, entry identity, addon prerequisite, license ownership, or canonical JSON representation reopens Phase 2.

## Deferred to Phase 3 and later

```text
tar and extended-header format
gzip/compression parameters
archive member ordering
mtime and owner normalization
archive byte reproducibility
safe extraction implementation
installation transactions and lifecycle
```

Next scope:

```text
docs/stages/STAGE3C_PHASE3_SCOPE.md
```

## Final marker

```text
STAGE3C_PHASE2=FROZEN
```
