# Stage 3-B Phase 4 Scope: CPython Development and Runtime Product Promotion

> **Status:** ACTIVE
> **Input:** Frozen Phase 2 replay and frozen Phase 3 dependency lock
> **Target:** aarch64-linux-android / API 24
> **Rule:** observe consumer contracts before defining new products

## Question

> Which generated CPython surfaces are actual development inputs and runtime inputs, and can the historical experiment paths be replaced by products derived from the controlled replay?

## Existing consumer contracts

### Launcher development consumer

`scripts/build/build-launcher.sh` currently consumes exactly:

```text
<CPYTHON_DEV_PREFIX>/include/python3.14/Python.h
<CPYTHON_DEV_PREFIX>/include/python3.14/pyconfig.h
<CPYTHON_DEV_PREFIX>/lib/libpython3.14.so
```

The configured prefix still points into:

```text
experiments/bootstrap-android-build/android-python-work/prefix
```

Phase 4 must determine whether the replay prefix can replace that historical development input without hiding additional requirements.

### Termux runtime consumer

`scripts/termux/prepare-runtime.sh` currently consumes:

```text
historical pristine runtime archive
    +
canonical launcher artifact
```

The default runtime archive is outside the repository product graph:

```text
$HOME/uv-base/cpython-3.14-aarch64-linux-android-for-uv.tar.gz
```

Phase 4 must derive and identify the replacement runtime source product before changing the assembly workflow.

## Upstream package boundary

The upstream `Android/android.py package` command does not archive the complete replay prefix.

It selects:

```text
tracked Android support files
selected OpenSSL/Python/SQLite headers
selected OpenSSL/Python/SQLite libraries
selected pkg-config metadata
Python stdlib and extension tree
```

and strips packaged shared objects unless debug packaging is requested.

Selected development and runtime files are stored under the archive's `prefix/` root. This is the upstream package product root, not the full cross-build target directory name.

Therefore the following are distinct objects:

```text
composite replay prefix
upstream Android package archive
project runtime-shaped prefix
launcher artifact
```

They must not be collapsed into one implicit “Python build” object.

## Phase sequence

```text
Phase 4.1  read-only product-boundary census
Phase 4.2  launcher development-input promotion
Phase 4.3  runtime-source product promotion
Phase 4.4  generated runtime assembly handoff
```

## First action

Run:

```sh
bash experiments/stage3b-product-boundary/analyze-current-boundaries.sh
```

The analyzer compares:

```text
historical development prefix
controlled replay development prefix
controlled replay package archive
launcher three-file development contract
```

It records inventories and diffs without modifying any input tree.

Expected marker:

```text
STAGE3B_PRODUCT_BOUNDARY_ANALYSIS=PASS
```

Primary result:

```text
results/workstation/stage3b-product-boundary/product-boundary-summary.json
```

Detailed TSV evidence is written beside the summary.

Step 1 established that the full replay prefix is not the correct equality object. Compare the selected package product directly:

```sh
bash experiments/stage3b-product-boundary/compare-package-boundary.sh
```

Expected marker:

```text
STAGE3B_PACKAGE_PREFIX_COMPARISON=PASS
```

Mechanically classify the remaining differences:

```sh
bash experiments/stage3b-product-boundary/review-package-differences.sh
```

Expected marker:

```text
STAGE3B_PACKAGE_DIFF_REVIEW=PASS
```

Compare the regenerated CPython ELF semantic surfaces and capture the exact five non-ELF differences:

```sh
bash experiments/stage3b-product-boundary/compare-regenerated-surfaces.sh
```

Expected marker when all 69 semantic surfaces match:

```text
STAGE3B_REGENERATED_SURFACE_COMPARE=PASS
```

Capture structured deltas in the five remaining build/development metadata files:

```sh
bash experiments/stage3b-product-boundary/analyze-metadata-deltas.sh
```

Expected marker:

```text
STAGE3B_METADATA_DELTA_CAPTURE=PASS
```

Result:

```text
results/workstation/stage3b-product-boundary/
  historical-package-prefix-summary.json
  historical-prefix-inventory.tsv
  replay-package-prefix-inventory.tsv
  historical-package-prefix-diff.tsv
```

## Phase 4.2 product promotion

Phase 4.1 is frozen. On Victor, promote the locked replay package:

```sh
bash experiments/stage3b-product-promotion/promote-replay-package.sh
```

Expected marker:

```text
STAGE3B_CPYTHON_PRODUCT_PROMOTION=PASS
```

Canonical transport product:

```text
out/aarch64-linux-android24/release/cpython/
  python-3.14.6-aarch64-linux-android.tar.gz
```

Derived workstation development view:

```text
work/workstation/stage3b-promoted-cpython/prefix
```

The archive is synchronized to Termux. The extracted development view remains on Victor and exists only to build the launcher.

## Phase 4.2 launcher consumer gate

Build isolated launcher candidates from the historical and promoted development inputs:

```sh
bash experiments/stage3b-launcher-promotion/compare-launcher-products.sh
```

Expected marker:

```text
STAGE3B_PROMOTED_LAUNCHER_COMPARE=PASS
```

The canonical launcher is not overwritten by this comparison.

## Acceptance conditions

```text
[x] historical and replay development prefixes inventoried
[x] input-tree non-mutation checks pass
[x] launcher three-file contract compared
[x] replay package member boundary inventoried
[x] differences classified by product role
[x] replay development product promoted to canonical generated output
[x] launcher rebuilt from promoted development product
[x] replacement runtime-source product selected and justified
[ ] runtime assembly no longer depends on the hidden historical archive
[ ] generated handoff is ready for Phase 5 closure validation
```

## Canonical workstation handoff

After product promotion, rebuild the canonical launcher on Victor:

```sh
bash experiments/stage3b-product-promotion/promote-replay-package.sh
bash scripts/build/build-launcher.sh
```

The first command refreshes the portable checksum sidecar and derived development view. The second command now uses the promoted development prefix by default.

Generated handoff:

```text
out/aarch64-linux-android24/release/
  bin/python3.14
  cpython/python-3.14.6-aarch64-linux-android.tar.gz
  cpython/SHA256SUMS
  metadata/build-info.txt
  metadata/cpython-product.json
```

This tree is then synchronized to Termux. Target-side assembly and validation remain separate gates.

## Non-goals

Phase 4 does not yet:

```text
declare file-count equality with Stage 3-A
delete replay-prefix files
rewrite sysconfig metadata
change the frozen launcher architecture
claim Termux runtime behavior before target-side validation
define the final public distribution archive
```
