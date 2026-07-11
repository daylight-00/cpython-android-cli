# Stage 3-C Phase 2 Archive Ownership Model Result

> **Status:** PASS — exact ownership and shared namespace gate closed
> **Target:** Termux on Android arm64
> **Result archive:** `stage3c-phase2-archive-ownership-model-results-20260711-203019.tgz`

## Result archive identity

```text
sha256
  e10c3a5086ba4317e7777044cf522c14eb8afaa5cec1aa95a6b124fc8762e84f
```

The uploaded TGZ was independently checked for unsafe member names and special entries, extracted, and inspected.

## Machine result

```text
ownership analyzer          64/64 PASS
structural verifier         74/74 PASS
safety verifier               9/9 PASS
workflow return codes        all 0
failed checks                    []
missing outputs                  []
parse errors                     {}
```

## Exact artifact ownership

```text
artifact               owned entries   regular   directories   symlinks   ELF   regular bytes
runtime-base                      714       654            57          3    81      38,759,749
development-addon                 454       443             9          2     0       4,973,375
test-addon                       1788      1643           145          0     0      33,476,790
```

```text
selected exact owned entries   2956
unsupported GUI excluded        199
canonical total                3155
exact owned overlap               0
```

## Shared structural namespace

There are exactly two shared namespace directories:

```text
lib
lib/python3.14
```

Both are exactly owned by `runtime-base` and structurally consumed by both addons.

```text
structural rows
  development-addon   2
  test-addon          2
  total               4
```

`STRUCTURAL_PARENT` is explicitly non-owning. It permits archive representation and overlay composition but does not grant recursive installed ownership.

## Manifest identities

```text
owned paths
  ab2c7374d2a70c7eb48db72dbfd1de86b708167efef151519f25b6a5a65023ea

structural directories
  9481da6ffa6bf0f54a10b631a31b81252580e2323bd1c8a92c6899aff26b78b3

shared namespace
  cc40599da21dbef18e48b940b77143e44479e821b3273946843a89340052956e
```

## Symlink safety

All five selected symlinks are relative, prefix-contained, point to an existing selected path, and remain within the same artifact ownership domain.

```text
runtime-base
  bin/python -> python3
  bin/python3 -> python3.14
  lib/libsqlite3.so.0 -> libsqlite3_python.so

development-addon
  lib/pkgconfig/python3-embed.pc -> python-3.14-embed.pc
  lib/pkgconfig/python3.pc -> python-3.14.pc
```

## Artifact composition contract

```text
runtime-base
  standalone runtime
  structural parents required: 0

development-addon
  overlay requiring matching runtime-base
  structural parents required: 2

test-addon
  overlay requiring matching runtime-base
  structural parents required: 2
```

Addon prerequisites are pinned to:

```text
component manifest
  91088a013722ad35910f049bfc45b2e61607423d833c23038c1d9645497b7b84

runtime-base fingerprint
  9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796
```

## License boundary

```text
installed payload owner
  runtime-base

installed payload path
  lib/python3.14/LICENSE.txt

archive envelope
  license material required for every distributable artifact outside payload/
```

## Source mutation

```text
canonical entries
  3155 / 3155
canonical fingerprint
  5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c

runtime-base entries
  714 / 714
runtime-base fingerprint
  9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796

mutation result
  PASS
```

## Closed claims

This result proves:

```text
three selected artifacts have disjoint exact payload ownership
all selected and excluded canonical paths are accounted for
shared parent directories are explicit structural namespace
all 81 ELF rows remain runtime-base-owned
all five selected symlinks satisfy the candidate safety policy
runtime-base is the only standalone artifact
both addons require the accepted runtime-base identity
installed license ownership is unique
canonical and runtime-base products remain unchanged
```

## Claim boundary

This result does not create archive bytes and does not prove archive reproducibility, hostile-input extraction safety, installation collision handling, upgrade, rollback, or uninstall transactions.

The next Phase 2 gate converts the accepted ownership rows into deterministic per-artifact schema-v1 manifests and an independently verified manifest index.
