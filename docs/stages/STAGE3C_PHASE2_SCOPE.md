# Stage 3-C Phase 2 Scope: Archive Ownership and Manifest Model

> **Status:** ACTIVE — ownership PASS, artifact manifest schema pending
> **Input:** frozen Stage 3-C Phase 1 component and runtime identities
> **Primary target:** Termux on Android arm64

## Phase question

> How should the frozen runtime, development, and test components be represented as independently inspectable artifacts and safely overlaid into one relocatable installation prefix without confusing payload ownership, shared namespace, and archive representation?

## Frozen input

```text
runtime-base
  714 exact owned entries
  fingerprint
    9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796

development-addon
  454 exact owned entries

test-addon
  1788 exact owned entries

selected total
  2956 exact owned entries

unsupported-gui-source
  199 excluded entries

component manifest
  91088a013722ad35910f049bfc45b2e61607423d833c23038c1d9645497b7b84
```

Authoritative Phase 1 boundary:

```text
docs/stages/STAGE3C_PHASE1_FINAL.md
docs/evidence/STAGE3C_PHASE1_RUNTIME_BASE_FINAL_RESULT.md
```

## Gate 1: exact archive ownership — PASS

Target result:

```text
ownership analyzer          64/64 PASS
structural verifier         74/74 PASS
safety verifier               9/9 PASS
workflow return codes        all 0
```

Accepted result archive:

```text
stage3c-phase2-archive-ownership-model-results-20260711-203019.tgz
sha256
  e10c3a5086ba4317e7777044cf522c14eb8afaa5cec1aa95a6b124fc8762e84f
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE2_ARCHIVE_OWNERSHIP_DESIGN.md
docs/evidence/STAGE3C_PHASE2_ARCHIVE_OWNERSHIP_RESULT.md
```

### Frozen ownership identities

```text
owned paths
  ab2c7374d2a70c7eb48db72dbfd1de86b708167efef151519f25b6a5a65023ea

structural directories
  9481da6ffa6bf0f54a10b631a31b81252580e2323bd1c8a92c6899aff26b78b3

shared namespace
  cc40599da21dbef18e48b940b77143e44479e821b3273946843a89340052956e
```

### Exact ownership result

```text
artifact               entries   regular   directories   symlinks   ELF
runtime-base                714       654            57          3    81
development-addon           454       443             9          2     0
test-addon                 1788      1643           145          0     0
```

```text
exact owned overlap               0
selected and excluded coverage    3155 / 3155
```

### Shared namespace result

There are exactly two shared namespace directories:

```text
lib
lib/python3.14
```

Both are exactly owned by runtime-base and structurally consumed by both addons.

```text
development-addon structural rows   2
test-addon structural rows          2
total structural rows               4
```

`STRUCTURAL_PARENT` is non-owning and must never be registered as recursive installed ownership.

### Frozen symlink policy

All five selected symlinks are:

```text
relative
prefix-contained
targeting an existing selected path
targeting a path owned by the same artifact
```

### Frozen ownership semantics

```text
exclusive ownership unit
  exact OWNED_PAYLOAD path

structural namespace
  explicit and non-owning

runtime-base
  only standalone artifact

development-addon and test-addon
  overlays requiring exact matching runtime-base identity

directory removal direction
  remove an owned directory only when empty
  preserve unowned descendants
```

### Frozen license boundary

```text
installed payload owner
  runtime-base

installed payload path
  lib/python3.14/LICENSE.txt

archive envelope
  every distributable artifact carries license material outside payload/
```

## Active Gate 2: schema-v1 artifact manifests

Question:

> Can the accepted ownership rows and product lock deterministically produce three canonical JSON artifact manifests and a verified manifest index without creating archive bytes?

Run:

```sh
bash experiments/stage3c-artifact-manifest/run-artifact-manifest-schema.sh
```

Implementation:

```text
experiments/stage3c-artifact-manifest/
  artifact_manifest_contract.py
  generate-artifact-manifests.py
  verify-artifact-manifests.py
  run-artifact-manifest-schema.sh
```

Design evidence:

```text
docs/evidence/STAGE3C_PHASE2_ARTIFACT_MANIFEST_SCHEMA_DESIGN.md
```

### Product identity

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

### Artifact identities

```text
cpython-android-cli-3.14.6-android24-aarch64-runtime-base
cpython-android-cli-3.14.6-android24-aarch64-development-addon
cpython-android-cli-3.14.6-android24-aarch64-test-addon
```

