# Epoch 3 Release-Blocker Resolution Plan

> **Status:** active plan
> **Product baseline:** frozen canonical `full`, `install_only`, and `install_only_stripped` artifacts
> **Default design rule:** adopt Astral-like behavior and structure wherever the upstream-thin and Android boundaries do not make it impossible
> **Non-claim:** this plan does not authorize selectability or publication

## 1. Purpose

The three product artifacts and their deterministic release-family envelope are complete and byte-frozen. The remaining work is not artifact assembly. It is the bounded resolution of evidence, data, consumer, operations, and execution-context blockers that must be satisfied before the product can be selected or published at its intended Android scope.

No blocker experiment may silently rebuild CPython or a dependency, substitute native providers, or alter the three frozen archive bytes. If release metadata must expand, a later release-family revision must reuse the exact frozen artifacts and add only independently verifiable metadata or data products.

## 2. Mandatory principles

1. **Astral-like by default.** Use Astral archive, metadata, consumer, checksum, and catalog semantics unless an Android or upstream-thin limitation makes the exact behavior impossible.
2. **Truthful substitution only.** Android-specific substitutions must be named, justified, and represented without inventing producer objects or build metadata.
3. **Artifact immutability.** The accepted artifact SHA-256 identities are inputs to every release-blocker experiment, never outputs to be regenerated.
4. **Parallel evidence lanes.** Local evidence and owner-device evidence proceed independently and may finish in any order.
5. **No broad claim from a narrow context.** API level, page size, or execution-context claims require direct evidence from that context.
6. **Fail closed.** Missing component identity, license evidence, data provenance, consumer compatibility, update operations, or required device evidence remains an explicit blocker.

## 3. Frozen product identities

| Flavor | SHA-256 | Size |
|---|---|---:|
| `full` | `20fe6b6a7877af303461cd271f658f40750b6a3d1981f437dd730aea07c0ff12` | 39,408,292 |
| `install_only` | `84315c6967e56ed2ad3587ffcd459597835b18897f4988de9fc7c67a1bf38d76` | 23,841,726 |
| `install_only_stripped` | `40951002c5880b223fa78c7b956dfcf2929e3ebf8e8beb9420c4179b98231134` | 23,841,241 |

Artifact-family identity:

```text
release id        cpython-3.14.6+e3-r1-aarch64-linux-android
file count        23
family fingerprint 87464d93187c0a43663c8db98925566bc918f77ae0fccf83110307bcd593b302
release digest    81bd66f5cd1978485eb50991d5a6e773b55b51defb52483db6db5215c1a91a9e
```

## 4. Parallel lanes

### Lane L1 — Component and license closure

Goal: produce a complete component-to-license map for all distributed bytes and distinguish distributed components from Android system dependencies.

Initial census must detect component/version evidence from the frozen archives without external guesses. Expected classes include CPython, the project launcher, pip and its vendored packages, OpenSSL, SQLite, bzip2, XZ/liblzma, zstd, Expat, libmpdec, libffi, and Android system providers such as `libz.so`.

Completion requires:

- exact component and version evidence;
- distributed-path ownership or embedded-object evidence;
- SPDX expression or truthful non-SPDX status;
- exact notice/license source identity;
- redistribution-obligation summary;
- complete mapping for all distributed bytes;
- independent missing-component and missing-license negative fixtures.

The first census is intentionally allowed to report gaps. A gap report is evidence, not completion.

### Lane L2 — CA and timezone data products

Goal: select versioned, independently updateable CA and timezone payloads under `DATA_ROOT`.

Completion requires exact upstream source identity, version, checksum, archive layout, activation contract, caller override, rollback, revocation, and expiry/update behavior. No update writes into the immutable Python install root.

### Lane L3 — Astral consumer compatibility

Goal: demonstrate that the common Astral-style metadata and archive structure can be consumed by the selected parser or managed-install path without undocumented project-only assumptions.

Completion requires a golden consumer fixture, extraction/install relocation, `PYTHON.json` interpretation, flavor selection, and negative tests for unsupported producer-complete fields. Any project extension must be isolated from the common Astral schema.

### Lane L4 — Release, security, update, and revocation operations

Goal: define the lifecycle for official Python patch updates, adaptation changes, data-only updates, supersession, rollback, and emergency revocation.

Completion requires deterministic catalog transitions, immutable prior-release retention, no ambiguous replacement of the same identity, security ownership boundaries, support status, rollback receipt, and revocation readback.

