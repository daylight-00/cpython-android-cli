# Stage 3-C Phase 5 Gate 3 Handoff — 2026-07-12

> **Repository:** `daylight-00/cpython-android-cli`
> **Target:** Termux on Android arm64
> **Current boundary:** Gate 3A same-version reinstall and registered corruption repair
> **Authority:** frozen repository contracts plus accepted Termux TGZ evidence

## Executive state

```text
Stage 3-C Phases 1–4
  FROZEN

Stage 3-C Phase 5 Gate 1
  FROZEN PASS
  80/80

Stage 3-C Phase 5 Gate 2
  FROZEN PASS
  location A 80/80
  location B 80/80
  Gate 2 46/46

Stage 3-C Phase 5 Gate 3A
  ACTIVE DESIGN BOUNDARY
  target workflow not yet frozen
```

## Frozen Gate 2 identity

```text
archive
  stage3c-phase5-installed-runtime-relocation-root-shape-corrected-results-20260712-163535.tgz

archive sha256
  8e57399f907aec0c64e033a1d51380f0a27c3806773bc05ed2d88cbd3bf8785e

result-index sha256
  a6607fd9bc88e4cf2776295b0fce329b690b8ccf33aba2426847ba1529e85e3d

complete-root fingerprint
  aea9a035d55530ab513458f43dbf7604a1f6aa9628eae4218dd050e688c14a30

complete-root shape
  719 entries
  60 directories
  656 regular files
  3 symlinks
  0 special

portable payload fingerprint
  f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978
```

Final evidence:

```text
docs/evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_RELOCATION_RESULT.md
```

The first Gate 2 verifier failure remains preserved and must not be rewritten as a pass.

## Gate 3 ordered boundaries

```text
Gate 3A  same-version reinstall NOOP and registered corruption repair
Gate 3B  modified owned-leaf and unowned-sentinel preservation
Gate 3C  addon composition, dependency enforcement, and addon removal
Gate 3D  runtime uninstall and exact final ownership boundary
```

Do not combine these subgates into one initial target run. Each subgate must produce its own machine evidence and accepted TGZ.

## First active question — Gate 3A

> Does the frozen Phase 4 engine produce a true same-version NOOP on an exact installed runtime and repair only registered corruptions back to the frozen manifest identity?

## Mandatory inputs

Gate 3A must consume:

```text
accepted Phase 4 integrated durability evidence
frozen runtime-base manifest and archive
frozen recovery engine and helpers
frozen Gate 1 portable identity
frozen Gate 2 complete-root identity where relevant
canonical Stage 3-B promoted Python only as tool Python
```

The runtime under test must be installed through the frozen Phase 4 engine.

Forbidden substitutions:

```text
Stage 3-B promoted prefix as runtime under test
Phase 1 isolated runtime as runtime under test
direct archive extraction that bypasses the engine
synthetic ownership registry
modified Phase 4 transaction or recovery semantics
```

## Required Gate 3A scenarios

### Exact same-version reinstall

```text
fresh runtime-base install
capture registry bytes
capture portable and strict payload fingerprints
run install runtime-base again
require noop=true
require zero payload mutations
require zero registry mutations
require registry bytes unchanged
require payload fingerprints unchanged
require engine verify PASS
```

### Registered corruption repair

Use independent scenario roots for at least:

```text
regular-file byte corruption
registered regular-file removal
registered symlink target corruption
registered symlink removal
registered mode corruption
```

Directory repair may be added only where the frozen transaction contract clearly defines safe reconstruction.

For each scenario:

```text
record exact intentional mutation
verify the corrupted state before repair
run install runtime-base through frozen engine
verify only expected registered paths changed
verify exact registry mapping restored
verify portable payload identity restored
verify engine verify PASS
verify runtime behavior after repair
```

## Evidence discipline

Every scenario must record:

```text
source manifest row
before path identity
intentional mutation description
post-mutation identity
engine result and mutation list
post-repair identity
registry before and after
unaffected-path fingerprint or equivalent proof
return code
```

Console markers alone are insufficient.

A final independent verifier must recompute scenario expectations from the frozen manifest and generated evidence rather than trusting scenario `pass` fields.

## Non-reopening rule

Gate 3A may add orchestration and independent verification only.

It must not change:

```text
source archives
manifests
installation contract
registry schema or ownership semantics
transaction operations
recovery behavior
durability helpers
```

If a target result exposes a frozen-engine defect, preserve the failure evidence and stop. Do not silently patch Phase 4 while claiming Gate 3 validation.

## Claim boundary

Gate 3A PASS will prove exact same-version NOOP behavior and registered corruption repair for `runtime-base`.

It will not prove:

```text
modified owned-leaf preservation
unowned sentinel preservation
addon lifecycle
runtime uninstall
upgrade or downgrade
cross-filesystem relocation
physical power-loss persistence
```

## Successor first action

Read the frozen transaction and recovery operation implementations and existing Phase 4 scenario evidence. Derive the exact expected mutation semantics before writing the Gate 3A runner.

Relevant starting points:

```text
experiments/stage3c-installation-transaction/transaction_engine.py
experiments/stage3c-installation-transaction/run-transaction-scenarios.py
experiments/stage3c-installation-recovery/recovery_engine.py
experiments/stage3c-installation-recovery/recovery_operations.py
docs/stages/STAGE3C_PHASE4_FINAL.md
docs/stages/STAGE3C_PHASE5_SCOPE.md
```
