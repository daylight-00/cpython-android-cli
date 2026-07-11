# Stage 3-C Phase 2 Artifact Manifest Schema Design

> **Status:** IMPLEMENTED — target evidence pending
> **Input:** accepted archive ownership result

## Objective

Freeze a deterministic machine-readable representation of the three selected artifacts before selecting tar headers, compression, or installation transactions.

The manifest must preserve payload identity while avoiding unstable or non-product filesystem observations.

## Schema identity

```text
schema_version
  1

manifest_kind
  cpython-android-cli-artifact-manifest

index_kind
  cpython-android-cli-artifact-manifest-index
```

Artifact IDs:

```text
cpython-android-cli-3.14.6-android24-aarch64-runtime-base
cpython-android-cli-3.14.6-android24-aarch64-development-addon
cpython-android-cli-3.14.6-android24-aarch64-test-addon
```

## Product identity

Every artifact records:

```text
product kind       upstream-cpython-android-package
implementation     CPython
Python version     3.14.6
source head        c63aec69bd59c55314c06c23f4c22c03de76fe45
platform           android
architecture       aarch64
target host        aarch64-linux-android
Android API        24
NDK                27.3.13750724
multiarch          aarch64-linux-android
SOABI              cpython-314-aarch64-linux-android
```

It also records the tracked product lock SHA-256 and the frozen upstream package archive identity.

## Compatibility identity

Each artifact records:

```text
component manifest
  91088a013722ad35910f049bfc45b2e61607423d833c23038c1d9645497b7b84

canonical product fingerprint
  5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c

runtime-base fingerprint
  9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796

owned paths
  ab2c7374d2a70c7eb48db72dbfd1de86b708167efef151519f25b6a5a65023ea

structural directories
  9481da6ffa6bf0f54a10b631a31b81252580e2323bd1c8a92c6899aff26b78b3

shared namespace
  cc40599da21dbef18e48b940b77143e44479e821b3273946843a89340052956e
```

Runtime-base has no prerequisite.

Both addons require the exact runtime-base artifact ID, Python version, target host, Android API, component-manifest identity, and strict runtime fingerprint.

## Layout identity

```text
archive root
  <artifact-id>/

metadata root
  metadata/

payload root
  payload/

payload paths
  prefix-relative

extraction semantics
  staging-not-installation
```

The manifest does not claim that extracting the archive directly into an installation prefix is safe.

## Ownership identity

```text
owned entry class
  OWNED_PAYLOAD
  registered as installed ownership

non-owning entry class
  STRUCTURAL_PARENT
  never registered as exclusive ownership
```

Directory removal direction:

```text
remove an owned directory only when empty
preserve unowned descendants
```

## Entry identity

Common fields:

```text
archive_path
payload_path
entry_class
type
mode
```

Owned payload entries also carry their component and ELF marker.

Regular file:

```text
size
SHA-256
```

Directory:

```text
no content hash
no size
no mtime
```

Symlink:

```text
symlink target
no regular-file size
no regular-file hash
```

The omission of directory `st_size` and all mtimes is deliberate. They are not stable product identity and archive-header normalization remains a later gate.

## Entry counts

```text
artifact               OWNED_PAYLOAD   STRUCTURAL_PARENT   total
runtime-base                      714                   0     714
development-addon                 454                   2     456
test-addon                       1788                   2    1790
```

Combined:

```text
owned payload rows       2956
structural rows              4
manifest rows             2960
```

## License identity

Every artifact records:

```text
archive metadata path
  metadata/licenses/CPython-LICENSE.txt

source payload path
  lib/python3.14/LICENSE.txt

license content SHA-256 and size
```

Only runtime-base records the installed payload license path. Addons carry archive-envelope license material but do not claim installed ownership.

## Canonical representation

Manifest and index JSON bytes are generated as:

```text
UTF-8
sorted object keys
2-space indentation
one trailing newline
```

A separate `manifest-index.json` records each artifact manifest filename, SHA-256, byte size, owned count, structural count, and total manifest count.

The manifest does not contain its own hash.

## Verification design

Generator:

```text
42 checks
accepted ownership evidence
product lock identity
entry counts
path safety
entry type fields
addon prerequisites
license mapping
index hashes and sizes
```

Independent verifier:

```text
48 checks
re-derives complete manifest objects from TSV ownership rows
checks exact object equality
checks canonical JSON bytes
checks index integrity
checks cross-artifact owned overlap remains zero
checks source and runtime non-mutation
```

## Implementation

```text
experiments/stage3c-artifact-manifest/
  artifact_manifest_contract.py
  generate-artifact-manifests.py
  verify-artifact-manifests.py
  run-artifact-manifest-schema.sh
```

## Claim boundary

A PASS proves deterministic schema-v1 artifact manifests and a verified index can be reproduced from the accepted ownership evidence and tracked product lock.

It does not prove tar archive bytes, compression, archive-header normalization, extraction safety, collision policy, installation transactions, upgrade, rollback, or uninstall behavior.
