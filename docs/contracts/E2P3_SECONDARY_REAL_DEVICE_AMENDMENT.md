# E2-P3 Secondary Real-Device Amendment

> **Status:** FROZEN — secondary Note9 qualification next
> **Amendment version:** 1
> **Original contract:** preserved unchanged as `E2P3_ARCHIVE_QUALIFICATION_CONTRACT.md`

## Decision

E2-P3 originally required independent `termux-real` and `termux-emulator` executions of the same frozen aarch64 archive. The real-device profile passed in full on the Galaxy S22 Ultra. The emulator profile cannot be executed with product fidelity using the available infrastructure:

- the available workstation is x86_64;
- its x86_64 Android AVD cannot natively execute the frozen aarch64 product;
- its ARM64 AVD is rejected by Android Emulator QEMU2 before boot because the guest and host architectures differ;
- a physical Android device must not be relabeled as an emulator.

The emulator objective is therefore waived from E2-P3 closure and remains explicitly unclaimed. It is replaced with an independent secondary physical-device profile.

## Frozen primary environment

```text
device          Samsung Galaxy S22 Ultra
profile         termux-real primary
machine         aarch64
ABI             arm64-v8a
Android API     36
Android         16
hardware        qcom
kernel          5.10.236-android12-9-31998796-abS908NKSS9GZE5
qualification   35/35
result verifier 19/19
independent     38/38
```

## Replacement secondary environment

```text
device                     Samsung Galaxy Note9
SoC                        Exynos 9810
authority profile          termux-real-secondary-exynos9810-api29
qualifier execution        termux-real
machine                    aarch64
ABI                        arm64-v8a,armeabi-v7a,armeabi
Android API                29
Android                    10
hardware                   samsungexynos9810
kernel                     4.9.118-24343300
qemu                       0
Termux prefix              /data/data/com.termux/files/usr
```

The target wrapper must fail closed unless every identity above matches. After preflight, it invokes the existing stable qualifier with `--profile termux-real`. No product bytes, checks, evidence classes, harness semantics, or frozen E2-P2 authority are changed.

## Unchanged qualification matrix

The secondary execution uses the exact existing 35-check `termux-real` matrix and 14 evidence files. In particular, the expected wheel platform remains `android_24_arm64_v8a`; the host API 29 does not change the frozen product minimum API identity.

## Closure policy

E2-P3 may proceed to a separate closure only after both physical-device authorities are frozen:

```text
primary    Galaxy S22 Ultra / API 36 / qcom
secondary  Galaxy Note9 / API 29 / Exynos 9810
```

The resulting claim is limited to dual-real-device aarch64 Termux compatibility. It is not emulator qualification, real-plus-emulator combined acceptance, selectability, publication readiness, or installer authority.

## Prohibited shortcuts

- do not weaken the emulator preflight and call a physical device an emulator;
- do not execute the aarch64 product in an x86_64 AVD through translation and treat it as native authority;
- do not rerun producer, build, package, or the accepted primary profile;
- do not set `selectable=true`;
- do not start metadata finalization or E2-P4.
