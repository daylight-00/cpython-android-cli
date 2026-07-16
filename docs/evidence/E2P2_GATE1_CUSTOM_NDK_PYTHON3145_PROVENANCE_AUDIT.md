# E2-P2 Gate 1 Custom-NDK / CPython 3.14.5 Provenance Audit

> **Status:** FROZEN REPOSITORY AUDIT PASS
> **Repository input:** `agent/epoch2-p2-standalone-build-facade` at `16a0d6713eff05447b3b2e328581f6884a14c3e8`, tree `733f92196f4ea36e2029caf366da802513f6a30d`
> **Effect on E2-P2:** Gate 2 unblocked with unchanged Stage 3-B CPython 3.14.6 façade inputs

## Audit evidence

The read-only Termux collector produced:

```text
work ID   20260716-stage3-custom-ndk-python3145-audit-v1
archive   20260716-stage3-custom-ndk-python3145-audit-v1-results-20260716T151049Z.tar.zst
sha256    f24470ae0bb1450b1c555fbd63bbb9584c5e8dcc5fb72663075fda3de9c301b3
Drive ID  18nhxfAbbg5QYBKrGPMCwCRhr11WoA8Tx
matches   426 tracked lines across 126 tracked paths
```

The archive preserved repository identity, matched blob identities, matched tracked files, Stage 3 path inventory, and exact search output. Search results were treated as discovery input; the decision below is derived from the frozen machine authorities and independently audited Gate 4A lineage.

## Decision

Two different claims must remain separate.

```text
PROVEN
  CPython 3.14.5 was produced as the Stage 3-C Gate 4A second product with
  the exact preserved custom r27d Android-host NDK asset and ephemeral lld overlay.

NOT PROVEN, AND EXPLICITLY NOT ACCEPTED
  android-ndk-custom became the project-wide canonical NDK or replaced the
  frozen Stage 3-B CPython 3.14.6 workstation producer authority.
```

The custom-NDK use is therefore real but scoped. It is not a global toolchain transition.

## Exact custom-NDK authority

```text
authority class   scoped-exact-binary-producer-toolchain
scope             Stage 3-C Gate 4A second-product acquisition only
NDK revision      27.3.13750724
asset             android-ndk-r27d-aarch64-linux-android.tar.xz
asset size        156427268
asset sha256      7aac94c85931c698ef13f8679c3472d3d6c7a4566e4c8bff112be91aff527bd7
asset md5         ab87309abc53830892e0556b91438fa5
workflow run      29265009312
job               86867844060
producer commit   63b097b4db9b1d2ab445d6637eab16718f6c513b
```

The original r27d `lld` could not execute on the observed ARM64 Bionic host because its `PT_TLS.p_align` was 8. The accepted remediation was an ephemeral overlay; the installed NDK and original linker remained unchanged.

```text
original lld      cf9f6f56dfcb286d52425a73f5ba7c7a17966cc2c71bea0ccb0f16c21d07b15b
patch             ELF64 PT_TLS p_align, offset 392, 0x08 -> 0x40
patched lld       eee71a33b1c9924eeb576673d033008b1e520f84a112a7102cc9482142bf5a09
```

This authority is binary-defined. It does not claim source-rebuild reproducibility of `android-ndk-custom` or equivalence with the official Linux-host NDK binary set.

## CPython 3.14.5 producer and product identity

```text
source tag        v3.14.5
source commit     5607950ef232dad16d75c0cf53101d9649d89115
target            aarch64-linux-android
canonical host    aarch64-unknown-linux-android
Android API       24
NDK               27.3.13750724
SOABI             cpython-314-aarch64-linux-android
runtime fingerprint
                  6ce6e4cad493c1334fb10d893d7bcc6d49564cbe44081422ea346ce4c73ca537
A3 replay archive bfd241f959cb081a91f4866cb07cf2773d1028919de0ea0959ed0d95c8984202
A3 replay size    62379269
```

A6 independently froze the three-artifact product:

```text
runtime-base      d01e142dae90cdca8681c6674999acc197d05bb1bec9a75468fe9b8cf4fff52d
development-addon 623d776bd9a987aac0417c360746b4917d666a5829a522ef43574b66493387e0
test-addon        7d397ab12cf1d70b2922754b8121936ae56270c45c7929f69656984cd6a0eb1d
```

## Producer versus consumer evidence

Stage 3-D Gate 6 is not the compile-provenance authority. It proves that uv `0.11.28` can consume the already-frozen runtime-only product through an isolated local catalog entry keyed `cpython-3.14.5-linux-aarch64-none`.

The compile provenance comes from the Stage 3-C Gate 4A A2b exact-binary toolchain authority, A3 clean replay evidence, and A6 independent freeze. This resolves the earlier uncertainty without broadening the Gate 6 managed-Python claim.

## E2-P2 decision

The Gate 1 façade contract remains correct and unchanged:

```text
producer authority  docs/stages/STAGE3B_FINAL.md
product lock        config/products/cpython-3.14.6-aarch64-linux-android.lock.json
build steps         Stage 3-B prepare replay, run replay, product promotion,
                    and canonical launcher build
```

The scoped 3.14.5 custom-NDK authority does not supersede those tracked inputs. E2-P2 Gate 2 may proceed through the stable façade using the frozen Stage 3-B CPython 3.14.6 workstation producer. Its result must remain unqualified, unselectable, and unpublished until later qualification authority exists.

## Non-claims

This audit does not accept a real E2-P2 Gate 2 build, a real E2-P1 release envelope, Android or Termux qualification, selectability, publication, installer conversion, custom-NDK source rebuild reproducibility, or project-wide canonical promotion.
