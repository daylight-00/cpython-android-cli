# Stage 3-C Phase 5 Gate 3A: Corrected Reinstall and Repair Product Acceptance

> **Status:** ACTIVE — authoritative Termux evidence pending
> **Prerequisites:** frozen Phase 4I intervention, frozen Gate 1, frozen Gate 2
> **Target:** Termux on Android arm64

## Product question

> After exact same-version reinstall and every accepted registered repair class, does the corrected installed runtime retain exact ownership identity and the complete Gate 1 behavior contract?

## Frozen inputs and identity semantics

```text
Phase 4 integrated result-index
  878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce

Phase 4I intervention result-index
  7c87a7a3ee34b9c827a4895c78dc15780058d5f3af37e7eb78cd1c454d28f3b6

portable installed-payload fingerprint
  f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978

manifest source-tree fingerprint
  9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796
```

The manifest source-tree fingerprint is a frozen contract identity. It is **not** the expected installed strict fingerprint.

The strict installed-tree fingerprint includes `mtime_ns`; therefore it is a same-tree mutation control only:

```text
per repair
  strict output must pass 714-entry shape and safety checks

runtime probes
  strict fingerprint before and after probes must be identical

cross-root identity
  use the portable f860caf... fingerprint
```

## Scenario topology

One corrected-engine seed installation is used for seven inode-separated isolated roots:

```text
exact-noop
regular-bytes
regular-mode
regular-wrong-type
symlink-target
missing-regular
missing-symlink
```

A separate sequential root executes:

```text
fresh corrected install
→ exact reinstall NOOP
→ regular byte repair
→ regular mode repair
→ wrong-type regular repair
→ symlink target repair
→ missing regular repair
→ missing symlink repair
→ full runtime validation
```

## Per-repair proof

Each repair must produce:

```text
intentional mutation recorded
pre-repair verify exactly one bad path
install actions noop 713 / repair 1
mutation count 2
post-repair verify PASS
registry bytes unchanged
portable fingerprint f860caf... exact
strict output shape/safety PASS
unaffected owned paths exact
transaction residue 0
final candidate exact to manifest and source archive
```

A fixed strict hash is deliberately not required across independently installed roots.

## Runtime acceptance

The sequential repaired root must pass the existing Gate 1 verifier without weakening its 80 checks:

```text
Python 3.14.6
Android aarch64
SOABI cpython-314-aarch64-linux-android
MULTIARCH aarch64-linux-android
sys.prefix and base_prefix exact
sysconfig paths inside installed prefix
HTTPS 200
smoke-termux PASS
uv venv PASS
uv run anyio PASS
native closure 81 ELF / 329 edges / 0 unresolved
system SONAME dlopen 5/5
extension imports 67/67
registry 1 artifact / 714 owned rows
portable fingerprint f860caf... exact before and after probes
strict shape/safety PASS before and after probes
strict fingerprint unchanged across probes
zero transaction residue
```

## Verification

```text
repair scenario checks          29
Gate 1 regression checks        80
Gate 3A acceptance checks       69
```

The 69-check verifier is split into evidence/repair and runtime/identity modules. It independently reopens raw engine process records, repair records, registry identity, fingerprints, runtime probes, smoke output, closure results, and Gate 1 verification.

## Run

Freshly extract both accepted evidence archives:

```sh
cd "$HOME/projects/cpython-android-cli"

git fetch origin agent/phase5-gate3a-product-acceptance
git switch --detach origin/agent/phase5-gate3a-product-acceptance

git log -1 --oneline

PHASE4_ARCHIVE="$HOME/Downloads/stage3c-phase4-integrated-durability-results-20260712-082135.tgz"
PHASE4_EXTRACT="$PREFIX/tmp/stage3c-phase4-integrated-durability-accepted"

printf '%s  %s\n' \
  '76bb78f200d9836d96f677cc1eca1e2f1483186f3655efa17a8e1f2361bd0187' \
  "$PHASE4_ARCHIVE" | sha256sum -c -

rm -rf "$PHASE4_EXTRACT"
mkdir -p "$PHASE4_EXTRACT"
tar xzf "$PHASE4_ARCHIVE" -C "$PHASE4_EXTRACT"

PHASE4_RESULTS="$(find "$PHASE4_EXTRACT" \
  -type d \
  -path '*/results/termux/stage3c-phase4-integrated-durability' \
  -print -quit)"

PHASE4I_ARCHIVE="$HOME/Downloads/stage3c-phase4-missing-leaf-repair-intervention-results-20260712-180237.tgz"
PHASE4I_EXTRACT="$PREFIX/tmp/stage3c-phase4-missing-leaf-repair-intervention-accepted"

printf '%s  %s\n' \
  'd497955abf1c4f83d9efc4e01783447c30af30f9b7b532d4a454b263a89c655a' \
  "$PHASE4I_ARCHIVE" | sha256sum -c -

rm -rf "$PHASE4I_EXTRACT"
mkdir -p "$PHASE4I_EXTRACT"
tar xzf "$PHASE4I_ARCHIVE" -C "$PHASE4I_EXTRACT"

PHASE4I_RESULTS="$(find "$PHASE4I_EXTRACT" \
  -type d \
  -path '*/results/termux/stage3c-phase4-missing-leaf-repair-intervention' \
  -print -quit)"

test -n "$PHASE4_RESULTS"
test -n "$PHASE4I_RESULTS"

PHASE4_RESULTS="$PHASE4_RESULTS" \
PHASE4I_RESULTS="$PHASE4I_RESULTS" \
  bash experiments/stage3c-installed-runtime-lifecycle/run-gate3a-product-acceptance.sh
```

## Expected markers

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

## Upload

```sh
RESULTS="$PWD/results/termux/stage3c-phase5-gate3a-reinstall-repair-acceptance"
ARCHIVE="$HOME/Downloads/stage3c-phase5-gate3a-reinstall-repair-acceptance-results-$(date +%Y%m%d-%H%M%S).tgz"

tar czf "$ARCHIVE" "$RESULTS"
printf 'upload: %s\n' "$ARCHIVE"
```

## Claim boundary

A PASS closes corrected same-version reinstall and all six registered repair classes with complete installed-runtime behavior. Corrected-engine relocation, preservation boundaries, addon lifecycle, uninstall, upgrade, and downgrade remain separate gates.
