# Stage 3-C Phase 5 Gate 3A: Corrected Reinstall and Repair Product Acceptance

> **Status:** FROZEN PASS
> **Target:** Termux on Android arm64
> **Accepted engine:** recovery-safe missing registered leaf correction

## Executive result

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

## Authoritative archive identity

```text
archive
  stage3c-phase5-gate3a-reinstall-repair-acceptance-results-20260712-191758.tgz

sha256
  16dbe98dedeb8db92df574a4d22ac3e45c0dd4032771dcf75e5e489b49605142

size
  48,135,273 bytes

members
  1,284

regular files / directories
  1,187 / 97

symlinks / hardlinks / special / unsafe paths
  0 / 0 / 0 / 0
```

The one-command Termux wrapper reported workflow return code 0 and packaged this archive.

## Result-index identities

```text
Gate 3A root result-index sha256
  a161eedeebd086b1be6f115671312b463ed1eb9969c4494cae1bdbb626794128

Gate 3A root indexed files
  1,174 / 1,174 exact

accepted Phase 4 result-index sha256
  878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce

accepted Phase 4 indexed files
  294 / 294 exact

accepted Phase 4I result-index sha256
  7c87a7a3ee34b9c827a4895c78dc15780058d5f3af37e7eb78cd1c454d28f3b6

accepted Phase 4I indexed files
  523 / 523 exact

all nested Phase 4 indices
  exact

hash, size, mode, missing, duplicate, and coverage mismatches
  0
```

## Workflow and evidence integrity

```text
workflow components
  repair_scenarios         0
  engine_verify            0
  base_probe               0
  smoke                    0
  venv_probe               0
  uv_run                   0
  closure_inventory        0
  closure_analysis         0
  closure_extension        0
  input_mutation           0
  gate1_regression         0
  acceptance_verification  0

input entries before / after
  905 / 905

input fingerprint before / after
  2aaa3502c7e54ee1b652c2f5b64eebbdd43037178f4ecc3a3bf266d1db445e22
  exact

generated JSON
  208 / 208 canonical

raw process and fingerprint records
  all exact to embedded scenario records
```

The two non-canonical JSON files in the archive are frozen copied `product-lock.json` inputs; no generated result JSON was non-canonical.

## Exact reinstall

```text
action counts
  noop 714

mutation count
  0

engine verification
  PASS

registry, strict, portable, and transaction identities
  unchanged
```

## Isolated repair matrix

All six accepted repair classes passed in inode-separated roots:

```text
regular byte corruption
regular mode corruption
registered regular replaced by directory
symlink target corruption
missing registered regular
missing registered symlink
```

For every repair:

```text
pre-repair verify
  rc 44
  exactly one bad path

install actions
  noop 713
  repair 1

mutation count
  2

post-repair verify
  rc 0
  bad paths 0

registry identity
  unchanged

portable installed-payload fingerprint
  f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978

strict installed-tree control
  714-entry shape and safety PASS

unaffected owned-path digest
  unchanged

transaction residue
  0
```

Final missing-leaf candidates were exact:

```text
regular
  lib/python3.14/LICENSE.txt
  mode 0600
  size 13804
  sha256 b0e25a78cffb43f4d92de8b61ccfa1f1f98ecbc22330b54b5251e7b6ba010231

symlink
  bin/python
  mode 0777
  target python3
```

## Sequential product root

One fresh corrected-engine installation completed:

```text
exact same-version NOOP
six deterministic corruption/repair cycles
final engine verification
complete installed-runtime behavior validation
```

All six sequential repairs reproduced the isolated repair contract, including exact registry and unaffected-path preservation after every repair.

## Gate 1-equivalent corrected-engine regression

```text
verifier
  80 / 80 PASS

failed checks
  0
```

Runtime result:

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

smoke-termux
  PASS

uv venv
  PASS

uv run anyio
  PASS

native closure
  81 ELF
  329 DT_NEEDED edges
  0 unresolved

system SONAME dlopen
  5 / 5

extension imports
  67 / 67

engine registry
  1 artifact
  714 owned rows
  0 bad paths
```

## Installed identity semantics

```text
portable before / after runtime probes
  f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978

strict before / after runtime probes
  shape and safety PASS
  fingerprint identical
```

The strict fingerprint contains `mtime_ns` and is used as a same-tree mutation control. The manifest source-tree fingerprint is not asserted as an installed strict fingerprint.

## Independent verifier

```text
repair scenario checks
  29 / 29

Gate 1 regression checks
  80 / 80

Gate 3A acceptance checks
  69 / 69

failed checks
  0

missing files
  0
```

## Preserved first-run failure

The first Gate 3A target run is retained as infrastructure-failure evidence. Product-facing repair and runtime checks passed, but the modular 69-check verifier failed before execution because Python isolated mode did not include the verifier directory for sibling imports.

```text
docs/evidence/STAGE3C_PHASE5_GATE3A_PRODUCT_ACCEPTANCE_FAILURE_20260712.md
```

The corrected verifier bootstrap and one-command Termux wrapper produced the accepted archive above.

## Claim boundary

This PASS proves:

```text
corrected exact same-version reinstall NOOP
all six accepted registered repair classes
registry and unaffected-owned-path preservation
portable installed identity restoration
complete post-repair runtime behavior
corrected-engine Gate 1-equivalent regression
```

It does not prove:

```text
corrected-engine complete-root relocation
modified owned-leaf preservation policy
unowned sentinel preservation
addon lifecycle
uninstall
upgrade or downgrade
```