### Manifest entry model

```text
artifact               OWNED_PAYLOAD   STRUCTURAL_PARENT   total
runtime-base                      714                   0     714
development-addon                 454                   2     456
test-addon                       1788                   2    1790
```

Common entry identity:

```text
archive path
prefix-relative payload path
entry class
entry type
mode
```

Type-specific identity:

```text
regular
  size + SHA-256 + component + ELF marker

directory
  no content hash
  no size
  no mtime

symlink
  symlink target
  no regular-file size or hash
```

Directory `st_size` and all mtimes are excluded from schema-v1 product identity.

### Manifest envelope model

```text
<artifact-id>/
  metadata/
  payload/
```

```text
payload paths          prefix-relative
extraction semantics   staging-not-installation
```

This gate describes archive representation but does not serialize tar entries.

### Compatibility model

Runtime-base has no prerequisite.

Both addons require:

```text
runtime-base artifact ID
Python version
target host
Android API
component manifest
runtime-base strict fingerprint
```

### Canonical JSON model

```text
UTF-8
sorted object keys
2-space indentation
one trailing newline
```

`manifest-index.json` records each manifest filename, SHA-256, size, owned count, structural count, and total manifest count.

### Verification gates

```text
manifest generator      42 checks
independent verifier    48 checks
```

The verifier independently re-derives complete manifest objects and entry lists from the accepted TSV ownership rows.

Expected markers:

```text
STAGE3C_PHASE2_ARTIFACT_MANIFEST_GENERATION=PASS
ARTIFACT_MANIFEST_ACCEPTED_INPUTS=PASS
ARTIFACT_MANIFEST_GENERATION=42/42 PASS
ARTIFACT_MANIFEST_VERIFICATION=48/48 PASS
ARTIFACT_MANIFEST_CANONICAL_JSON=PASS
ARTIFACT_MANIFEST_INDEX_INTEGRITY=PASS
ARTIFACT_MANIFEST_SOURCE_MUTATION_CHECK=PASS
STAGE3C_PHASE2_ARTIFACT_MANIFEST_SCHEMA=PASS
```

### Expected outputs

```text
results/termux/stage3c-phase2-artifact-manifest-schema/
  input/
  manifests/
    runtime-base.manifest.json
    development-addon.manifest.json
    test-addon.manifest.json
  manifest-index.json
  generation.json
  verification.json
  workflow-status.json
  source-mutation-check.txt
```

### Result archive convention

```sh
RESULTS="$PWD/results/termux/stage3c-phase2-artifact-manifest-schema"
ARCHIVE="$HOME/Downloads/stage3c-phase2-artifact-manifest-schema-results-$(date +%Y%m%d-%H%M%S).tgz"

tar czf "$ARCHIVE" "$RESULTS"
printf 'upload: %s\n' "$ARCHIVE"
```

## Acceptance conditions

```text
[x] accepted Phase 1 evidence chain verified
[x] exact owned path sets derived for three artifacts
[x] exact owned overlap = 0
[x] structural parent sets derived
[x] runtime-owned shared namespace identified
[x] addon prerequisites selected
[x] installed ownership unit selected
[x] directory uninstall direction selected
[x] archive-envelope versus installed-payload license rule selected
[x] candidate envelope root and payload root selected
[x] ownership model independently verified
[x] ownership source mutation control passes
[x] ownership claim boundary recorded
[ ] schema-v1 manifests generated for all three artifacts
[ ] artifact product and compatibility identities exact
[ ] type-specific entry identity exact
[ ] canonical JSON representation passes
[ ] manifest index hashes and sizes pass
[ ] complete manifest objects independently reproduced
[ ] canonical and runtime-base source mutation controls pass
[ ] manifest schema result and claim boundary recorded
```

## Non-goals

```text
creating final tar archives
choosing gzip, zstd, or another compression format
normalizing archive timestamps, uid/gid, or owner names
claiming byte-identical archive reproducibility
extracting hostile archives
implementing installation transactions
implementing upgrade, rollback, or uninstall
adding unsupported GUI source
changing the frozen component partition
```

## Claim boundary

The ownership PASS proves disjoint exact payload ownership and explicit shared structural namespace.

A manifest-schema PASS will additionally prove deterministic canonical JSON artifact descriptions and a verified manifest index.

Neither gate proves archive serialization, reproducible archive bytes, hostile-input extraction safety, or transactionally safe installation.