### Lane T1 — API 24 runtime

Goal: directly execute the frozen artifact family on Android API 24, the official upstream floor.

Static API metadata is not sufficient. The exact artifact must pass startup, relocation, read-only execution, native-extension imports, subprocess re-entry, pip, venv, `python-config`, and pkg-config on an API 24 target.

### Lane T2 — Real 16 KiB page-size runtime

Goal: execute the exact artifact on a real AArch64 Android device whose runtime page size is 16,384 bytes.

ELF alignment is already statically verified. This lane proves actual runtime support and must record kernel page size, device identity, Android version/API, and all bounded runtime checks.

### Lane T3 — Non-Termux Android context

Goal: execute the exact native CLI distribution in a non-Termux Android app-private or shell context without Termux native providers.

The context must record package/process identity, filesystem roots, environment, dynamic provider resolution, and absence of Termux package-prefix dependencies. An APK/JNI consumer is not required unless chosen as the bounded host for this execution context.

## 5. Gate model

| Gate | Requirement | May run in parallel | Blocks |
|---|---|---|---|
| RB-0 | Artifact-family authority frozen | no | all blocker work |
| RB-1 | Component/license closure | yes | selectability and publication |
| RB-2 | CA/timezone data products | yes | intended product selection |
| RB-3 | Astral consumer compatibility | yes | Astral-like selection claim |
| RB-4 | Release/security/update/revocation operations | yes | publication |
| RB-5 | API 24 runtime | yes | API 24 support claim |
| RB-6 | Real 16 KiB runtime | yes | 16 KiB support claim |
| RB-7 | Non-Termux runtime | yes | Termux-independence claim |
| RB-8 | Final release-candidate integration | after RB-1..RB-7 | selectability |

RB-5, RB-6, and RB-7 do not have to be satisfied by one physical device, but every receipt must bind the exact same frozen artifact identities.

## 6. First bounded action

The first action is a deterministic component and license census over the exact artifact family. It must:

1. verify artifact-family authority;
2. locate the exact family from the owner cache or verified result archive;
3. inspect the `full` and `install_only` payloads without modifying them;
4. record component/version evidence and distributed paths;
5. classify license evidence as complete, present-but-unmapped, missing-text, missing-version, or external-system-provider;
6. emit a gap register and independent audit;
7. preserve all other release blockers as open;
8. make no selectability or publication claim.

## 7. Decision rules

- A component is not omitted because its code is statically linked into an extension.
- An Android system library is recorded as an external provider and is not represented as a distributed payload component.
- A generic license text is not accepted as component-specific notice evidence when copyright or attribution text is required.
- A source-path string inside an ELF is evidence only when corroborated by a version or symbol surface; it is not by itself a license authority.
- If exact license bytes are absent, acquire them later through a bounded official-source package with fixed source identity and fail-closed checks.
- If Astral has a compatible surface, adopt it. If not, use a separately named project metadata file rather than changing common Astral semantics.

## 8. Stop conditions

Stop and retain the blocker when:

- a component cannot be identified from frozen bytes or an exact official source;
- license obligations or copyright notices remain ambiguous;
- data payload version/update ownership is undefined;
- a consumer requires fabricated producer metadata;
- a target context cannot prove its API, page size, or non-Termux identity;
- a proposed correction changes any frozen artifact byte;
- a PASS would depend on weakening a previously valid gate.

## 9. Final release boundary

After all mandatory blockers pass, a new release-family revision may add complete component-license mapping, data-product references, operations policy, and final platform qualification receipts while reusing the exact three artifact bytes. Only a subsequent explicit selectability authority may set `selectable=true`. Publication remains a separate owner authorization.
## 10. RB-1 baseline result and next bounded action

The first deterministic census passed and is frozen as a non-closing baseline. It identified 12 component classes, resolved 10 exact versions, retained 12 blocking gaps, and left only `libffi` version provenance unresolved. The baseline does not complete component-to-license mapping and does not authorize selectability or publication.

The next bounded action is source-provenance resolution. It must:

1. bind the exact frozen artifact family and RB-1 baseline authority;
2. read the exact Python.org Android package and its preserved `android.py` without changing artifact bytes;
3. resolve the BeeWare dependency release coordinates, including `libffi`;
4. bind an exact CPython 3.14.6 source release coordinate for later authoritative license extraction;
5. emit a deterministic license-source plan and a reduced-but-still-open gap register;
6. preserve `rb1_closed=false`, `selectable=false`, and `publication=false`.

