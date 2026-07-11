# Stage 3-C Phase 1 Frozen `__phello__` Reassessment Result

> **Status:** PASS — isolated composition gate closed
> **Machine verifier:** 114/114
> **Corrected capability probes:** 17/17 × 4
> **Source and variant mutation:** PASS

## Accepted result

```text
schema version      1
check count       114
failed checks       []
missing outputs     []
parse errors        {}
pass              true
```

Reassessment return codes:

```text
corrected_capabilities          0
source_fingerprint_after        0
variant_fingerprints_after      0
```

## Retained first-run incident

The first isolated run remains preserved as evidence.

```text
first-run failed checks
  runtime-base_capability_pass
  runtime-development_capability_pass
  workflow_status_pass

first-run capability return code
  16

all first-run non-capability return codes
  0
```

Root cause:

```text
__phello__ is frozen into CPython and remains importable without the
physical lib/python3.14/__phello__ optional-source rows.
```

Corrected contract:

```text
frozen importability
  required in all variants

physical __phello__ source root absent
  runtime-base
  runtime-development

physical __phello__ source root present
  runtime-test
  runtime-supported
```

## Corrected variant capability matrix

```text
runtime-base
  capability       PASS
  entries          714
  __phello__       frozen
  physical root    absent

runtime-development
  capability       PASS
  entries          1168
  __phello__       frozen
  physical root    absent

runtime-test
  capability       PASS
  entries          2502
  __phello__       frozen
  physical root    present

runtime-supported
  capability       PASS
  entries          2956
  __phello__       frozen
  physical root    present
```

Every corrected capability probe passed 17/17 checks.

## Frozen identities

Canonical promoted source:

```text
entries
  3155

fingerprint
  5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c
```

Isolated variants:

```text
runtime-base
  9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796

runtime-development
  c310052378f2ab40041c8ed599c301fbe6778c139665496ddb9f8b8a9ec947c6

runtime-test
  da1627557907b417bea4b0175e431c746a450dbfa8f31698077853328a54835e

runtime-supported
  ea5930b2b0c0266b28efa0a66fb70267f8ecafe5c62a5c29c61f26cc05c20a64
```

Every before/after pair remained equal, and every current identity matched the retained first-run identity.

## Closed gate

The following claims are now closed:

```text
first-run failure is retained and exactly explained
physical component partition contains no test-addon path leakage
all four corrected capability matrices pass
runtime-base production smoke passes
native development addon compiles and imports a real extension
test addon runs a representative CPython regression test
all isolated variants remain byte/metadata stable
canonical promoted source remains unchanged
```

## Remaining Phase 1 gates

```text
runtime-base native closure
runtime-base 67/67 extension import sweep
runtime-base production-shape whole-prefix relocation
portable source/relocated product fidelity
canonical and runtime-base non-mutation during final validation
```

## Claim boundary

This result closes isolated physical composition and capability semantics.

It does not yet prove that the split `runtime-base` retains the frozen native closure or remains fully operational after a whole-prefix move. Those are the final Phase 1 validation gates.
