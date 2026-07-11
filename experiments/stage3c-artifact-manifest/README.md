# Stage 3-C Phase 2: Artifact Manifest Schema

> **Status:** ACTIVE — target evidence pending
> **Input:** accepted archive ownership result

## Question

```text
Can the frozen ownership model be represented as deterministic, independently
reproducible schema-v1 manifests before any archive container is created?
```

## Run

```sh
bash experiments/stage3c-artifact-manifest/run-artifact-manifest-schema.sh
```

## Accepted ownership input

```text
ownership analyzer          64/64 PASS
structural verifier         74/74 PASS
safety verifier               9/9 PASS
exact owned overlap              0
shared namespace directories     2
structural rows                   4
```

```text
owned paths
  ab2c7374d2a70c7eb48db72dbfd1de86b708167efef151519f25b6a5a65023ea

structural directories
  9481da6ffa6bf0f54a10b631a31b81252580e2323bd1c8a92c6899aff26b78b3

shared namespace
  cc40599da21dbef18e48b940b77143e44479e821b3273946843a89340052956e
```

## Product identity

```text
product kind       upstream-cpython-android-package
Python             CPython 3.14.6
target host        aarch64-linux-android
Android API        24
NDK                27.3.13750724
SOABI              cpython-314-aarch64-linux-android
source head        c63aec69bd59c55314c06c23f4c22c03de76fe45
```

The tracked product lock is copied into the result and its exact file SHA-256 is embedded in every artifact manifest.

## Schema-v1 artifact identities

```text
cpython-android-cli-3.14.6-android24-aarch64-runtime-base
cpython-android-cli-3.14.6-android24-aarch64-development-addon
cpython-android-cli-3.14.6-android24-aarch64-test-addon
```

## Manifest entry counts

```text
artifact               owned payload   structural parents   manifest entries
runtime-base                      714                    0                714
development-addon                 454                    2                456
test-addon                       1788                    2               1790
```

The four structural rows are non-owning representations of:

```text
lib
lib/python3.14
```

for each addon.

## Entry identity rules

Every entry contains:

```text
archive_path
payload_path
entry_class
entry type
mode
```

Type-specific fields:

```text
regular
  size
  SHA-256
  ELF marker
  component

directory
  no size
  no content hash
  no mtime

symlink
  symlink target
  no regular-file size or hash
```

Directory `st_size` and all entry mtimes are intentionally excluded from schema-v1 product identity.

## Envelope contract encoded by the manifest

```text
<artifact-id>/
  metadata/
  payload/
```

```text
payload paths              prefix-relative
extraction semantics       staging, not installation
installed ownership unit   exact OWNED_PAYLOAD path
STRUCTURAL_PARENT           non-owning
```

## Compatibility contract

Runtime-base has no prerequisite.

Development and test addons require the exact accepted:

```text
runtime-base artifact ID
Python version
Android API
target host
component manifest
runtime-base strict fingerprint
```

## License contract

```text
archive metadata path
  metadata/licenses/CPython-LICENSE.txt

source payload path
  lib/python3.14/LICENSE.txt

installed payload owner
  runtime-base only
```

Every artifact manifest carries the same license content hash and size. Addons do not claim the installed license path.

## Outputs

```text
results/termux/stage3c-phase2-artifact-manifest-schema/
  input/
    ownership/
    product-lock.json
    ownership-model.json
    ownership-verification.json
    ownership-safety-verification.json
    phase1-final-verification.json
  manifests/
    runtime-base.manifest.json
    development-addon.manifest.json
    test-addon.manifest.json
  manifest-index.json
  generation.json
  verification.json
  workflow-status.json
  canonical-before.json
  canonical-after.json
  runtime-before.json
  runtime-after.json
  source-mutation-check.txt
```

## Verification

```text
manifest generator     42 checks
independent verifier   48 checks
```

The verifier independently re-derives every artifact object and entry list from the accepted TSV ownership rows. It also verifies canonical JSON bytes and every index hash and size.

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

## Upload

```sh
RESULTS="$PWD/results/termux/stage3c-phase2-artifact-manifest-schema"
ARCHIVE="$HOME/Downloads/stage3c-phase2-artifact-manifest-schema-results-$(date +%Y%m%d-%H%M%S).tgz"

tar czf "$ARCHIVE" "$RESULTS"
printf 'upload: %s\n' "$ARCHIVE"
```

## Claim boundary

A PASS freezes deterministic manifest semantics and canonical JSON representation. It does not prove tar layout, compression, archive-header normalization, hostile extraction safety, or installation transaction behavior.
