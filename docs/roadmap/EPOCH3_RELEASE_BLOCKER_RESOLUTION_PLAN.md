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
## 11. Source-provenance resolver implementation

The bounded resolver is implemented but not yet accepted. It reads the two preserved copies of CPython's Android `android.py`, requires them to be byte-identical, resolves the six BeeWare dependency release tags, and validates an exact Python.org CPython 3.14.6 source archive before preserving its SPDX and license evidence.

The owner run must reduce the gap register only by resolving `libffi-version-unresolved`. A successful result is expected to leave 11 blocking gaps. It does not package final license payloads and cannot close RB-1.
## 12. Accepted source provenance and next bounded lane

The owner source-provenance run passed and is frozen by `rb1-source-provenance-authority.json`. It resolved the exact six BeeWare dependency release coordinates, bound the exact Python.org CPython 3.14.6 source archive, and reduced the baseline gap register from 12 to 11 solely by resolving `libffi-version-unresolved`.

The next bounded lane is authoritative license-payload acquisition plus component-expansion audit. It must not assume that the 12-class baseline is complete. It must detect bundled components evidenced by distributed bytes, including HACL* in `_hmac` and `_sha3`, and must quarantine version-mismatched source coordinates. In particular, CPython source SPDX entries for XZ 5.2.5 and mpdecimal 4.0.0 are not authorities for the frozen XZ 5.4.6 and libmpdec 2.5.1 product bytes.

The lane may acquire exact fixed-hash CPython source-deps archives for matching components and preserve license-like files as evidence. It may emit a component map and NOTICE candidate, but it must retain `rb1_closed=false`, `component_license_mapping_complete=false`, `selectable=false`, and `publication=false`. Frozen artifact bytes remain immutable.
## 13. License-payload expansion r1 static-fixture correction

The first owner attempt stopped during static verification before onboarding, source acquisition, artifact-family access, or target execution. The product and authority boundaries were not exercised. The failure was isolated to the negative fixture for the already-frozen source-provenance authority: it copied the entire repository while following unrelated historical work/result symlinks, some of whose external targets no longer existed in the owner checkout.

The correction copies only `experiments/epoch3-upstream-thin-release-blockers/`, the complete subtree read by the authority verifier, and preserves symlinks as symlinks. No verifier check, source identity, artifact identity, component-expansion rule, payload-acquisition rule, or claim boundary is weakened. The corrected runner must repeat the same static, source, reproducibility, independent-audit, rollback, and push gates.

## 14. License-payload expansion r2 source-symlink correction

The corrected owner r2 passed repository, static, onboarding, frozen source-authority, artifact-family, CPython source, and all five fixed-hash source-archive acquisition gates. Both independent target runs then stopped on the same normal zstd source-tree symlink, `tests/cli-tests/bin/unzstd`. The license inventory scanner had classified every non-directory and non-regular member as unsupported even though the lane reads selected regular files only and does not materialize source trees.

The bounded r3 correction accepts only relative symlinks whose lexical resolution remains inside the archive root, records no payload from them, and does not create or follow them. Absolute or escaping symlinks remain rejected. Hardlinks, devices, FIFOs, duplicate normalized names, unsafe paths, truncated members, and unsupported special types remain hard failures. CPython source scanning uses the same rule for consistency. No frozen artifact, source identity, selected license byte, component-expansion rule, mismatch quarantine, audit rule, or claim boundary changes.
## 12. RB-1 license-payload and component-expansion authority

The fixed-hash payload acquisition and component-expansion run passed and is frozen as a non-closing authority. It preserved the exact artifact family, acquired five exact source archives, expanded the component set from 12 to 13 by adding HACL*, and reduced the blocking gap register from 11 to 8. The result remains a candidate evidence set: component-to-license mapping, legal overlay integration, owner notice approval, selectability, and publication remain false.

The next bounded action is legal-evidence overlay and provider-policy synthesis. It must:

1. bind the frozen payload/component-expansion authority and exact artifact family;
2. acquire the exact BeeWare `xz-5.4.6-1` product dependency asset using its frozen SHA-256 and size, rather than the mismatched CPython SPDX `xz 5.2.5` coordinate;
3. extract and verify the exact XZ notice payload from the product-matching asset;
4. derive SQLite public-domain evidence from the exact `sqlite-3.50.4.0` source archive;
5. derive HACL* upstream-coordinate and license-header evidence from the exact CPython 3.14.6 source archive;
6. freeze the Android system-provider boundary from the accepted full static authority without representing platform libraries as distributed product bytes;
7. synthesize a deterministic legal-overlay candidate and updated component map without changing any frozen artifact byte;
8. retain complete obligation review, release-family integration, final notice approval, selectability, and publication as explicit open gates.

