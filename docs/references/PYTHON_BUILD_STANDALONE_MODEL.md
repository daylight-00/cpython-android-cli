# Reference: Python Standalone Distribution Model

> **Reviewed:** 2026-07-16

## Primary sources

- Astral standalone builds: https://github.com/astral-sh/python-build-standalone
- uv Python download metadata tooling: https://github.com/astral-sh/uv/blob/main/crates/uv-python/fetch-download-metadata.py

## Useful product concepts

The standalone ecosystem separates producer and consumer artifacts. Common archive classes include:

```text
full
  build and installed products for downstream producers and auditing

install_only
  installed runtime tree

install_only_stripped
  installed runtime tree with native debug symbols stripped
```

Machine-readable metadata records Python version, target, build options, archive identity, paths, and provenance. Consumers such as uv prefer runnable installation-oriented artifacts rather than complete producer workspaces.

## Project relevance

Epoch 2 adopts the product-contract lessons, not a requirement to duplicate every implementation detail:

- one immutable runnable archive is sufficient for initial consumer integration;
- unstripped and symbol products can be separate;
- `full` is valuable when producer reconstruction or upstream compatibility requires retained build objects;
- external metadata and a release index must identify exact archive bytes;
- the installer is a consumer, not the archive producer.

Android-specific API level, ABI, Bionic, execution profile, wheel tags, and Termux qualification remain project-owned extensions.
