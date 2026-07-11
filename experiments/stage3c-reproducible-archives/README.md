# Stage 3-C Phase 3: Reproducible Archive Serialization

> **Status:** ACTIVE — target evidence pending
> **Input:** frozen Stage 3-C Phase 2 manifests

## Question

```text
Can the accepted schema-v1 artifacts be serialized twice to byte-identical
normalized tar.gz archives and independently verified through safe staging
extraction?
```

## Run

```sh
bash experiments/stage3c-reproducible-archives/run-reproducible-archives.sh
```

## Frozen manifest input

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

## Archive filenames

```text
cpython-android-cli-3.14.6-android24-aarch64-runtime-base.tar.gz
cpython-android-cli-3.14.6-android24-aarch64-development-addon.tar.gz
cpython-android-cli-3.14.6-android24-aarch64-test-addon.tar.gz
```

## Envelope

```text
<artifact-id>/
  metadata/
    manifest.json
    manifest-index.json
    product-lock.json
    licenses/
      CPython-LICENSE.txt
  payload/
    <manifest archive paths>
```

## Normalization

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
payload mode               exact manifest mode
hardlinks                  forbidden
special entries            forbidden
pax headers                path/linkpath only when required
```

## Source mapping

```text
runtime-base
  isolated validated runtime-base prefix

development-addon
  canonical promoted prefix selected by manifest

test-addon
  canonical promoted prefix selected by manifest

STRUCTURAL_PARENT
  emitted as a directory header from manifest metadata
  never registered as exclusive payload ownership
```

## Builder

```text
build-reproducible-archives.py
```

The builder performs 31 checks:

```text
accepted generator 42/42 and verifier 48/48
accepted manifest/index/product-lock hashes
source path type/mode/size/hash/symlink checks
license hash and size checks
safe manifest paths
independent build A and build B
three byte-identical archive hashes
three identical sizes and member counts
```

Build B is temporary. Its index is retained while build A archives remain in the result tree.

## Independent verifier

```text
verify-reproducible-archives.py
```

The verifier performs 76 checks:

```text
exact gzip header
exact member order and count
unique safe member paths
allowed entry types only
hardlinks zero
normalized uid/gid/names/mtime
allowed PAX header keys
exact envelope and metadata modes
metadata byte identity
payload regular-file hashes
payload symlink targets
safe custom staging extraction
extracted metadata and payload identity
retained archive hash/size/member-count agreement with build index
```

## Results

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
  canonical-before.json
  canonical-after.json
  runtime-before.json
  runtime-after.json
  source-mutation-check.txt
  workflow-status.json
```

## Expected markers

```text
STAGE3C_PHASE3_REPRODUCIBLE_ARCHIVE_BUILD=PASS
REPRODUCIBLE_ARCHIVE_ACCEPTED_INPUTS=PASS
REPRODUCIBLE_ARCHIVE_BUILD=31/31 PASS
REPRODUCIBLE_ARCHIVE_BYTE_IDENTITY=3/3 PASS
REPRODUCIBLE_ARCHIVE_VERIFICATION=76/76 PASS
REPRODUCIBLE_ARCHIVE_SAFE_STAGING_EXTRACTION=3/3 PASS
REPRODUCIBLE_ARCHIVE_SOURCE_MUTATION_CHECK=PASS
STAGE3C_PHASE3_REPRODUCIBLE_ARCHIVES=PASS
```

## Upload

```sh
RESULTS="$PWD/results/termux/stage3c-phase3-reproducible-archives"
ARCHIVE="$HOME/Downloads/stage3c-phase3-reproducible-archives-results-$(date +%Y%m%d-%H%M%S).tgz"

tar czf "$ARCHIVE" "$RESULTS"
printf 'upload: %s\n' "$ARCHIVE"
```

The TGZ includes the three generated tar.gz archives and may be substantially larger than earlier result bundles.

## Claim boundary

A PASS proves normalized archive serialization, byte identity across two target builds, exact retained archive integrity, and safe staging extraction under the tested implementation.

It does not prove installation transactions, collision handling, upgrade, rollback, or uninstall behavior.
