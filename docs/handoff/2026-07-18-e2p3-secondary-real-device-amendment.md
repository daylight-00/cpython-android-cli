# Handoff — E2-P3 Secondary Real-Device Amendment

## Frozen repository boundary

This transaction changes only E2-P3 governance and documentation. The original archive qualification contract, stable qualifier, result schema, 35-check matrix, frozen envelope, primary result, and target authorities remain byte-identical.

## Decision

The native ARM64 emulator objective is waived because the available x86_64 workstation cannot boot the ARM64 AVD, while the bootable x86_64 AVD cannot natively qualify the aarch64 product. The waiver is explicit and carries no emulator claim.

The replacement is a secondary physical-device qualification on:

```text
Samsung Galaxy Note9
Exynos 9810
Android API 29 / Android 10
aarch64 / arm64-v8a
hardware=samsungexynos9810
qemu=0
kernel=4.9.118-24343300
```

## Next bounded action

Execute only the Note9 secondary physical-device package. It must:

1. verify the exact repository commit/tree produced by this transaction;
2. verify exact Note9 host identity before acquiring authority;
3. consume the existing E2-P2 private envelope without build or package work;
4. invoke the unchanged stable qualifier as `--profile termux-real`;
5. require 35/35 qualification, 19/19 result verification, and independent target review;
6. promote to a secondary-device-specific authority namespace;
7. preserve `selectable=false`;
8. upload complete PASS-or-FAIL evidence.

Do not rerun the S22 Ultra profile. Do not claim emulator or combined real-plus-emulator acceptance. Do not open metadata finalization, publication, installer conversion, E2-P4, or the post-E2-P3 scope redesign.
