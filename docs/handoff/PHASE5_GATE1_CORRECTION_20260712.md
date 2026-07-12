# Stage 3-C Phase 5 Gate 1 Correction Handoff — 2026-07-12

> **Status:** corrected authoritative Termux rerun pending
> **Preserved failure:** `docs/evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_BASELINE_FAILURE.md`

## Current state

Stage 3-C Phases 1–4 remain frozen. Phase 5 Gate 1 remains active.

The first Gate 1 target run completed every installation and runtime component but failed the 80-check verifier at two identity checks:

```text
phase4_result_index_exact
installed_fingerprint_exact
```

The exact accepted Phase 4 result-index requirement remains:

```text
878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce
```

The corrected installed payload identity is:

```text
kind
  stage3c-installed-payload-portable-v1

sha256
  f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978
```

Strict metadata-sensitive fingerprints are retained only for before/after mutation control.

## Corrected rerun input

Do not use the mutable default Phase 4 result directory unless its root `result-index.json` has the accepted SHA-256.

Use a fresh extraction of:

```text
stage3c-phase4-integrated-durability-results-20260712-082135.tgz

sha256
  76bb78f200d9836d96f677cc1eca1e2f1483186f3655efa17a8e1f2361bd0187
```

## Corrected rerun

```sh
cd "$HOME/projects/cpython-android-cli"

git pull --ff-only
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

test -n "$PHASE4_RESULTS"

PHASE4_RESULTS="$PHASE4_RESULTS" \
  bash experiments/stage3c-installed-runtime-baseline/run-installed-runtime-baseline.sh
```

## Expected result

The corrected workflow must report:

```text
INSTALLED_RUNTIME_BASELINE_ACCEPTED_INPUTS=PASS
INSTALLED_RUNTIME_BASELINE_INSTALL=714/714 PASS
INSTALLED_RUNTIME_BASELINE_REGISTRY=714/714 PASS
INSTALLED_RUNTIME_BASELINE_SMOKE=PASS
INSTALLED_RUNTIME_BASELINE_HTTPS=200 PASS
INSTALLED_RUNTIME_BASELINE_UV_VENV=PASS
INSTALLED_RUNTIME_BASELINE_UV_RUN=PASS
INSTALLED_RUNTIME_BASELINE_NATIVE_CLOSURE=81/329/0 PASS
INSTALLED_RUNTIME_BASELINE_EXTENSION_IMPORTS=67/67 PASS
INSTALLED_RUNTIME_BASELINE_VERIFICATION=80/80 PASS
INSTALLED_RUNTIME_BASELINE_MUTATION_CHECK=PASS
STAGE3C_PHASE5_INSTALLED_RUNTIME_BASELINE=PASS
```

Upload a corrected-rerun TGZ. Do not overwrite or rename the first failed archive as though it passed.
