# Epoch 3 Charter: Clean upstream-derived Android standalone distribution

> **Status:** PLANNED
> **Input:** accepted Epoch 2 evidence export
> **Primary structural reference:** Astral `python-build-standalone`

## Mission

Create a new clean release repository that turns verified Python.org Android products and the BeeWare dependency products selected by CPython into a consumer-facing Android/Bionic standalone CPython distribution.

## Producer model

```text
verified Python.org Android package
+ inherited BeeWare dependency topology
+ project-owned standalone launcher and bounded adaptation
+ deterministic Astral-structured artifact transformation
+ metadata, licenses, qualification, and release index
= Epoch 3 product
```

Epoch 3 trusts upstream source-build, dependency, API, module, and linkage decisions. Every local byte-level mutation must be enumerated and justified.

## Repository boundary

The repository is initialized cleanly from an accepted product seed. It contains product code, release automation, tests, metadata, user documentation, and bounded provenance. It does not import the complete laboratory history.

## Artifact contract

The product should expose the same consumer-facing artifact family expected from Epoch 4:

```text
full
install_only
install_only_stripped
optional symbols/debug products
release index
checksums and attestations
licenses and provenance
qualification results
```

Epoch 3 `full` means a complete upstream-derived reconstruction and audit input, including exact upstream packages, project overlays, mutation manifests, installed product, metadata, and licenses. It does not claim a project-owned CPython/dependency object tree.

## Owned responsibilities

- upstream location and checksum policy;
- standalone launcher and Android host adaptation;
- deterministic extraction and bounded transformation;
- archive roots, layouts, flavors, and metadata;
- exact mutation and provenance manifests;
- static and target qualification;
- CI and public release production;
- uv-facing artifact identity and consumer documentation;
- maintenance and security response for project-owned delta.

## Not owned

- CPython source patch production;
- BeeWare dependency recipe production;
- independent NDK/API policy;
- independent extension and linkage topology;
- source-level PGO/LTO production.

## Acceptance

A clean clone must reproduce release artifacts from pinned upstream inputs, validate fresh extraction on supported Android contexts, expose the agreed runtime and SDK surface, and produce metadata consumable without knowledge of the research repository.
