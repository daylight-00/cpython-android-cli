# Stage 3-B Phase 4.1: Product-Boundary Census

This experiment observes the boundaries between:

```text
historical launcher development prefix
controlled replay development prefix
controlled replay upstream package
launcher three-file development contract
```

Run:

```sh
bash experiments/stage3b-product-boundary/analyze-current-boundaries.sh
```

Expected marker:

```text
STAGE3B_PRODUCT_BOUNDARY_ANALYSIS=PASS
```

Outputs:

```text
results/workstation/stage3b-product-boundary/
  product-boundary-summary.json
  historical-dev-inventory.tsv
  replay-dev-inventory.tsv
  development-prefix-diff.tsv
  replay-package-members.tsv
```

The analyzer hashes files but does not modify either prefix. Metadata-tree fingerprints are taken before and after the census to verify non-mutation.

## Refined package-prefix comparison

The first census showed that the full replay prefix contains thousands of development/dependency entries outside the upstream package boundary.

Compare the historical prefix directly against the archive's selected `prefix/` product without extracting it:

```sh
bash experiments/stage3b-product-boundary/compare-package-boundary.sh
```

Expected marker:

```text
STAGE3B_PACKAGE_PREFIX_COMPARISON=PASS
```

Step 1 low-level evidence:

```text
docs/evidence/STAGE3B_PHASE4_BOUNDARY_CENSUS_STEP1.md
```

## Difference review

After package-prefix comparison, classify every non-identical row mechanically:

```sh
bash experiments/stage3b-product-boundary/review-package-differences.sh
```

Expected marker:

```text
STAGE3B_PACKAGE_DIFF_REVIEW=PASS
```

This review does not assign semantic acceptability. It separates changed ELF files, changed regular files, link/kind changes, and paths present on only one side so that later analysis has a closed review set.
