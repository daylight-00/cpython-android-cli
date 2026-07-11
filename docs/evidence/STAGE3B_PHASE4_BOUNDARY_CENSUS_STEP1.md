# Stage 3-B Phase 4.1 Product-Boundary Census: Step 1

> **Status:** PASS — comparison object refined
> **Operation:** read-only historical/replay/package census
> **Final marker:** `STAGE3B_PRODUCT_BOUNDARY_ANALYSIS=PASS`

## Inputs

```text
historical development prefix
  experiments/bootstrap-android-build/android-python-work/prefix

replay composite prefix
  work/workstation/stage3b-phase2-replay/
    cross-build/aarch64-linux-android/prefix

replay upstream package
  python-3.14.6-aarch64-linux-android.tar.gz
  sha256 a16e0433b6f7e69c4634b52ce582d4d387447fbcfed797425f669ac224631f4f
```

Both prefix metadata fingerprints were unchanged before and after inspection.

## Prefix census

| Metric | Historical prefix | Replay composite prefix |
|---|---:|---:|
| entries | 3155 | 9053 |
| directories | 216 | 376 |
| files | 2934 | 8631 |
| symlinks | 5 | 46 |
| ELF objects | 81 | 88 |
| file bytes | 79336714 | 288157138 |

Path comparison:

```text
common exact       3068
common different     86
only historical       1
only replay        5899
```

## Launcher development contract

The launcher consumes three files.

```text
Python.h          exact byte match
pyconfig.h        exact byte match
libpython3.14.so  present in both, byte difference
```

Hashes:

```text
Python.h
  historical/replay
  e39aad93d70c3ea1a63b77ec5795ff59a5c177745aedace6f83bbf4275a20d9f

pyconfig.h
  historical/replay
  f92a48f0cfce0f5f687590ed9c485d3381dfaaff16ba320e0be5a413b7b98fb5

libpython3.14.so
  historical
  45ebdbf5a70a63c87d1d4aab2c82fdf20f9bc7035dee53a77c4f74ffd9e38008
  replay composite
  bbf814194fff8d4b7c4bf2570124408a6e858d23793c97c5599e732b6e511f47
```

The library byte difference is not classified as failure. Phase 1 already established that the historical prefix was produced on macOS while the replay was produced on Linux. Semantic ELF and consumer behavior remain the relevant gates.

## Upstream package census

```text
members              3194
directories            239
files                  2952
symlinks                  3
declared file bytes 79419009
```

Top-level archive members:

```text
README.md
android-env.sh
android.py
prefix/
testbed/
```

All three launcher contract paths exist under the package's `prefix/` root.

## Interpretation

The large full-prefix difference is primarily a product-boundary signal, not a runtime-equivalence result.

```text
replay composite prefix
  dependency headers, libraries, tools and metadata
  CPython development files
  CPython runtime files

upstream package
  selected embedding/development surface
  selected runtime surface
  Android support/test files
```

The package size and member count are close to the historical prefix, while the composite prefix is much larger. Therefore the next exact comparison must be:

```text
historical prefix
    versus
replay package prefix/
```

not historical prefix versus the entire replay composite prefix.

No pruning or canonical-path change is authorized by Step 1.
