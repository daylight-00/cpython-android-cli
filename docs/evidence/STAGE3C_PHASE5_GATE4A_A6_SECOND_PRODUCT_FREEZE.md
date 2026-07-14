# Stage 3-C Phase 5 Gate 4A A6 Second-Product Freeze

> **Status:** GATE 4A SECOND PRODUCT FROZEN
> **Product:** CPython 3.14.5 / android24 / aarch64
> **Next boundary:** Gate 4 transition-policy design

## Final decision

The exact CPython 3.14.5 three-artifact product is accepted as the second complete frozen product authority.

```text
A6 result
  20260714-gate4a-a6-independent-freeze-candidate-v1-results-20260714T140413Z.tar.zst

size
  9,964 bytes

sha256
  4565b69e78c618f58fda59f928c086bbcf1cd02cfb28252f419e42e8cbc266aa

result index
  40/40 exact

A6 candidate
  18/18 PASS

archived independent verifier
  18/18 PASS

external archive audit
  28/28 PASS
```

The external audit recomputed archive safety and the self-excluding index, checked the exact repository state, rebound the A3/A4/A5 lineage, verified artifact and product identities, and inspected the previously open producer warnings.

## Frozen product identity

```text
Python             3.14.5
source commit      5607950ef232dad16d75c0cf53101d9649d89115
target             aarch64-linux-android
canonical host     aarch64-unknown-linux-android
Android API        24
NDK                 27.3.13750724
SOABI               cpython-314-aarch64-linux-android
runtime fingerprint 6ce6e4cad493c1334fb10d893d7bcc6d49564cbe44081422ea346ce4c73ca537
```

Frozen artifacts:

```text
runtime-base
  archive sha256   d01e142dae90cdca8681c6674999acc197d05bb1bec9a75468fe9b8cf4fff52d
  manifest sha256  2e5efbc9fe765c1b7a4d1bc7375a74d27bcf6d1a56557e3be11cffb9f451e815
  owned paths      714

development-addon
  archive sha256   623d776bd9a987aac0417c360746b4917d666a5829a522ef43574b66493387e0
  manifest sha256  30a840feb2922684604d87b206617243a4ddce2fdff10053c720a52bae5fc671
  owned paths      447
  structural refs  2

test-addon
  archive sha256   7d397ab12cf1d70b2922754b8121936ae56270c45c7929f69656984cd6a0eb1d
  manifest sha256  1d6f2c2fd48fa258f9fd982c84732118a012b977a50399395913d13e72c63877
  owned paths      1,785
  structural refs  2
```

The 2,946 owned paths are disjoint and use four non-owning structural namespaces.

## Lineage accepted by A6

```text
A3 clean replay authority                 accepted
A4 materializer                           25/25 PASS
A4 archived verifier                      26/27 FAIL — preserved false negative
A4 static adjudication                    26/26 PASS
A4 adjudication-result audit               9/9 PASS
A5 v1 false-negative diagnosis            18/18 PASS
A5 v2 candidate / verifier                10/10 / 41/41 PASS
A5 independent archive audit              34/34 PASS
A6 candidate / verifier                   18/18 / 18/18 PASS
A6 external archive audit                 28/28 PASS
```

## Producer warning dispositions

### HACL memzero fallback

In the exact CPython 3.14.5 A3 build, the warning originated from `Modules/_hacl/Lib_Memzero0.c:66`. On the accepted Android producer, `explicit_bzero` and `explicit_memset` were unavailable. The build therefore selected the upstream no-safe-memzero fallback path. The target configure and build completed, the HACL/hashlib extension surface loaded, and the selected offline hashlib test passed.

This behavior is accepted as part of the exact CPython 3.14.5 product. The freeze does **not** claim a platform-provided or cryptographically guaranteed secure-erasure primitive. Replacing the fallback requires a new producer authority and revalidation.

### Bundled libmpdec

The system libmpdec probe failed and CPython 3.14.5 built its upstream bundled libmpdec into `_decimal`. The target build completed and the isolated `_decimal` import passed.

This is accepted for the exact 3.14.5 authority. It is not a Python 3.16 compatibility claim; system libmpdec must be supplied before any Python 3.16 product authority.

## Transition boundary

Gate 4A is complete, so transition-policy design may now begin. No transition behavior is frozen by this decision. In particular, the following remain open:

```text
whole-product versus artifact-by-artifact ordering
mixed-product addon compatibility
cross-version collision and residual policy
product-lock and registry replacement semantics
upgrade and downgrade journaling
bidirectional recovery and second-recovery idempotence
post-transition runtime behavior
scenario count and acceptance thresholds
```
