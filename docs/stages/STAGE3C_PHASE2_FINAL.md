# Stage 3-C Phase 2 Final: Archive Ownership and Artifact Manifest Model

> **Status:** FROZEN
> **Primary target:** Termux on Android arm64
> **Python baseline:** CPython 3.14.6

## Phase question

> How are the frozen runtime, development, and test components represented as disjoint exact payload owners with explicit shared structural namespace and deterministic schema-v1 artifact manifests?

## Frozen input

```text
canonical promoted source
  entries
    3155
  fingerprint
    5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c

runtime-base
  entries
    714
  strict fingerprint
    9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796

component manifest
  91088a013722ad35910f049bfc45b2e61607423d833c23038c1d9645497b7b84
```

## Frozen ownership partition

```text
artifact               owned entries   regular   directories   symlinks   ELF
runtime-base                      714       654            57          3    81
development-addon                 454       443             9          2     0
test-addon                       1788      1643           145          0     0
```

```text
selected exact owned entries   2956
unsupported GUI excluded        199
canonical total                3155
exact owned overlap               0
```

Ownership manifests:

```text
owned paths
  ab2c7374d2a70c7eb48db72dbfd1de86b708167efef151519f25b6a5a65023ea

structural directories
  9481da6ffa6bf0f54a10b631a31b81252580e2323bd1c8a92c6899aff26b78b3

shared namespace
  cc40599da21dbef18e48b940b77143e44479e821b3273946843a89340052956e
```

## Frozen shared namespace

Exactly two directories are shared structural namespace:

```text
lib
lib/python3.14
```

Both are exactly owned by runtime-base and structurally consumed by development-addon and test-addon.

```text
runtime-base structural rows          0
development-addon structural rows     2
test-addon structural rows            2
```

`STRUCTURAL_PARENT` is non-owning and never grants recursive installed ownership.

## Frozen ownership semantics

```text
exclusive ownership unit
  exact OWNED_PAYLOAD path

standalone artifact
  runtime-base only

overlay artifacts
  development-addon
  test-addon

addon prerequisite
  exact matching runtime-base artifact identity

owned-directory removal direction
  remove only when empty

unowned descendant policy
  preserve
```

## Frozen symlink policy

All five selected symlinks are:

```text
relative
prefix-contained
targeting an existing selected path
targeting a path owned by the same artifact
```

## Frozen license boundary

```text
installed payload owner
  runtime-base

installed payload path
  lib/python3.14/LICENSE.txt

archive metadata path
  metadata/licenses/CPython-LICENSE.txt

archive rule
  every distributable artifact carries the same license material outside payload/
```

## Frozen artifact identities

```text
cpython-android-cli-3.14.6-android24-aarch64-runtime-base
cpython-android-cli-3.14.6-android24-aarch64-development-addon
cpython-android-cli-3.14.6-android24-aarch64-test-addon
```

Product identity:

```text
product kind       upstream-cpython-android-package
implementation     CPython
Python version     3.14.6
source head        c63aec69bd59c55314c06c23f4c22c03de76fe45
target host        aarch64-linux-android
Android API        24
NDK                27.3.13750724
architecture       aarch64
multiarch          aarch64-linux-android
SOABI              cpython-314-aarch64-linux-android
```

## Frozen schema-v1 entry model

```text
artifact               OWNED_PAYLOAD   STRUCTURAL_PARENT   manifest total
runtime-base                      714                   0              714
development-addon                 454                   2              456
test-addon                       1788                   2             1790
```

Common fields:

```text
archive_path
payload_path
entry_class
type
mode
```

Regular-file identity:

```text
size
SHA-256
component
ELF marker
```

Directory identity:

```text
mode
no st_size
no content hash
no mtime
```

Symlink identity:

```text
symlink target
no regular-file size or hash
```

## Frozen canonical JSON representation

```text
UTF-8
sorted object keys
2-space indentation
one trailing newline
```

Manifest index:

```text
sha256
  540adfaacf9387e80a258dfa3db8c299ad775d99e771c475a89dfc61de6868c1

product lock sha256
  83f6b1fd3b610c22606f8dd4108a86cf2454e5997d0d0ada4124a209bfb091b7
```

Artifact manifests:

```text
runtime-base
  bytes
    274636
  sha256
    ce48849c9c88c9296264d6a917c3b55b0433e0d67bdda06579d6f18d701f285a

development-addon
  bytes
    178043
  sha256
    9a01655d63044ab126fd71236ca2cb814221317ee9b6b44fd2417fa5535a8b2a

test-addon
  bytes
    738348
  sha256
    47d9f2e24e74b23e34ae6bfa95a0df22ec7cf9505e3e189dc3d6bdf2dc1c8b5f
```

## Validation ledger

```text
ownership analyzer                 64/64 PASS
structural verifier                74/74 PASS
safety verifier                      9/9 PASS
manifest generator                 42/42 PASS
independent manifest verifier      48/48 PASS
source mutation controls                 PASS
```

Preserved incidents:

```text
first manifest run
  isolated sibling import bootstrap failure

second manifest run
  accepted ownership fingerprint input-copy failure

final corrected manifest run
  PASS
```

## Frozen evidence

```text
docs/evidence/STAGE3C_PHASE2_ARCHIVE_OWNERSHIP_DESIGN.md
docs/evidence/STAGE3C_PHASE2_ARCHIVE_OWNERSHIP_RESULT.md
docs/evidence/STAGE3C_PHASE2_ARTIFACT_MANIFEST_SCHEMA_DESIGN.md
docs/evidence/STAGE3C_PHASE2_ARTIFACT_MANIFEST_IMPORT_INCIDENT.md
docs/evidence/STAGE3C_PHASE2_ARTIFACT_MANIFEST_INPUT_COPY_INCIDENT.md
docs/evidence/STAGE3C_PHASE2_ARTIFACT_MANIFEST_SCHEMA_RESULT.md
```

## Non-reopening rule

Later archive and installer phases must consume these exact identities. They must not:

```text
change exact owned-path assignment
register STRUCTURAL_PARENT as exclusive ownership
change addon prerequisites merely to simplify archive creation
duplicate installed license ownership into addons
include directory st_size or source mtimes as product identity
weaken regular-file SHA-256 checks
change canonical JSON serialization without reopening Phase 2
change artifact IDs or compatibility identity
```

Any intentional change reopens Phase 2 and requires the complete ownership and manifest validation chain.

## Deferred contract

Phase 2 does not freeze:

```text
tar format and extended-header policy
gzip or other compression format
archive member ordering
normalized timestamp source
uid/gid and owner-name normalization
archive byte reproducibility
archive extraction implementation
installation collision and transaction behavior
upgrade, rollback, or uninstall
```

These begin in Stage 3-C Phase 3 and later.

## Final marker

```text
STAGE3C_PHASE2=FROZEN
```
