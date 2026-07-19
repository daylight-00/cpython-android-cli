# Current Project Context

> **Current epoch:** Epoch 2
> **Current phase:** E2-P3 secondary real-device amendment frozen
> **Next phase:** qualify the same frozen envelope on the Exynos 9810 Galaxy Note9 / Android API 29
> **Frozen predecessor:** Epoch 1 through Stage 3-F
> **Epoch 1 predecessor commit:** `e1de252740a96c40f3d587269136235a2c84ea16`
> **Epoch 2 Phase 0 commit:** `a34e5fdc6224e66aa7ed335e921780fbadd728dc`
> **Epoch 2 Phase 1 commit:** `68828691fcae382cf49b9dbc2b5231f9e21f9282`
> **Primary target:** Android/Bionic arm64, `aarch64-linux-android`, API 24+
> **Primary execution profile:** `termux-cli`

## Frozen E2-P1 artifact contract

```text
contract version       1
primary flavor         install_only_stripped
archive format         pax-tar+zstd
archive/install root   python/
payload classes        runtime + development
excluded classes       tests + build + debug_symbols
target triple          aarch64-linux-android
Android ABI            arm64-v8a
minimum API            24
wheel platform         android_24_arm64_v8a
primary profile        termux-cli
```

## Frozen E2-P2 Gate 1 façade

```text
stable command
  components/standalone/bin/cpython-android-standalone

operations
  plan
  build
  package
  verify --scope repository
  verify --scope envelope
```

Gate 1 remains frozen as historical repository and synthetic-envelope authority. The current façade is explicitly bound to the frozen Termux-native producer authority without rewriting Gate 1.

## Frozen Termux-native CPython 3.14.6 producer authority

```text
Python              3.14.6
source commit       c63aec69bd59c55314c06c23f4c22c03de76fe45
target              aarch64-linux-android
canonical host      aarch64-unknown-linux-android
Android API         24
NDK                 27.3.13750724
SOABI               cpython-314-aarch64-linux-android
package SHA-256     517f4b0d113c4c1cf6931c230b6b517bee7a2b7f8b4f0f099a148260fa3ac8e7
prefix snapshot     3081a1b150473ff6d6896589a2898cb38baf831e0f811af2bd0447c29b36bb89
```

Frozen three-artifact set:

```text
runtime-base        7119e97cb43fb19ef4dce3eec145bb867b8070b9f8b7772c74a5885f4fe53c03
development-addon   73dc90a8ead6c58d040a2fc31386f1c00ff38ce84fd4507229e8e9bc18902b6f
test-addon          5bb4c1a45a2c04031c8c8c1a0be05fc02ad4653f21492b63559039105be5ce03
```

Accepted evidence:

```text
clean replay core                 33/34 plus canonical-host adjudication
canonical identity adjudication   24/24 + 10/10
materialization core              25/25
materialization adjudication      23/23 + 12/12
standalone candidate              10/10
standalone verifier               41/41
standalone invariant closure      21/21
façade invariant closure          24/24 before and after
custom-NDK invariant closure      49/49 before and after
external freeze audit             23/23
```

## Frozen bound façade execution authority

```text
execution input commit   863dccbb31acf4ffe32dd0e26630dd861f96d992
execution input tree     560267eb71d3a26dab019802f0dd2427fe81a774
artifact id              cpython-3.14.6-aarch64-linux-android24-install_only_stripped
envelope archive         66c2a39b7164701d3a14cff538be298abcf30c696150f6abf7785e212c1b4727
release index            64825d3afabbda7c90992debfb11e771baeff5514f2b6e6d13584dc7ac6fcf85
private authority index  5fd8c03b53bcb749cfa221277e75f16b2392e6cec3a184b716f98e24d84fe0b5
manifest entries         1169
stripped ELF objects     81
canonical/replay         8/8 files byte-identical
repository verifier      20/20 before and after
envelope verifier        52/52 canonical and replay
independent review       27/27
```

The real stable façade `build` and `package` operations completed on the canonical Termux host. The private authority stores the exact unqualified E2-P1 envelope and supporting receipts. This is an execution and static-review authority, not target qualification, selectability, or publication authority.

## Frozen E2-P3 qualification contract

```text
stable command          components/standalone/bin/cpython-android-qualify
contract version        1
static checks           9
termux-real checks      35
termux-emulator checks  35
result verifier         19
regression              21/21 after harness correction
static replay           9/9 + 19/19
```

The contract consumes the frozen private envelope without rerunning E2-P2. Gate 1 freezes design and harness behavior only; no Android target evidence is claimed.

## Frozen E2-P3 qualification harness correction

The first real-Termux execution reached 33/35. `venv_relocation` followed a normal venv symlink during path containment, and `wheel_tag_android24` queried pip from the intentionally pip-free base runtime. Both were harness false negatives. The corrected harness uses lexical venv identity and reads wheel tags from pip inside the created venv. The 35-check target matrix and frozen product bytes are unchanged. No target profile is qualified by this correction.

## Frozen E2-P3 real Termux qualification authority

The corrected `termux-real` retry consumed the exact frozen E2-P2 private envelope without rebuilding or repackaging it. The complete result archive was audited independently and promoted to the E2-P3 target-authority namespace.

