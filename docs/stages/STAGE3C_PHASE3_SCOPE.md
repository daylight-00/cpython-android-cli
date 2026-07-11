# Stage 3-C Phase 3 Scope: Reproducible Archive Serialization

> **Status:** ACTIVE — normalized tar.gz prototype
> **Input:** frozen Stage 3-C Phase 2 ownership and schema-v1 artifact manifests
> **Primary target:** Termux on Android arm64

## Phase question

> Can each frozen artifact manifest be serialized into a byte-identical, independently inspectable tar.gz archive whose members, metadata, payload bytes, symlinks, and normalized headers exactly match the accepted schema?

## Frozen input

```text
manifest index sha256
  540adfaacf9387e80a258dfa3db8c299ad775d99e771c475a89dfc61de6868c1

runtime-base manifest
  ce48849c9c88c9296264d6a917c3b55b0433e0d67bdda06579d6f18d701f285a

development-addon manifest
  9a01655d63044ab126fd71236ca2cb814221317ee9b6b44fd2417fa5535a8b2a

test-addon manifest
  47d9f2e24e74b23e34ae6bfa95a0df22ec7cf9505e3e189dc3d6bdf2dc1c8b5f
```

Authoritative Phase 2 boundary:

```text
docs/stages/STAGE3C_PHASE2_FINAL.md
docs/evidence/STAGE3C_PHASE2_ARTIFACT_MANIFEST_SCHEMA_RESULT.md
```

## Candidate archive set

```text
cpython-android-cli-3.14.6-android24-aarch64-runtime-base.tar.gz
cpython-android-cli-3.14.6-android24-aarch64-development-addon.tar.gz
cpython-android-cli-3.14.6-android24-aarch64-test-addon.tar.gz
```

## Candidate archive envelope

```text
<artifact-id>/
  metadata/
    manifest.json
    manifest-index.json
    product-lock.json
    licenses/
      CPython-LICENSE.txt
  payload/
    <schema-v1 archive paths>
```

The archive is a staging envelope. Extraction is not installation.

## Candidate normalization contract

```text
container format
  POSIX pax tar

compression
  gzip

compression level
  9

gzip filename
  empty

gzip mtime
  0

tar member mtime
  0

uid / gid
  0 / 0

uname / gname
  empty / empty

envelope directory mode
  0755

metadata regular-file mode
  0644

payload mode
  exact schema-v1 mode

member ordering
  exact deterministic order defined by the writer

hardlinks
  forbidden

special entries
  forbidden

pax headers
  only deterministic path/linkpath extensions when required
```

This candidate becomes frozen only after target evidence passes.

## Payload source model

```text
runtime-base OWNED_PAYLOAD
  work/termux/stage3c-phase1-isolated-variants/runtime-base/prefix

development-addon OWNED_PAYLOAD
  work/termux/stage3b-promoted-runtime/prefix

test-addon OWNED_PAYLOAD
  work/termux/stage3b-promoted-runtime/prefix

STRUCTURAL_PARENT
  emitted from manifest metadata
  no recursive payload ownership
```

Every source entry must be checked against the schema-v1 manifest before serialization.

## Metadata source model

```text
metadata/manifest.json
  exact artifact manifest bytes

metadata/manifest-index.json
  exact accepted manifest-index bytes

metadata/product-lock.json
  exact accepted product-lock bytes

metadata/licenses/CPython-LICENSE.txt
  exact content selected by the manifest license hash and size
```

## First gate

The first Phase 3 workflow must:

```text
verify accepted Phase 2 hashes and check counts
verify source products before serialization
build every archive twice in independent output locations
require byte-identical SHA-256 and size for build A and build B
retain build A archives
inspect every tar and gzip header
verify exact member ordering and member set
verify metadata files byte-for-byte
verify every regular payload size and SHA-256
verify every symlink target
verify every directory and file mode
verify uid/gid/uname/gname/mtime normalization
verify no hardlink, device, fifo, socket, absolute path, or parent traversal
extract with a safe policy into staging
verify extracted metadata and payload against the manifest
verify canonical and runtime-base source non-mutation
```

## Expected outputs

```text
results/termux/stage3c-phase3-reproducible-archives/
  input/
    manifest-schema/
  archives/
    *.tar.gz
  build-a-index.json
  build-b-index.json
  reproducibility.json
  archive-verification.json
  extraction-verification.json
  canonical-before.json
  canonical-after.json
  runtime-before.json
  runtime-after.json
  source-mutation-check.txt
  workflow-status.json
  verification.json
```

## Acceptance conditions

```text
[ ] accepted Phase 2 identities exact
[ ] all three archives generated
[ ] independent build A/B hashes and sizes identical
[ ] gzip header normalization exact
[ ] tar metadata normalization exact
[ ] exact member order and set pass
[ ] metadata bytes exact
[ ] regular payload hashes exact
[ ] symlink targets exact
[ ] structural parents remain non-owning
[ ] unsafe paths and entry types zero
[ ] safe staging extraction passes
[ ] extracted trees match manifests
[ ] source mutation controls pass
[ ] claim boundary recorded
```

## Non-goals

```text
installing directly from the archive
selecting an installed ownership registry
handling path collisions
same-version reinstall
upgrade or downgrade
rollback or interrupted-operation recovery
uninstall
release signing or publication
```

## Claim boundary

A Phase 3 PASS will prove deterministic archive serialization, retained archive integrity, safe staging extraction under the tested implementation, and exact schema-v1 payload fidelity.

It will not prove transactionally safe installation or lifecycle behavior.
