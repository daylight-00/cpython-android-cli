# Stage 3-C Phase 1 Runtime-Base Final Validation Result

> **Status:** PASS — final Phase 1 product gate closed
> **Target:** Termux on Android arm64
> **Validated product:** 714-entry `runtime-base`
> **Result archive:** `stage3c-phase1-runtime-base-final-validation-results-20260711-193213.tgz`

## Result archive identity

```text
sha256
  7b8b23b04d4e4a120a42e028d79478de01e409b1d5b0a4cd6436ec2aecbcbc49
```

The uploaded TGZ was independently extracted and inspected. It contains the complete final-validation result tree, including accepted input evidence, closure inventories, extension probes, relocation logs, portable-fidelity manifests, mutation controls, and aggregate verifiers.

## Aggregate result

```text
final verifier
  schema_version    1
  check_count      47
  failed_checks    []
  missing_outputs  []
  parse_errors     {}
  pass             true

workflow return codes
  input_verification                0
  closure_workflow                  0
  closure_verification              0
  relocation_workflow               0
  relocation_engine_verification    0
  relocation_verification           0
```

Sub-verifiers:

```text
final input contract                 47/47 PASS
runtime-base closure                 63/63 PASS
Stage 3-B relocation engine          31/31 PASS
Stage 3-C relocation wrapper         60/60 PASS
```

## Accepted identities

Runtime-base:

```text
entries
  714

type counts
  directories   57
  regular      654
  symlinks       3
  special        0

strict fingerprint
  9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796
```

Canonical promoted source:

```text
entries
  3155

type counts
  directories   216
  regular      2934
  symlinks         5
  special          0

strict fingerprint
  5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c
```

Both trees remained unchanged during closure and relocation validation. No `__pycache__` or special-file path was introduced.

## Native closure

```text
runtime-base file entries             714
symlinks                                 3
ELF objects                             81
objects with DT_NEEDED edges            81
DT_NEEDED edges                        329
unique needed SONAMEs                    9

classification edges
  ANDROID_SYSTEM                       249
  RUNTIME_INTERNAL                      80

classification unique SONAMEs
  ANDROID_SYSTEM                         5
  RUNTIME_INTERNAL                       4

unresolved edges                         0
inspection errors                        0
mutation check                        PASS
```

The split removed development, test, and unsupported GUI source without weakening the frozen native graph.

## Android-system providers

```text
unique Android-system SONAMEs    5
dlopen PASS                      5
dlopen FAIL                      0
```

Provider ambiguity remains diagnostic and non-gating:

```text
ambiguous provider SONAMEs       8
```

The accepted gate is the exact edge classification and successful fresh-process `dlopen` result.

## Extension surface

```text
extension candidates     67
isolated import PASS     67
isolated import FAIL      0
extension discovery       sys.path
```

The discovered extension directory is inside the isolated runtime-base:

```text
work/termux/stage3c-phase1-isolated-variants/runtime-base/prefix/
  lib/python3.14/lib-dynload
```

## Production-shape relocation

The runtime-base was copied to location A, validated, moved as a whole prefix to location B, and validated again.

Accepted markers:

```text
LOCATION_RECONFIRM[A]=PASS
VENV_RECONFIRM=PASS
UV_RUN_RECONFIRM=PASS
LOCATION_RECONFIRM[B]=PASS
VENV_RECONFIRM=PASS
UV_RUN_RECONFIRM=PASS
STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS
STAGE3A_PRODUCTION_RELOCATION_RECONFIRM=PASS
```

HTTPS returned status 200 at both locations.

The Stage 3-B relocation verifier passed unchanged:

```text
schema_version    2
check_count      31
failed_checks    []
missing_outputs  []
parse_errors     {}
pass             true
```

## Relocated-product fidelity

```text
source entries               714
relocated entries            714
added paths                    0
removed paths                  0
strict changed paths           0
portable changed paths         0
pycache paths                  0
strict pass                 true
portable pass               true
```

Portable source/B fingerprint:

```text
5e3a46e454163b35f1c3bca6c381253fe0e025695f67fe874deedea006034fab
```

The source and relocated portable fingerprints are identical.

## Phase 1 closed claims

The accepted evidence proves:

```text
every canonical promoted path has an explicit component
selected distributable component paths are complete and non-overlapping
unsupported Tk/IDLE/turtle source is excluded
runtime-base contains exactly 714 entries
runtime-base production smoke passes
HTTPS, subprocess, uv venv and uv run pass
native development addon compiles and imports a real extension
test addon runs a representative CPython regression test
frozen __phello__ semantics are separated from physical source ownership
runtime-base retains all 81 ELF objects and 329 native dependency edges
unresolved native edges remain zero
all 67 extension imports pass
runtime-base survives whole-prefix relocation A -> B
stale A-prefix assertions pass
source/B portable product fidelity is exact
runtime-base and canonical promoted source remain unchanged
```

## Claim boundary

This result does **not** prove or freeze:

```text
archive envelope and root layout
manifest schema
archive byte reproducibility
mtime/uid/gid/archive-header normalization
compression algorithm and parameters
archive extraction safety policy
installed ownership registry
collision and same-version reinstall behavior
upgrade, downgrade and rollback transactions
uninstall and interrupted-operation recovery
release signing or publication
```

Those are Stage 3-C Phase 2 and later contract questions. Packaging must consume the frozen Phase 1 component and product identities rather than reopening them.