## 15. RB-1 legal-overlay implementation start

The accepted payload/component-expansion authority freezes 13 component classes, five exact source archives, HACL* expansion, mismatch quarantine, and an eight-gap boundary. A verification amendment binds that authority to the actual 23-check verifier output without altering any accepted claim.

The next bounded implementation synthesizes a legal-evidence overlay without changing any of the 23 frozen release-family files. It must:

1. reacquire and verify the exact CPython source and five fixed-hash source archives;
2. bind the exact BeeWare `xz-5.4.6-1` product asset and verify `AUTHORS`, `COPYING`, and `COPYING.GPLv2` by fixed hashes;
3. derive SQLite public-domain evidence from the exact SQLite source;
4. preserve HACL* license-header and upstream-coordinate evidence from the exact bundled CPython source;
5. preserve the bundled libmpdec 2.5.1 redistribution header rather than using the mismatched mpdecimal 4.0.0 SPDX coordinate;
6. freeze the exact Android external-provider boundary (`libc.so`, `libdl.so`, `liblog.so`, `libm.so`, and `libz.so`) without treating platform bytes as distributed product components;
7. produce a deterministic component-map candidate, notice candidate, legal file index, and independent audit twice byte-identically; and
8. reduce only the evidence-policy gap register from eight to four.

The remaining gates are complete componentization and obligation review, integration of authoritative legal evidence into a revised release family, inclusion of the project license in that family, and final owner approval of the notice set. This implementation cannot close RB-1 or authorize selectability or publication.
## 16. RB-1 legal-overlay authority and legal-integration start

The corrected owner r2 passed the exact artifact-family, source-input, XZ product-asset, two-run reproducibility, and independent-audit gates. The accepted authority freezes a deterministic 72-file legal evidence overlay with fingerprint `e4378c59eabcc6fdf5d07cccd718bd536d87deda531e5e2fcc3115fb6944a878`, resolves four evidence-policy gaps, and retains four explicit blockers. No frozen artifact byte changed.

The next bounded action may technically resolve only three blockers:

1. complete componentization and technical obligation review, including all 18 units listed by the exact pip 26.1.2 `pip/_vendor/vendor.txt`;
2. integrate the exact accepted legal evidence under a revised release-family metadata envelope while preserving the three artifact archives and their existing artifact sidecars byte-for-byte; and
3. include the project `LICENSE` in that revised family.

The revised family is an owner-approval-pending candidate, not a selectable or publishable product. `THIRD-PARTY-NOTICES` approval, RB-1 closure, selectability, and publication remain forbidden until a separate owner-approval transaction accepts the exact notice and integrated-family identities.
## 17. RB-1 technical obligation review and legal integration implementation start

The accepted legal-overlay authority opens a bounded non-closing integration lane. The implementation reads the exact pip 26.1.2 `vendor.txt` from the frozen install-only artifact, maps all 18 vendored units to their embedded license bytes, and combines them with the 13 top-level component classes for 31 technical review units.

The candidate release family uses release ID `cpython-3.14.6+e3-r2-aarch64-linux-android`. It reuses the three artifact archives and eighteen artifact sidecars byte-for-byte, preserves the r1 `release-index.json` and `SHA256SUMS` under `lineage/r1/`, integrates the accepted 72-file legal overlay and project `LICENSE`, and regenerates only the revised envelope metadata.

The bounded target is deterministic and must reduce the RB-1 gap register from four to one. The sole remaining gap is `final-notice-set-not-owner-approved`. A successful implementation transaction still cannot close RB-1, select the product, or authorize publication.


## RB-1 final notice owner approval gate

The accepted legally integrated family is frozen by `rb1-legal-integration-authority.json`. The only RB-1 gap is explicit owner approval of the exact notice set. The review-preparation runner must produce a deterministic dossier bound to the release, family, notice, component-map, technical-review, pip-vendor-review, and project-license hashes. Running the runner is not approval. RB-1 may close only after a separate owner approval document preserves every binding, contains the exact required statement, identifies the owner, and sets `approved=true`. Selectability and publication remain false because RB-2 through RB-7 are independent blockers.
