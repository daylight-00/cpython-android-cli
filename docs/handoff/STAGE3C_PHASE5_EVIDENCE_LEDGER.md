# Stage 3-C Phase 5 Evidence Ledger

> **Purpose:** compact authoritative identity ledger for installed-runtime and lifecycle gates.
> **Authority:** accepted Termux TGZ evidence plus repository-frozen contracts.

## Gate 1 — installed runtime baseline

```text
status
  FROZEN PASS

accepted archive sha256
  06aa75b8b7617dc1310e7c0f3b56781b2297d2cc1ad617c1f4045909af9fb6ea

result-index sha256
  29e6dc1e24b7ad82bd809ac44d70aac1486549e71c24d49eb3ef8cc2dc4fe377

verifier
  80/80 PASS

workflow return codes
  all 0

portable payload fingerprint
  f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978

payload shape
  714 entries
  654 regular
  57 directories
  3 symlinks
  0 special

registry
  1 artifact
  714 owned rows
  manifest mapping exact

runtime
  Python 3.14.6
  Android aarch64
  HTTPS 200
  uv venv PASS
  uv run anyio PASS

native closure
  81 ELF
  329 DT_NEEDED edges
  0 unresolved
  5/5 system SONAME dlopen
  67/67 extension imports
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_BASELINE_RESULT.md
```

Preserved first failure:

```text
verifier 78/80
phase4_result_index_exact
installed_fingerprint_exact
```

## Gate 2 — complete installed-root relocation

```text
status
  FROZEN PASS

accepted archive
  stage3c-phase5-installed-runtime-relocation-root-shape-corrected-results-20260712-163535.tgz

accepted archive sha256
  8e57399f907aec0c64e033a1d51380f0a27c3806773bc05ed2d88cbd3bf8785e

archive size
  24,212,336 bytes

archive members
  434

result-index sha256
  a6607fd9bc88e4cf2776295b0fce329b690b8ccf33aba2426847ba1529e85e3d

indexed files
  393 / 393 exact

location A Gate 1
  80/80 PASS

location B Gate 1
  80/80 PASS

Gate 2 verifier
  46/46 PASS

workflow return codes
  all 0
```

Complete-root identity:

```text
fingerprint
  aea9a035d55530ab513458f43dbf7604a1f6aa9628eae4218dd050e688c14a30

entries
  719

directories
  60

regular files
  656

symlinks
  3

special
  0
```

Relocation semantics:

```text
complete installation-root move          PASS
same filesystem                          PASS
installation-root inode preserved        PASS
location A root absent                   PASS
location B root present                  PASS
registry A-to-B                          byte exact
portable payload identity                exact
strict payload identity                  exact
complete-root identity                   exact
stale location-A references              0
```

Destination result:

```text
Python 3.14.6
Android aarch64
HTTPS 200
uv venv PASS
uv run anyio PASS
81 ELF
329 edges
0 unresolved
5/5 system SONAME dlopen
67/67 extension imports
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_RELOCATION_RESULT.md
```

Preserved first failure:

```text
verifier 45/46
installation_root_entry_count_717

root cause
  verifier omitted the durable lock and empty transactions root
```

## Active next boundary

```text
Stage 3-C Phase 5 Gate 3A
  same-version reinstall NOOP
  registered corruption repair
```

Gate 3 subgate order:

```text
3A reinstall and repair
3B preservation boundaries
3C addon lifecycle and dependencies
3D runtime uninstall and final ownership boundary
```

## Claim discipline

Gate 2 does not prove:

```text
cross-filesystem relocation
same-version reinstall or repair
modified owned-leaf preservation
unowned sentinel preservation
addon lifecycle
exact uninstall preservation
upgrade
downgrade
physical power-loss persistence
```
