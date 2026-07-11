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
