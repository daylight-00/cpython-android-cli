# Stage 3-C Phase 3 Final: Reproducible Archive Serialization

> **Status:** FROZEN
> **Primary target:** Termux on Android arm64
> **Python baseline:** CPython 3.14.6

## Phase question

> Can each frozen schema-v1 artifact be serialized twice to byte-identical normalized tar.gz archives and independently verified through fail-closed preflight and safe staging extraction?

## Frozen input

```text
manifest index
  540adfaacf9387e80a258dfa3db8c299ad775d99e771c475a89dfc61de6868c1

runtime-base manifest
  ce48849c9c88c9296264d6a917c3b55b0433e0d67bdda06579d6f18d701f285a

development-addon manifest
  9a01655d63044ab126fd71236ca2cb814221317ee9b6b44fd2417fa5535a8b2a

test-addon manifest
  47d9f2e24e74b23e34ae6bfa95a0df22ec7cf9505e3e189dc3d6bdf2dc1c8b5f

product lock
  83f6b1fd3b610c22606f8dd4108a86cf2454e5997d0d0ada4124a209bfb091b7
```

## Frozen archive identities

```text
artifact               members      bytes        sha256
runtime-base                722   13,684,443   2ba7c309b1700926dc423eb4305a9eba1a53c023a11617e490b151be71e49743
development-addon           464    1,037,544   f77ea24c92fdd982cd32e172b2d38134f1d785b1f106d1bfe36a9bffa9cc8eea
test-addon                 1798    7,135,813   02a1fad1af5528a4e910f0eb3370f4a2696da4f78067586e8b62f2a10fb4c9b1
```

Each identity is exact for build A, build B, and the retained result archive.

## Frozen serialization contract

```text
tar format                 POSIX pax
gzip level                 9
gzip filename              empty
gzip mtime                 0
tar member mtime           0
uid / gid                  0 / 0
uname / gname              empty / empty
envelope directory mode    0755
metadata file mode         0644
payload mode               schema-v1 exact mode
hardlinks                  forbidden
special entries            forbidden
PAX headers                path/linkpath only when required
```

Observed gzip header:

```text
1f8b08000000000002ff
```

Observed PAX key set:

```text
path
```

## Frozen archive envelope

```text
<artifact-id>/
  metadata/
    manifest.json
    manifest-index.json
    product-lock.json
    licenses/CPython-LICENSE.txt
  payload/
    <schema-v1 archive paths>
```

Extraction is staging, not installation.

## Frozen source mapping

```text
runtime-base OWNED_PAYLOAD
  isolated validated runtime-base prefix

development-addon OWNED_PAYLOAD
  canonical promoted prefix selected by manifest

test-addon OWNED_PAYLOAD
  canonical promoted prefix selected by manifest

STRUCTURAL_PARENT
  emitted as a directory member
  remains non-owning
```

## Frozen member ordering

```text
1  artifact root
2  metadata directory
3  metadata/licenses directory
4  payload directory
5  metadata/manifest.json
6  metadata/manifest-index.json
7  metadata/product-lock.json
8  metadata/licenses/CPython-LICENSE.txt
9+ schema-v1 entries in exact manifest order
```

## Frozen extraction preflight

No archive may enter staging extraction unless it proves:

```text
exact expected member order and set
unique safe prefix-relative names
allowed directory/regular/symlink types only
hardlinks absent
exact expected symlink set
all symlink targets prefix-contained
no member below a symlink parent
```

## Validation ledger

```text
reproducible archive builder     31/31 PASS
archive extraction preflight     28/28 PASS
independent archive verifier     76/76 PASS
safe staging extraction            3/3 PASS
source mutation controls               PASS
```

## Frozen evidence

```text
docs/evidence/STAGE3C_PHASE3_REPRODUCIBLE_ARCHIVE_DESIGN.md
docs/evidence/STAGE3C_PHASE3_REPRODUCIBLE_ARCHIVE_RESULT.md
```

Accepted result bundle:

```text
stage3c-phase3-reproducible-archives-results-20260711-220238.tgz
sha256
  51a334a8bbaa16e89a1f3aeb10373cb72a862d3063e25ffb6844f15ce731b946
```

## Non-reopening rule

Later installation phases must consume the exact frozen archive identities and must not:

```text
change archive member order
change gzip or tar normalization
change metadata envelope bytes
silently accept archive hash drift
extract before exact preflight passes
register STRUCTURAL_PARENT as exclusive ownership
interpret staging extraction as installation
```

Any intentional archive-format or byte-identity change reopens Phase 3 and requires complete builder, preflight, verifier, extraction, and source-mutation validation.

## Deferred contract

Phase 3 does not freeze:

```text
installation state layout
installed ownership registry
collision policy
same-version reinstall behavior
upgrade and downgrade semantics
mutation journal
rollback and crash recovery
concurrent-operation locking
uninstall behavior
```

These begin in Stage 3-C Phase 4.

## Final marker

```text
STAGE3C_PHASE3=FROZEN
```
