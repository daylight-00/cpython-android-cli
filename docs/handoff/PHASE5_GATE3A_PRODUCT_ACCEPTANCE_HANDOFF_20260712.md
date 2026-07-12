# Phase 5 Gate 3A Product Acceptance Handoff — 2026-07-12

> **Current boundary:** corrected same-version reinstall and registered repair product acceptance
> **Prerequisite:** frozen Phase 4I missing-leaf intervention evidence
> **Target:** Termux on Android arm64

## Frozen authority

```text
Gate 1 installed-runtime baseline
  FROZEN 80/80

Gate 2 installed-root relocation
  FROZEN 46/46

Gate 3A0 diagnostic
  FROZEN 17/17 + 31/31

Phase 4I missing-leaf intervention
  FROZEN 39/39 + 51/51
```

Phase 4I accepted archive:

```text
stage3c-phase4-missing-leaf-repair-intervention-results-20260712-180237.tgz
sha256
  d497955abf1c4f83d9efc4e01783447c30af30f9b7b532d4a454b263a89c655a

result-index sha256
  7c87a7a3ee34b9c827a4895c78dc15780058d5f3af37e7eb78cd1c454d28f3b6
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE4_MISSING_LEAF_REPAIR_INTERVENTION_RESULT.md
```

## Product question

> After exact same-version reinstall and every accepted registered repair class, does the corrected installed runtime retain exact ownership identity and the full Gate 1 runtime behavior contract?

## Installed identity semantics

```text
portable fingerprint
  f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978
  portable cross-install identity

manifest source-tree fingerprint
  9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796
  frozen contract identity only

strict installed fingerprint
  contains mtime_ns
  same-tree mutation control only
```

Do not require the manifest source-tree fingerprint as the installed strict fingerprint.

Required strict evidence:

```text
per repair
  714-entry shape and safety PASS
  zero pycache and special paths

runtime probes
  strict fingerprint before and after probes byte-identical
```

## Required repair classes

```text
regular byte corruption
regular mode corruption
registered regular replaced by directory
symlink target corruption
missing registered regular
missing registered symlink
```

Exact same-version reinstall remains a separate NOOP prerequisite.

## Required topology

Use one fresh corrected-engine installation as an immutable seed and create independent scenario roots for all repair classes.

Additionally create one canonical sequential acceptance root:

```text
fresh install
→ exact reinstall NOOP
→ six corruption/repair cycles
→ full installed-runtime validation
```

Every scenario root and the sequential acceptance root must be inode-separated from the seed.

## Per-repair evidence

Each repair class must prove:

```text
intentional mutation recorded
pre-repair engine verify has exactly one bad path
corrected install succeeds
install action counts noop 713 / repair 1
mutation count 2
post-repair engine verify PASS
registry byte identity unchanged
portable fingerprint f860caf... exact
strict shape and safety PASS
transaction residue 0
final candidate exact to manifest and source archive
unaffected-path identity exact
```

## Sequential acceptance root

The sequential root must apply and repair all six classes in deterministic order. After every repair, capture registry, portable, strict-shape, and transaction identities.

After the final repair, run the complete installed-runtime behavior contract:

```text
Python 3.14.6
Android aarch64
SOABI cpython-314-aarch64-linux-android
MULTIARCH aarch64-linux-android
sys.prefix and base_prefix exact
sysconfig paths inside installed prefix
HTTPS status 200
smoke-termux PASS
uv venv PASS
uv run anyio PASS
native closure 81 ELF / 329 edges / 0 unresolved
system SONAME dlopen 5/5
extension imports 67/67
engine verify PASS
registry 1 artifact / 714 owned rows
portable identity exact
strict before/after probes identical
no transaction residue
```

## Gate 1 regression requirement

The accepted correction changes the engine implementation identity even though fresh installation behavior is expected to remain unchanged.

Gate 3A acceptance must therefore include a Gate 1-equivalent regression using the corrected engine. A prior Gate 1 TGZ alone is insufficient.

The current workflow reuses the sequential root and invokes the complete frozen 80-check Gate 1 verifier after all repairs.

## Independent verification

```text
repair scenario checks
  29

Gate 1 regression checks
  80

Gate 3A acceptance checks
  69
```

The 69 checks are split into repair/evidence and runtime/identity modules. They reopen raw engine outputs, mutation records, registry bytes, portable and strict controls, runtime probes, uv results, native closure outputs, and result-index coverage.

Scenario-level `pass` values and final console markers are not authority.

## Gate 2 boundary

Gate 2 relocation regression remains separate unless the Gate 3A workflow explicitly moves the complete corrected-engine installation root and repeats full destination validation.

Do not claim Gate 2 regression from Gate 3A acceptance alone.

## Claim boundary

Gate 3A PASS will prove corrected same-version NOOP, all six registered repair classes, and full post-repair installed-runtime behavior.

It will not prove:

```text
Gate 2 relocation regression
modified owned-leaf preservation
unowned sentinel preservation
addon lifecycle
uninstall
upgrade or downgrade
```

## Active workflow

```text
experiments/stage3c-installed-runtime-lifecycle/GATE3A_PRODUCT_ACCEPTANCE.md
experiments/stage3c-installed-runtime-lifecycle/run-gate3a-product-acceptance.sh
```