```text
profile                       termux-real
device                        real Android / Termux / aarch64
Android API                   36
qualification                 35/35
result verifier               19/19
independent review            38/38
result archive SHA-256        b92b041b78b21e0a3b402e54a15e008008db13320a264284d604f39046907e0b
target authority index        9fbd2ce1f9c288bcdb92b19c0fffce24086671d40b2cce658f524935ad473ab1
selectable                    false
```

The accepted target result proves only the individual real-Termux profile. Emulator qualification, combined acceptance, metadata finalization, selectability, publication, installer conversion, and transition behavior remain open.

## Frozen E2-P3 secondary real-device amendment

The primary real-device authority was produced on the Samsung Galaxy S22 Ultra:

```text
machine        aarch64
ABI            arm64-v8a
Android API    36
Android        16
hardware       qcom
kernel         5.10.236-android12-9-31998796-abS908NKSS9GZE5
qemu           0
```

The original second target was an ARM64 Android Emulator. The available Linux workstation is x86_64. Its x86_64 AVD boots but cannot natively qualify the frozen aarch64 product, while the ARM64 AVD is rejected by Android Emulator QEMU2 before boot because the guest architecture does not match the host. The emulator objective is therefore explicitly waived, not passed.

E2-P3 now substitutes an independent second physical-device run on the Samsung Galaxy Note9 / Exynos 9810:

```text
profile authority              termux-real-secondary-exynos9810-api29
qualifier execution profile    termux-real
machine                        aarch64
ABI                            arm64-v8a
Android API                    29
Android                        10
hardware                       samsungexynos9810
kernel                         4.9.118-24343300
qemu                           0
qualification matrix           unchanged 35 checks
selectable                     false
```

This amendment preserves the original contract as historical authority and does not claim emulator coverage. If the Note9 run passes, E2-P3 may claim dual-real-device aarch64 Termux compatibility across API 29 and API 36, but not real-plus-emulator acceptance.

## Current claim boundary

```text
producer authority          frozen
three-artifact authority    frozen
standalone Termux           accepted
façade producer binding     frozen
bound façade execution      frozen
real E2-P1 envelope         frozen — unqualified
static envelope review      frozen — 52/52 + 27/27
E2-P3 contract              frozen
qualification harness        correction frozen
real Termux qualification    frozen — 35/35 + 19/19 + 38/38
emulator qualification       waived — infrastructure infeasible; not claimed
secondary real qualification next — Note9 / Exynos 9810 / API 29
dual-real-device acceptance  not yet claimed
original combined acceptance not claimed
selectability                false
publication                 not permitted
transition behavior         not reopened
```

## Immediate reading path

1. [`contracts/E2P3_SECONDARY_REAL_DEVICE_AMENDMENT.md`](contracts/E2P3_SECONDARY_REAL_DEVICE_AMENDMENT.md)
2. [`evidence/E2P3_EMULATOR_INFEASIBILITY_AND_SECONDARY_REAL_DEVICE_AMENDMENT.md`](evidence/E2P3_EMULATOR_INFEASIBILITY_AND_SECONDARY_REAL_DEVICE_AMENDMENT.md)
3. [`handoff/2026-07-18-e2p3-secondary-real-device-amendment.md`](handoff/2026-07-18-e2p3-secondary-real-device-amendment.md)
4. [`evidence/E2P3_REAL_TERMUX_ARCHIVE_QUALIFICATION_AUTHORITY_FREEZE.md`](evidence/E2P3_REAL_TERMUX_ARCHIVE_QUALIFICATION_AUTHORITY_FREEZE.md)
5. [`handoff/2026-07-18-e2p3-real-termux-archive-qualification-authority-freeze.md`](handoff/2026-07-18-e2p3-real-termux-archive-qualification-authority-freeze.md)
6. [`evidence/E2P3_ARCHIVE_QUALIFICATION_HARNESS_CORRECTION.md`](evidence/E2P3_ARCHIVE_QUALIFICATION_HARNESS_CORRECTION.md)
7. [`contracts/E2P3_ARCHIVE_QUALIFICATION_CONTRACT.md`](contracts/E2P3_ARCHIVE_QUALIFICATION_CONTRACT.md)
8. [`../experiments/epoch2-archive-qualification/`](../experiments/epoch2-archive-qualification/)
9. [`evidence/E2P2_TERMUX_NATIVE_CPYTHON3146_FACADE_EXECUTION_AUTHORITY_FREEZE.md`](evidence/E2P2_TERMUX_NATIVE_CPYTHON3146_FACADE_EXECUTION_AUTHORITY_FREEZE.md)
10. [`roadmap/EPOCH2_ROADMAP.md`](roadmap/EPOCH2_ROADMAP.md)
11. [`epochs/EPOCH2_CHARTER.md`](epochs/EPOCH2_CHARTER.md)

## Next bounded gate

Run only the secondary physical-device qualification package on the Exynos 9810 Galaxy Note9. It must preflight the exact Note9 identity and then invoke the unchanged `termux-real` 35-check matrix against the exact same private envelope. Do not rerun producer/build/package or the accepted S22 Ultra profile. Keep dual-real-device closure, metadata finalization, selectability, publication, installer conversion, transition behavior, and the post-E2-P3 scope redesign separate.
