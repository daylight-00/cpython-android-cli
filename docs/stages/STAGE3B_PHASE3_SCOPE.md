# Stage 3-B Phase 3 Scope: Dependency Product Promotion

> **Status:** FROZEN
> **Result:** PASS — see `docs/evidence/STAGE3B_PHASE3_FINAL_SUMMARY.md`
> **Input:** Frozen Stage 3-B Phase 2 controlled replay
> **Target:** aarch64-linux-android
> **Principle:** identify products before promoting paths

## Question

> Can every third-party native dependency input consumed by the successful replay be represented as an explicit, immutable product identity rather than an incidental cache file?

## Inputs

The preserved producer declares six release products:

```text
bzip2    1.0.8-3
libffi   3.4.4-3
openssl  3.5.7-0
sqlite   3.50.4-0
xz       5.4.6-1
zstd     1.5.7-2
```

For the selected target, each declaration resolves to one release archive under:

```text
https://github.com/beeware/cpython-android-source-deps/releases/download/
```

The successful replay cache is evidence, but the cache pathname is not a promoted product identity.

## First action: read-only capture

Run:

```sh
bash experiments/stage3b-dependency-promotion/capture-current-inputs.sh
```

The capture records for each expected archive:

```text
dependency name
version
recipe revision
release tag
source URL
archive filename
SHA-256
size
tar member counts
declared member bytes
top-level archive paths
```

Expected marker:

```text
STAGE3B_DEPENDENCY_INPUT_CAPTURE=PASS
```

Result:

```text
results/workstation/stage3b-dependency-promotion/dependency-input-manifest.json
```

Promoted lock:

```text
config/dependencies/android-source-deps-aarch64-linux-android.lock.json
```

Verification command:

```sh
bash experiments/stage3b-dependency-promotion/verify-promoted-inputs.sh
```

Expected verification marker:

```text
STAGE3B_DEPENDENCY_INPUT_VERIFY=PASS
```

## Promotion model

Phase 3 distinguishes:

```text
download cache
    disposable location

dependency input identity
    tracked name/version/revision/URL/hash contract

extracted dependency prefix
    derived build input

CPython prefix
    downstream consumer
```

A cache hit is not reproducibility evidence unless the archive bytes match the promoted identity.

## Acceptance conditions

```text
[x] Phase 2 consumed all six declared release archives successfully
[x] all six cached archives exist
[x] all six archives are readable tar products
[x] SHA-256 and size captured for all six
[x] archive structural inventory captured for all six
[x] immutable identities promoted into a tracked manifest
[x] a second capture verifies the promoted identities
[x] extraction/product boundary is documented
```

## Non-goals

Phase 3 does not:

```text
rebuild the six dependency projects from source
rewrite their binaries
prune the CPython prefix
define the final runtime archive
perform Stage 3-A closure comparison
```

Rebuilding dependencies from source may become a separate later requirement. It is not silently implied by promoting the exact products consumed by this replay.
