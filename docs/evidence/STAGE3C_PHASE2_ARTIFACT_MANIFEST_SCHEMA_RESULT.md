# Stage 3-C Phase 2 Artifact Manifest Schema Result

> **Status:** PASS — schema-v1 manifest gate closed
> **Target:** Termux on Android arm64
> **Result archive:** `stage3c-phase2-artifact-manifest-schema-input-copy-fixed-results-20260711-213948.tgz`

## Result archive identity

```text
sha256
  a3adc857dbf435208d18d48d45197faaf1281f500ff2b496153f2a0f3dba582a

members
  40

unsafe member names
  0

special archive entries
  0
```

The uploaded TGZ was independently inspected. It contains the complete self-contained accepted ownership input, product lock, generated artifact manifests, manifest index, generator and verifier outputs, workflow status, and source mutation evidence.

## Machine result

```text
manifest generator      42/42 PASS
independent verifier    48/48 PASS
workflow return codes    all 0
failed checks                []
missing outputs              []
parse errors                 {}
```

```text
STAGE3C_PHASE2_ARTIFACT_MANIFEST_GENERATION=PASS
STAGE3C_PHASE2_ARTIFACT_MANIFEST_SCHEMA=PASS
```

## Manifest index

```text
schema version
  1

index kind
  cpython-android-cli-artifact-manifest-index

sha256
  540adfaacf9387e80a258dfa3db8c299ad775d99e771c475a89dfc61de6868c1

product lock sha256
  83f6b1fd3b610c22606f8dd4108a86cf2454e5997d0d0ada4124a209bfb091b7
```

The generated index hash exactly matches the independently recomputed file hash.

## Artifact manifests

```text
artifact             owned   structural   total   bytes    sha256
runtime-base           714            0     714   274636   ce48849c9c88c9296264d6a917c3b55b0433e0d67bdda06579d6f18d701f285a
development-addon      454            2     456   178043   9a01655d63044ab126fd71236ca2cb814221317ee9b6b44fd2417fa5535a8b2a
test-addon            1788            2    1790   738348   47d9f2e24e74b23e34ae6bfa95a0df22ec7cf9505e3e189dc3d6bdf2dc1c8b5f
```

Every index filename, byte size, SHA-256, owned count, structural count, and total entry count matches the retained manifest file.

## Artifact identities

```text
cpython-android-cli-3.14.6-android24-aarch64-runtime-base
cpython-android-cli-3.14.6-android24-aarch64-development-addon
cpython-android-cli-3.14.6-android24-aarch64-test-addon
```

Runtime-base is standalone and has no prerequisite.

Both addons require the accepted runtime-base identity:

```text
Python version
  3.14.6

target host
  aarch64-linux-android

Android API
  24

component manifest
  91088a013722ad35910f049bfc45b2e61607423d833c23038c1d9645497b7b84

runtime-base fingerprint
  9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796
```

## Entry identity

The accepted schema-v1 representation proves:

```text
regular file
  mode + size + SHA-256 + component + ELF marker

directory
  mode only
  no directory st_size
  no content hash
  no mtime

symlink
  mode + symlink target
  no regular-file size or hash
```

All archive and payload paths are safe prefix-relative paths. Exact owned overlap remains zero. Structural rows are restricted to directory entries.

## Canonical JSON

All three manifests and the index are retained as canonical JSON bytes:

```text
UTF-8
sorted object keys
2-space indentation
one trailing newline
```

The independent verifier reproduced complete manifest objects from the accepted TSV ownership rows and verified exact canonical bytes.

## License boundary

```text
archive metadata path
  metadata/licenses/CPython-LICENSE.txt

source payload path
  lib/python3.14/LICENSE.txt

installed payload owner
  runtime-base only
```

All three manifests carry the same license content hash and size. Addons do not claim the installed license payload path.

## Source mutation

Canonical promoted source:

```text
entries before/after
  3155 / 3155

fingerprint before/after
  5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c
```

Runtime-base:

```text
entries before/after
  714 / 714

fingerprint before/after
  9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796
```

```text
source mutation check
  PASS
```

## Preserved incident history

The first target run failed at isolated sibling-module import bootstrap.

The second target run passed import bootstrap but failed because four accepted ownership fingerprint files were omitted from the self-contained input copy.

Both failures remain recorded independently and were not rewritten as PASS evidence:

```text
docs/evidence/STAGE3C_PHASE2_ARTIFACT_MANIFEST_IMPORT_INCIDENT.md
docs/evidence/STAGE3C_PHASE2_ARTIFACT_MANIFEST_INPUT_COPY_INCIDENT.md
```

## Closed claims

This result proves:

```text
accepted ownership evidence deterministically produces three schema-v1 manifests
all complete manifest objects are independently reproduced
canonical JSON bytes are exact
manifest-index hashes and sizes are exact
artifact and addon compatibility identities are exact
license metadata and installed ownership boundaries are exact
canonical and runtime-base products remain unchanged
```

## Claim boundary

This result does not create or validate tar archives. It does not prove archive byte reproducibility, gzip header normalization, PAX header policy, hostile-input extraction safety, installation transactions, upgrade, rollback, or uninstall behavior.

Those begin in Stage 3-C Phase 3 and later.
