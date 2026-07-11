# Stage 3-C Phase 1 Isolated Variant `__phello__` Incident

> **Status:** FIRST RUN RETAINED — verifier false negative diagnosed
> **Physical gates:** PASS
> **Corrected capability reassessment:** ACTIVE

## First-run machine result

```text
verification schema       1
verification checks      46
failed checks             3
missing outputs           0
parse errors              0
pass                  false
```

Exact failed checks:

```text
runtime-base_capability_pass
runtime-development_capability_pass
workflow_status_pass
```

Workflow return codes:

```text
capabilities                              16
runtime_base_smoke                         0
development_extension_compile              0
development_extension_import               0
test_addon                                 0
fidelity_after                             0
runtime_base_fingerprint_after             0
runtime_development_fingerprint_after      0
runtime_test_fingerprint_after             0
runtime_supported_fingerprint_after        0
source_fingerprint_after                   0
```

The aggregate workflow failure was therefore caused only by the capability probe return code.

## Physical product gates that passed

```text
materialization                      7/7 PASS
initial exact-path fidelity         15/15 PASS
final exact-path fidelity           15/15 PASS
runtime-base production smoke             PASS
development extension compile/import      PASS
test-addon representative test            PASS
canonical source mutation control         PASS
all four variant mutation controls        PASS
```

Canonical source before/after:

```text
entries
  3155 / 3155

fingerprint
  5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c
```

Variant identities:

```text
variant               entries   regular bytes   portable manifest                                                  strict fingerprint
runtime-base              714      38,759,749   c3022b58638bfe37905a5379f70831945286d89932fbcb2d9871a6a1def5ccc7   9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796
runtime-development      1168      43,733,124   32581362216f98b6d2c5de5289e9fe1609ee6fd734601df0f2c9974883d05220   c310052378f2ab40041c8ed599c301fbe6778c139665496ddb9f8b8a9ec947c6
runtime-test             2502      72,236,539   e8a83eba50ff9d499c6e07deffe820f8c3c0f9e2b4c4f610f165e07bdbde4b5b   da1627557907b417bea4b0175e431c746a450dbfa8f31698077853328a54835e
runtime-supported        2956      77,209,914   bd10ec44bcc86641a254bf52f8bf5177a2851111d3d63aee186c9038cbacb077   ea5930b2b0c0266b28efa0a66fb70267f8ecafe5c62a5c29c61f26cc05c20a64
```

Every before/after strict fingerprint pair was equal.

## Runtime-base smoke result

```text
CPython                 3.14.6
runtime prefix          isolated runtime-base
HTTPS status            200
SSL_CERT_FILE           Termux CA bundle
uv venv                 PASS
venv base_prefix        isolated runtime-base
uv run + anyio          PASS
STAGE2C_SMOKE            PASS
```

The uv hardlink fallback warning is non-gating. Installation completed and the uv-run base identity remained the isolated runtime-base prefix.

## Development-addon result

A real extension was compiled with Termux clang against the isolated development headers and `libpython3.14` surface.

```text
clang
  /data/data/com.termux/files/usr/bin/clang

extension
  stage3c_devprobe.cpython-314-aarch64-linux-android.so

import result
  DEV_EXTENSION_RESULT=42
```

## Test-addon result

```text
representative file       test_json
result                    SUCCESS
files                     1/1
individual tests          218
skipped                   37
marker                    STAGE3C_TEST_ADDON_REPRESENTATIVE=PASS
```

## Exact capability failure

`runtime-base` and `runtime-development` each failed only:

```text
module_expectations_match
```

All module expectation entries were true except:

```text
__phello__ = false
```

The probe expected `__phello__` import to fail when `OPTIONAL_TEST_DEMO` physical rows were absent. The observation contradicted that expectation:

```text
success          true
spec found       true
spec origin      frozen
module file      <variant>/prefix/lib/python3.14/__phello__/__init__.py
```

The reported `module_file` is a synthetic stdlib source location associated with the frozen module. It does not prove the physical path exists.

The exact-path materialization and fidelity evidence independently proved that:

```text
runtime-base
  OPTIONAL_TEST_DEMO rows absent

runtime-development
  OPTIONAL_TEST_DEMO rows absent

runtime-test
  OPTIONAL_TEST_DEMO rows present

runtime-supported
  OPTIONAL_TEST_DEMO rows present
```

Therefore there was no path leakage from the test addon.

## Root cause

`__phello__` is compiled into this CPython as a frozen package. Its importability is runtime capability and is independent of the optional physical `lib/python3.14/__phello__` source tree.

The first probe incorrectly used:

```text
__phello__ import success
  ==
OPTIONAL_TEST_DEMO physical ownership
```

That equivalence is false.

## Corrected contract

Import contract:

```text
__phello__ imports in every variant
__phello__ spec origin is frozen in every variant
```

Physical payload contract:

```text
lib/python3.14/__phello__ absent
  runtime-base
  runtime-development

lib/python3.14/__phello__ present
  runtime-test
  runtime-supported
```

Physical ownership remains enforced by the component manifest and exact-path fidelity verifier. It is no longer inferred from frozen-module importability.

## Targeted reassessment

The corrected workflow does not rematerialize the variants and does not overwrite the first-run results.

```sh
bash \
  experiments/stage3c-product-role-inventory/run-isolated-variant-capability-reassessment.sh
```

It requires:

```text
first-run failed-check set exact
first-run capability return code exactly 16
all first-run non-capability return codes zero
materialization 7/7 retained
fidelity before/after 15/15 retained
first-run source/variant fingerprints unchanged
current source/variant fingerprints equal first-run identities
corrected capabilities 17/17 for all four variants
__phello__ frozen origin in all variants
physical __phello__ root state follows test-addon ownership
source/variant fingerprints unchanged by reassessment
```

Expected markers:

```text
FIRST_RUN_FAILURE_PRESERVED=PASS
PHELLO_FROZEN_CONTRACT_CORRECTED=PASS
ISOLATED_VARIANT_CAPABILITIES_REASSESSED=PASS
ISOLATED_VARIANT_REASSESSMENT_MUTATION_CHECK=PASS
STAGE3C_PHASE1_PHELLO_REASSESSMENT=PASS
```

## Claim boundary

The first run proves the physical split, production runtime smoke, native-development composition, representative test execution, exact fidelity, and non-mutation.

It does not itself prove the original capability expectation set because that set contained a false frozen-module assumption.

A corrected reassessment PASS will close that semantic false negative without discarding or rewriting the first-run evidence. Native closure and production-shape relocation remain subsequent gates.
