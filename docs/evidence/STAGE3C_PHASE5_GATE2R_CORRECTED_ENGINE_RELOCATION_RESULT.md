# Stage 3-C Phase 5 Gate 2R Corrected-Engine Relocation Result

> **Status:** FROZEN PASS
> **Target:** Termux on Android arm64
> **Accepted evidence:** complete independently inspected TGZ

## Archive identity

```text
archive
  stage3c-phase5-gate2r-corrected-engine-relocation-results-20260712-202419.tgz

sha256
  8e2c131567d78a4208e7c8eb02e783a479713f6d867a3e5cd98eae60aa5738a7

size
  72,501,453 bytes

members
  1,727

regular files / directories
  1,596 / 131

unsafe / link / special entries
  0 / 0 / 0
```

## Result-index authority

```text
root result-index sha256
  69734a0ba286b9d6b55e8ef4c364dca7cb80bd380080cd6653038040ac51650c

root indexed files
  1,576/1,576 exact

accepted Gate 3A result-index sha256
  a161eedeebd086b1be6f115671312b463ed1eb9969c4494cae1bdbb626794128

accepted Phase 4 result-index sha256
  878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce

nested result indices
  19/19 exact
```

Every index had zero hash, size, mode, missing, duplicate, target, type, or coverage mismatches.

## Verification

```text
Gate 2R authority verifier
  15/15 PASS

historical relocation verifier
  46/46 PASS

Gate 1 at location A
  80/80 PASS

Gate 1 at location B
  80/80 PASS

workflow return codes
  all 0

wrapper return code
  0
```

## Corrected-engine authority

```text
recovery_engine_missing_leaf.py sha256
  33b55d94714fb96f401caefe0e72d6587da955a9d0c201f4eb18dfc5193eb87a

recovery_operations_missing_leaf.py sha256
  61d20c68c7c5234a00328104914b83adc69859acca9791f3b14d9ff969e24021
```

Temporary runtime patch authority:

```text
baseline SCRIPT_DIR preservation         1
relocation SCRIPT_DIR preservation       1
baseline engine override                 1
relocation engine override               1
baseline runner override                 1
corrected engine forwarding to baseline  1
```

Fresh location-A installation used the corrected engine:

```text
create actions
  714

mutation count
  715
```

## Complete-root relocation

```text
same filesystem
  true

source / destination device
  65082 / 65082

source / relocated inode
  2497225 / 2497225

inode preserved
  true

location A absent
  true

location B present
  true
```

Complete-root identity at A, B immediately after the move, and B after all probes:

```text
entries
  719

directories / regular / symlink / special
  60 / 656 / 3 / 0

fingerprint
  aea9a035d55530ab513458f43dbf7604a1f6aa9628eae4218dd050e688c14a30
```

Installed payload identity:

```text
portable entries
  714 / 714 / 714

portable fingerprint
  f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978

strict entries
  714 / 714 / 714

strict fingerprint
  3d61c27a3943930e53ac30035a2c4b77932cfabd17e4994f6370a30408a034f3

strict pycache / special paths
  0 / 0
```

Registry bytes were exact across the move with one artifact and 714 owned rows. The stale-location scan found zero regular-file, symlink, or probe references to location A.

## Destination runtime

```text
Python
  3.14.6

platform / machine
  android / aarch64

SOABI
  cpython-314-aarch64-linux-android

MULTIARCH
  aarch64-linux-android

HTTPS
  200

uv venv / uv run
  PASS / PASS

native closure
  81 ELF / 329 edges / 0 unresolved

classification
  80 RUNTIME_INTERNAL / 249 ANDROID_SYSTEM

system SONAME
  5/5

extension imports
  67/67

engine verify
  1 artifact / 714 owned rows / 0 bad paths
```

## Wrapper-log note

The stored wrapper log omitted some final human-readable Gate 2R marker lines because the wrapper copied a process-substitution `tee` log before the asynchronous writer had fully flushed. This does not affect acceptance: wrapper status, workflow status, both verifiers, all raw machine evidence, and the archive result-index are complete and PASS. Future wrappers must use synchronous log capture before packaging.

## Claim boundary

This PASS proves same-filesystem rename-style relocation of a complete installation root created and verified with the accepted corrected engine, including ownership and recovery state, and full destination runtime revalidation.

It does not prove cross-filesystem relocation, preservation boundaries, addon lifecycle, uninstall, upgrade, or downgrade.
