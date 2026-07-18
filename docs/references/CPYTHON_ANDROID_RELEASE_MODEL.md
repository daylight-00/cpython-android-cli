# Reference: CPython Android Release Model

> **Reviewed:** 2026-07-16

## Primary sources

- CPython Android documentation: https://docs.python.org/3/using/android.html
- CPython Android downloads: https://www.python.org/downloads/android/
- PEP 738: https://peps.python.org/pep-0738/
- CPython Android tooling: https://github.com/python/cpython/tree/main/Platforms/Android

## Current upstream model

CPython publishes Android embeddable packages for supported architectures and documents an application-embedding workflow. The packaged runtime is an official and valuable upstream product, but the official model does not define a general interactive `python3` command-line distribution for Android users.

Current CPython tooling builds, packages, and tests Android products under `Platforms/Android`. The release package provides a prefix-shaped runtime suitable for embedding and downstream adaptation.

## Project relevance

Epoch 2 and Epoch 3 adopt the official Python.org Android package as the primary runtime input and inherit the BeeWare dependency products selected by CPython. Epoch 2 tests the thinnest CLI adaptation and bounded API variants; Epoch 3 productizes the accepted upstream input:

```text
official CPython Android lineage
  + relocatable native launcher
  + complete runtime closure
  + standalone release metadata
  + Termux-first qualification
  = Android/Bionic standalone CPython CLI product
```

The project does not need to compete with CPython's embedding support. It builds a different consumer-facing contract from the same upstream lineage.

## Adopted epoch policy

The official upstream API/product combination is the control. Epoch 2 additionally compares CPython/launcher API 36 and complete same-source API 36 variants. Full project-owned source production is deferred to Epoch 4.
