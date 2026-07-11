# Stage 3-B Phase 4.2 Launcher Consumer Comparison

Build the same launcher source twice through the canonical build script:

```text
historical development prefix -> historical candidate
promoted development prefix   -> promoted candidate
```

Neither candidate overwrites the canonical launcher.

Run on Victor:

```sh
bash experiments/stage3b-launcher-promotion/compare-launcher-products.sh
```

The comparison records byte hashes and compares ELF header, dynamic tags, and normalized dynamic-symbol surfaces.

Expected marker:

```text
STAGE3B_PROMOTED_LAUNCHER_COMPARE=PASS
```
