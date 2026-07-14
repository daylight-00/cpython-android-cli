# Stage 3-C Phase 5 Gate 4A A2b Termux-Native Toolchain Authority Decision

> **Status:** A2b FROZEN PASS — A2 complete; A3 clean replay ready, not started
> **Claim class:** scoped exact-binary producer-toolchain authority

## Decision

Gate 4A accepts the captured Termux-native Android/Bionic aarch64 toolchain as the second-product A2b authority.

This is a scoped exception to the original workstation-only execution topology. It applies only to Gate 4A second-product acquisition. It does not rewrite or replace the frozen first-product Victor/Linux provenance, and it does not claim that the custom Android-host NDK binaries are byte-equivalent to the official Linux-host NDK distribution.

The accepted authority is binary-defined:

```text
NDK revision
  27.3.13750724

preserved asset
  android-ndk-r27d-aarch64-linux-android.tar.xz
  size    156427268
  sha256  7aac94c85931c698ef13f8679c3472d3d6c7a4566e4c8bff112be91aff527bd7
  md5     ab87309abc53830892e0556b91438fa5

project authority remote
  gdrive:HW-T/cpython-android-cli/authorities/gate4a/toolchains/
    android-ndk-custom/r27/android-aarch64

producer binding
  workflow run  29265009312
  job           86867844060
  commit        63b097b4db9b1d2ab445d6637eab16718f6c513b
```

The release archive and installed `$HOME/opt/android-ndk-r27d` tree match exactly across 14,802 entries. The exact asset is preserved under the project authority path with size, MD5, SHA-256 sidecar, and authority metadata read back after upload.

## Linker overlay authority

The original r27d `lld` cannot execute on the observed ARM64 Bionic host because its ELF `PT_TLS.p_align` is 8 while the loader requires at least 64.

The accepted remediation is an ephemeral overlay. The installed NDK and original linker remain unchanged.

```text
original lld sha256
  cf9f6f56dfcb286d52425a73f5ba7c7a17966cc2c71bea0ccb0f16c21d07b15b

single byte patch
  ELF64 PT_TLS p_align field
  offset 392
  0x08 -> 0x40

patched overlay lld sha256
  eee71a33b1c9924eeb576673d033008b1e520f84a112a7102cc9482142bf5a09
```

The overlay was reproduced independently and selected by the exact CPython v3.14.5 `Android/android-env.sh` compiler driver. It passed C link/run, shared-library link, C++ link/run, target ELF inspection, and original-linker non-mutation checks.

## Evidence sequence

```text
initial Termux toolchain census
  9721c17248b181a934acdf28204df51b7fe3ac308239fed41265948f1ff5b45d
  diagnostic FAIL preserved: original r27d lld cannot execute

r27d linker diagnostic
  b9a0c998b4a3059be80f93f5808e547141937920ce64a08910113fb81e80f2d3
  13/13 capture PASS; 39/39 verifier PASS

overlay witness
  d71828ede5925d550000666f0a86906682bed8b9c3dca1d004bc4cda2cb1fb59
  38/38 capture PASS; 31/31 verifier PASS

initial provenance capture
  585fdca325a621eb580e8f56016d1e389ca58a2713fe08fa3a2873fafb38284c
  diagnostic FAIL preserved: stale mutable-release tag was mistaken for producer commit

corrected producer binding and preservation
  bba0ea4c8df4115fee0c5a5c24c33cfa1114f5acf81a1644cfdeeb4810715a2e
  32/32 binding PASS; 27/27 verifier PASS; preservation PASS

combined external audit
  46/46 PASS
```

Machine audit:

```text
docs/evidence/STAGE3C_PHASE5_GATE4A_A2B_TERMUX_NATIVE_TOOLCHAIN_EXTERNAL_AUDIT.json
sha256  5f44ce69e3fa8db5da661fbbc85cef13e58cf58ca3457497134526d9f9b2fc13
```

## Acceptance boundary

A2b accepts:

```text
exact preserved custom r27d binary asset
installed NDK tree identity
producer workflow run, job, commit, and fetched recipe snapshot
Android SDK path and observed components
exact compiler, linker, make, host Python, and relevant host-tool identities
ephemeral linker overlay recipe and resulting identity
exact v3.14.5 android-env selection
C, shared-library, and C++ mechanical witnesses
```

A2b does not accept:

```text
source-rebuild reproducibility of android-ndk-custom
equivalence to the official Linux-host NDK binary set
mutation of the installed NDK
A3 clean replay or any CPython product artifact
A4 through A6
upgrade, downgrade, compatibility, migration, or recovery behavior
```

The upstream custom-NDK recipe uses mutable release assets and does not digest-pin every upstream builder input. Those limitations are explicit. The project authority is therefore the exact preserved binary asset plus the exact overlay recipe, not a source-rebuild claim.

## Gate state

```text
A1  selection and repository design          DESIGN FROZEN
A2  exact input and toolchain capture         FROZEN PASS
  A2a immutable remote inputs                 FROZEN PASS
  A2b Termux-native binary toolchain          FROZEN PASS
A3  clean upstream Android replay             READY — not started
A4  three-artifact materialization            pending
A5  standalone Termux validation              pending
A6  independent archive audit and freeze      pending
```

Gate 4 transition design remains closed until A6 freezes the complete second-product authority.
