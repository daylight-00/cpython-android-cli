# ADR-0007: Epoch 2 evidence program and Epoch 3 selection gates

- **Status:** Accepted
- **Date:** 2026-07-19
- **Extends:** ADR-0006
- **Detailed plan:** [`EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md`](../roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md)

## Context

ADR-0006 separated the upstream-derived Epoch 3 product from the full source-producing Epoch 4 system. A detailed upstream-thin research plan subsequently identified the remaining loader, relocation, launcher, sysconfig, SDK, data, feature, portability, update, and artifact-design questions.

Two additional rules are required to avoid collapsing research evidence into product policy:

1. API-36 builds remain mandatory Epoch 2 experiments because they use the same upstream-published CPython and BeeWare source revisions, patches, recipes, module decisions, toolchain identity, and linkage topology as practical, changing the Android compile API as the controlled variable.
2. A successful Epoch 2 experiment does not automatically become an Epoch 3 product feature.

For example, an external pip payload may work in qualification while the clean Epoch 3 product may deliberately omit base pip. The same distinction applies to bundled certificate data, timezone data, multiprocessing capabilities, SDK modes, generated command wrappers, optional artifact flavors, and host integrations.

## Decision

### 1. Epoch 2 produces evidence, not automatic product inclusion

Every material Epoch 2 experiment receives an evidence disposition:

```text
pass
bounded-pass
fail
unavailable
```

A passing result proves feasibility within its stated boundary. It does not by itself authorize inclusion in the clean distribution.

### 2. Epoch 3 applies an explicit selection disposition

Every optional or policy-bearing Epoch 2 result must receive exactly one Epoch 3 disposition:

```text
adopt
adopt-with-redesign
exclude
defer-to-epoch4
```

The disposition must include rationale, product impact, maintenance ownership, security/update ownership, consumer impact, and qualification consequences.

No item may enter the Epoch 3 product merely because it was present in the research runtime or because an experiment passed.

Full CPython/dependency source production remains Epoch 4.

### 3. Mandatory product invariants and selectable capabilities are separate

Epoch 3 must satisfy mandatory invariants such as:

- direct verified Python.org/BeeWare derivation;
- pure Bionic and Android-public native closure;
- no required Termux native provider or hard-coded Termux identity;
- fresh-extraction execution;
- accepted whole-prefix relocation behavior;
- no project-required `LD_LIBRARY_PATH`;
- no loader-bootstrap self re-execution;
- truthful Astral-structured archives and metadata;
- exact mutation, provenance, license, and qualification accounting.

Feature and policy choices such as base pip, command wrappers, bundled CA data, bundled timezone data, supported multiprocessing primitives, SDK modes, optional debug products, and specific venv relocation cases are selected separately.

### 4. API 36 is mandatory Epoch 2 research

The controlled matrix remains:

```text
A  exact official Python.org/BeeWare binary control

B  the same upstream CPython and launcher source revisions and patches,
   rebuilt for API 36 while retaining the official BeeWare dependency binaries

C  the same upstream CPython and BeeWare dependency source revisions,
   patches, recipes, module decisions, NDK/toolchain identity, and linkage
   topology as practical, rebuilt for API 36
```

The API-36 results are comparison evidence. They do not automatically replace the official upstream API-floor product in Epoch 3. Epoch 3 selects its release floor and inputs from the complete Epoch 2 evidence export.

### 5. The detailed upstream-thin plan becomes canonical subordinate authority

The raw external plan is preserved byte-for-byte. The adjudicated canonical plan:

- organizes the remaining work into UT-0 through UT-7 plus the API-36 comparison track;
- defines evidence outputs and stop conditions;
- defines Epoch 2 closure gates;
- defines Epoch 3 initialization and completion gates;
- distinguishes mandatory product invariants from selectable capabilities;
- keeps CPython/dependency source-production responsibility in Epoch 4.

## Consequences

- research can explore capabilities without silently committing to their inclusion;
- Epoch 3 may intentionally produce a smaller and more maintainable product than the maximum experimentally feasible runtime;
- API-36 research remains part of Epoch 2 while API-36 release adoption remains an Epoch 3 decision;
- the clean repository starts from an explicit selection register rather than from the historical research runtime;
- Epoch 4 inherits unresolved or source-required mechanisms without changing the Epoch 3 consumer contract by default.
