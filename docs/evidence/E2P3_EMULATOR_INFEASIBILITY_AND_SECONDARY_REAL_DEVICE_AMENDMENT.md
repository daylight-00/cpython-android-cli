# E2-P3 Emulator Infeasibility and Secondary Real-Device Amendment

## Accepted facts

The primary Galaxy S22 Ultra profile is already frozen at 35/35 qualification, 19/19 result verification, and 38/38 independent review.

A first attempt to execute the emulator package on the physical S22 Ultra failed correctly at `android_emulator` preflight. Its complete result archive is retained as negative evidence:

```text
result archive SHA-256  ff30d1ddc9be0102c9daf759e6a0b1bed08cf334edfe6a042f9a6959b4c57e73
repository HEAD         c05cf9b608b69903aabaf42047cfa921276a6069
repository tree         8ed6e6ed6b00378324d6774132e211353b7caa75
observed device          real / qcom / aarch64 / API 36
```

The available x86_64 Linux workstation successfully created an API 36 ARM64 AVD definition, but Android Emulator QEMU2 rejected it before boot:

```text
host architecture       x86_64
AVD ABI                  arm64-v8a
AVD CPU                  arm64
Android Emulator         36.6.11.0
failure                  ARM64 AVD not supported on x86_64 QEMU2 host
negative archive SHA-256 74523e3743353cb83a750ab4ae7606213ef276568fafba9e4e697d057d5302fe
```

The x86_64 AVD can boot and exposes QEMU/ranchu identity, but it cannot natively qualify the frozen aarch64 product. Thus neither available AVD path can produce the intended authority.

## Replacement evidence target

The Galaxy Note9 is accepted as an independent secondary real-device environment:

```text
machine     aarch64
ABI         arm64-v8a,armeabi-v7a,armeabi
API         29
Android     10
hardware    samsungexynos9810
qemu        0
kernel      4.9.118-24343300
prefix      /data/data/com.termux/files/usr
```

This environment adds meaningful product evidence across Android generation, Bionic/kernel generation, SoC vendor, and physical-device instance. It does not establish emulator behavior.

## Claim boundary

```text
primary real-device authority        frozen
secondary real-device authority      not yet executed
emulator authority                   waived and unclaimed
dual-real-device acceptance          not yet claimed
original real+emulator acceptance    unmet
selectability                        false
publication                          prohibited
```
