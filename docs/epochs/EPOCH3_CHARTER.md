# Epoch 3 Charter: Clean upstream-derived Android standalone distribution

> **Status:** PLANNED
> **Input:** accepted Epoch 2 evidence export and complete Epoch 3 selection register
> **Primary structural reference:** Astral `python-build-standalone`
> **Decision authorities:** ADR-0006 and ADR-0007
> **Completion gates:** [`EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md`](../roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md)

## Mission

Create a new clean release repository that turns verified Python.org Android products and the BeeWare dependency products selected by CPython into a consumer-facing Android/Bionic standalone CPython distribution.

Epoch 3 selects a product from Epoch 2 evidence. It does not merely copy the maximum feature surface demonstrated by the research runtime.

## Producer model

```text
verified Python.org Android package
+ inherited BeeWare dependency topology
+ project-owned standalone launcher and bounded adaptation
+ deterministic Astral-structured artifact transformation
+ explicitly selected runtime, SDK, and data surface
+ metadata, licenses, qualification, and release index
= Epoch 3 product
```

Epoch 3 trusts upstream source-build, dependency, API, module, and linkage decisions by default. Every local byte-level mutation must be enumerated and justified.

API-36 variants remain Epoch 2 comparison evidence unless a separate Epoch 3 product decision explicitly selects one. The official upstream API-floor product remains the default input.

## Selection register

Before implementation expands, every optional or policy-bearing Epoch 2 result must receive exactly one disposition:

```text
adopt
adopt-with-redesign
exclude
defer-to-epoch4
```

The register must cover at least:

- base pip and command wrappers;
- CA and timezone payload policy;
- runtime-only, on-device SDK, and cross-build SDK modes;
- subprocess secondary surface;
- venv move/update cases;
- multiprocessing primitives;
- uv integration details;
- optional symbols/debug/test artifacts;
- API-36-derived inputs.

A passing experiment is not an inclusion decision. Excluded and deferred capabilities must be absent from release claims and corresponding qualification requirements.

## Repository boundary

The repository is initialized cleanly from an accepted product seed and content-addressed evidence export. It contains product code, release automation, selected tests, metadata, user documentation, the selection register, and bounded provenance. It does not import the complete laboratory history.

## Mandatory product invariants

- direct verified Python.org/BeeWare derivation;
- pure Bionic plus Android-public native closure;
- no required Termux native provider or hard-coded Termux identity;
- fresh-extraction execution;
- accepted whole-prefix relocation;
- no project-required `LD_LIBRARY_PATH`;
- no loader-bootstrap self re-execution;
- truthful Astral-compatible archive and `PYTHON.json`;
- exact mutation, provenance, license, checksum, and qualification accounting.

## Artifact contract

The product exposes the selected subset of the common Epoch 3/Epoch 4 family:

```text
full
install_only
install_only_stripped
optional symbols/debug/SDK products
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
- archive roots, layouts, selected flavors, and metadata;
- exact mutation and provenance manifests;
- selected runtime, SDK, data, and consumer surface;
- static and target qualification;
- CI and public release production;
- selected uv-facing artifact identity and consumer documentation;
- maintenance and security response for project-owned delta and bundled data.

## Not owned

- CPython source patch production;
- BeeWare dependency recipe production;
- independent NDK/API policy without a separate product decision;
- independent extension and linkage topology;
- source-level PGO/LTO production.

## Initialization acceptance

Epoch 3 may initialize only when E3-I1 through E3-I4 pass: accepted evidence export, complete selection register, clean repository boundary, and frozen product contract.

## Completion

Epoch 3 completes when E3-G1 through E3-G10 pass. A clean clone must reproduce selected release artifacts from pinned upstream inputs, validate fresh extraction on supported Android contexts, expose only the selected runtime and SDK surface, and produce metadata consumable without knowledge of the research repository.
