# Stage 3-C Phase 5 Gate 3A: Corrected Reinstall and Repair Product Acceptance

> **Status:** FROZEN PASS
> **Target:** Termux on Android arm64
> **Next boundary:** Gate 2R corrected-engine relocation regression

## Frozen result

```text
GATE3A_ACCEPTANCE_EXACT_REINSTALL_NOOP=PASS
GATE3A_ACCEPTANCE_ISOLATED_REPAIRS=6/6 PASS
GATE3A_ACCEPTANCE_SEQUENTIAL_REPAIRS=6/6 PASS
GATE3A_ACCEPTANCE_REGISTRY_AND_PAYLOAD=PASS
GATE3A_ACCEPTANCE_HTTPS=200 PASS
GATE3A_ACCEPTANCE_UV_VENV=PASS
GATE3A_ACCEPTANCE_UV_RUN=PASS
GATE3A_ACCEPTANCE_NATIVE_CLOSURE=81/329/0 PASS
GATE3A_ACCEPTANCE_EXTENSION_IMPORTS=67/67 PASS
GATE3A_ACCEPTANCE_GATE1_REGRESSION=80/80 PASS
GATE3A_ACCEPTANCE_VERIFICATION=69/69 PASS
STAGE3C_PHASE5_GATE3A_REINSTALL_REPAIR_ACCEPTANCE=PASS
```

Accepted archive:

```text
stage3c-phase5-gate3a-reinstall-repair-acceptance-results-20260712-191758.tgz
sha256
  16dbe98dedeb8db92df574a4d22ac3e45c0dd4032771dcf75e5e489b49605142
size
  48,135,273 bytes
members
  1,284
```

Result identity:

```text
root result-index sha256
  a161eedeebd086b1be6f115671312b463ed1eb9969c4494cae1bdbb626794128
indexed files
  1,174/1,174 exact
repair scenario checks
  29/29
Gate 1 regression
  80/80
acceptance verifier
  69/69
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_GATE3A_PRODUCT_ACCEPTANCE_RESULT.md
```

## Accepted classes

```text
exact same-version reinstall NOOP
regular byte repair
regular mode repair
registered regular wrong-type repair
symlink target repair
missing registered regular repair
missing registered symlink repair
```

Every repair preserved registry bytes, unaffected owned paths, portable installed identity, strict shape and safety, and zero transaction residue.

## Accepted runtime contract

```text
Python 3.14.6
Android aarch64
SOABI cpython-314-aarch64-linux-android
MULTIARCH aarch64-linux-android
HTTPS 200
smoke-termux PASS
uv venv PASS
uv run anyio PASS
native closure 81/329/0
system SONAME 5/5
extension imports 67/67
engine verify 1 artifact / 714 owned rows / 0 bad paths
```

Portable before and after runtime probes remained:

```text
f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978
```

Strict installed-tree fingerprints include `mtime_ns` and were used as same-tree mutation controls; before and after runtime probes were identical.

## Preserved first-run infrastructure failure

The first target run is preserved separately. Product-facing work passed, but the modular acceptance verifier failed before executing checks because its sibling module directory was absent under Python isolated mode.

```text
docs/evidence/STAGE3C_PHASE5_GATE3A_PRODUCT_ACCEPTANCE_FAILURE_20260712.md
```

The corrected bootstrap and one-command Termux wrapper produced the accepted archive.

## Next boundary

```text
Gate 2R corrected-engine complete-root relocation regression
```

Handoff:

```text
docs/handoff/PHASE5_GATE2R_CORRECTED_ENGINE_RELOCATION_HANDOFF_20260712.md
```

## Termux execution policy

Target-only workflows must provide one wrapper script that verifies inputs, performs fresh extraction and execution, records status and result indices, and creates a TGZ on PASS or FAIL.

## Claim boundary

Gate 3A proves corrected reinstall, all six repair classes, and full post-repair installed-runtime behavior. Corrected-engine relocation, preservation boundaries, addon lifecycle, uninstall, upgrade, and downgrade remain separate gates.
