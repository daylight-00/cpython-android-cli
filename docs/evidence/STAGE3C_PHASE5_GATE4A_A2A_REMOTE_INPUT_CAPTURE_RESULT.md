# Stage 3-C Phase 5 Gate 4A A2a Remote-Input Capture Result

> **Status:** A2a FROZEN PASS — A2b Linux-workstation toolchain witness pending
> **Claim class:** immutable remote-input authority only

## Accepted result archive

```text
archive
  20260713-gate4a-a2a-remote-input-capture-results-20260713T132628Z.tar.zst

archive sha256
  e9c9ed69098017017b3cbf70e8237c040ede26d378f6530043cc5ff4e7469caf

archive size
  26,218 bytes

archive members
  53 total / 51 regular / 2 directories
  0 links / 0 special / 0 unsafe / 0 duplicate

root result-index sha256
  5d87e7727aef99b793ac8ddacf5e9d77f96701caf2377094013753edcda17fbe

root indexed files
  50/50 exact

external audit
  81/81 PASS
```

The result is bound to:

```text
branch  agent/phase5-gate4-second-product-authority
HEAD    b807c2964b408adc954a7f5a2155030e7442ed05
tree    2f0106dc6f19ab2190dcb9c15454f6e041e44fa7
```

## Preserved original collector result

The original collector emitted a complete pass-or-fail archive and correctly preserved its own result:

```text
GATE4A_A2A_REMOTE_INPUT_CAPTURE=FAIL
CHECKS=44/49
TOOLCHAIN_WITNESS_STATUS=pending-linux-workstation-witness
```

Failed checks:

```text
reused_first_lock_exact_bzip2
reused_first_lock_exact_libffi
reused_first_lock_exact_sqlite
reused_first_lock_exact_xz
reused_first_lock_exact_zstd
```

This original FAIL is retained as immutable diagnostic evidence. It is not rewritten or hidden.

## Failure classification

The five failures are a verifier false negative, not an input-identity contradiction.

The collector compared each complete captured dependency record against the older first-product lock with direct object equality for the `archive` field. The new capture intentionally added three safety diagnostics:

```text
other_count          0
unsafe_member_names  []
unsafe_link_targets  []
```

The old lock schema does not contain these keys. Therefore complete dictionary equality returned false even though every pre-existing identity and inventory field matched.

The independent audit recomputed the intended contract without weakening it:

```text
version / recipe revision / release tag     exact
host / filename / source URL                 exact
size / SHA-256                               exact
legacy archive inventory fields              exact
new safety diagnostics                       independently required and PASS
```

For bzip2, libffi, sqlite, xz, and zstd, both the stable identity projection and all legacy archive inventory values match the frozen first-product lock exactly. The added safety fields are valid for all five assets.

## Captured immutable inputs

The audit accepts:

```text
CPython tag          v3.14.5
source commit        5607950ef232dad16d75c0cf53101d9649d89115
source tree          7f48ff2aae0af2f4f4ee51a8d9dc970a0a0571f7
Android API          24
required NDK         27.3.13750724
producer blobs       Android/android.py and Android/android-env.sh exact
reference archives   2/2 exact and safe
source dependencies  6/6 exact and safe
OpenSSL delta        3.0.20-0 versus first-product 3.5.7-0
```

The official source and Android package remain reference identities only. They are not promoted into project product authority.

## Acceptance boundary

A2a proves only that the exact v3.14.5 source, producer files, official references, and six producer-declared dependency assets were freshly fetched, hashed, structurally inventoried, and bound to the Gate 4A repository state.

It does **not** prove:

```text
A2b Linux-workstation NDK binary/path/tool witness
A3 clean upstream Android replay
A4 three-artifact materialization
A5 standalone Termux validation
A6 independent second-product freeze
upgrade or downgrade behavior
```

A2 remains open until A2b passes. Gate 4 transition design remains closed until A6.

## Machine authority

```text
docs/evidence/STAGE3C_PHASE5_GATE4A_A2A_REMOTE_INPUT_CAPTURE_EXTERNAL_AUDIT.json
experiments/stage3c-gate4-second-product-authority/verify-gate4a-a2a-remote-input-capture.py
```
