# Phase 5 Gate 2R Corrected-Engine Relocation Regression Handoff — 2026-07-12

> **Current boundary:** complete installed-root relocation under the accepted corrected engine
> **Prerequisite:** frozen Gate 3A product acceptance
> **Target:** Termux on Android arm64

## Frozen authority

```text
Gate 1 baseline
  FROZEN 80/80

Gate 2 historical complete-root relocation
  FROZEN 46/46

Gate 3A0 diagnostic
  FROZEN 17/17 + 31/31

Phase 4I intervention
  FROZEN 39/39 + 51/51

Gate 3A corrected product acceptance
  FROZEN 29/29 + 80/80 + 69/69
```

Accepted Gate 3A archive:

```text
stage3c-phase5-gate3a-reinstall-repair-acceptance-results-20260712-191758.tgz
sha256
  16dbe98dedeb8db92df574a4d22ac3e45c0dd4032771dcf75e5e489b49605142

result-index sha256
  a161eedeebd086b1be6f115671312b463ed1eb9969c4494cae1bdbb626794128
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_GATE3A_PRODUCT_ACCEPTANCE_RESULT.md
```

## Regression question

> Does a complete installation root created by the accepted corrected engine retain exact ownership identity and full runtime behavior after the same-filesystem inode-preserving relocation proven by historical Gate 2?

## Required topology

```text
fresh corrected-engine runtime-base installation at location A
full Gate 1-equivalent validation at A
complete installation-root fingerprint at A
same-filesystem mv from A to B
full Gate 1-equivalent validation at B
complete installation-root fingerprint after move and after probes
stale location-A scan
```

The moved root must include:

```text
prefix/
.cpython-android-cli/lock
.cpython-android-cli/registry.json
.cpython-android-cli/transactions/
```

## Required relocation evidence

```text
source and target parent device identical
root inode preserved
location A absent
location B present
location B Python executable
registry bytes exact
portable fingerprint f860caf... exact
strict same-tree fingerprint exact across move
complete-root fingerprint exact across move and probes
complete-root shape 719 / 60 / 656 / 3
no special paths
zero stale location-A references
zero transaction residue
```

## Runtime validation at both locations

```text
Gate 1 verifier 80/80
Python 3.14.6
Android aarch64
HTTPS 200
smoke-termux PASS
uv venv PASS
uv run anyio PASS
native closure 81/329/0
system SONAME 5/5
extension imports 67/67
engine verify 1 artifact / 714 owned rows / 0 bad paths
```

All install and verify operations must use the accepted corrected engine adapter.

## Historical Gate 2 reuse

The historical Gate 2 workflow and verifier may be adapted, but the new regression must not trust historical Gate 2 output as a substitute for a fresh corrected-engine target run.

Expected claim remains limited to same-filesystem rename-style relocation. Cross-filesystem copy relocation is not proved.

## Termux execution policy

Provide one Termux script that performs:

```text
accepted input TGZ hash verification
fresh extraction
complete regression workflow
wrapper status capture
result-index generation or regeneration
TGZ packaging on PASS or FAIL
archive path, SHA256, size, and workflow return code output
```

No separate extraction or `tar` command should be required from the user.

## Claim boundary

Gate 2R PASS will close corrected-engine relocation regression only. Gate 3B preservation boundaries, addon lifecycle, uninstall, upgrade, and downgrade remain separate gates.
