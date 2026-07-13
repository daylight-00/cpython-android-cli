# Stage 3-C Phase 5 Gate 3D Final Uninstall Acceptance Result

> **Status:** FROZEN PASS
> **Target:** Termux on Android arm64
> **Scope:** complete three-artifact teardown, final runtime-base uninstall, residual ownership, recovery, locking, and archive integrity

## Accepted authority

```text
archive
  stage3c-phase5-gate3d-final-uninstall-results-20260713T053801Z.tar.zst

archive sha256
  579b880495098e9a46b40e2d96c9555178d0ad8c725d40768e6b854227d66143

archive size
  23,270,627 bytes

accepted implementation tree
  5d54f8e0ab69ab5923949b9a5a34d71e2ab3da36

observed applied head
  d147a577fce60005890c04d8a0fec34a8a37190b
```

The commit SHA is transport-dependent because `git am` creates a new committer identity. The semantic tree is the repository authority.

## Target and independent verification

```text
accepted authority checks       22/22 PASS
target scenarios                44/44 PASS
independent verifier          138/138 PASS
external archive audit          37/37 PASS

preflight / teardown / residual
  6 / 8 / 10

recovery / locking / audit
  12 / 2 / 6
```

The target wrapper did not enable the local development `GATE3C_FAST_SUCCESS` path.

## Archive and index integrity

```text
archive members                    909
regular / directories          846 / 63
unsafe / symlink / hardlink       0 / 0 / 0
special entries                       0

root indexed files              845/845 exact
root result-index sha256
  5f9aa64cb4e0679a4784c9c3b8ebd6d8d91829704984672186dc9f9c0d96ed60

result-tree-safety sha256
  47b571d79990cf6c5f1157f7784a5acfa47478b04a7c6f55185d3c4f38ab8a00

generated canonical JSON        442/442
```

The archive has one root (`target-results`), no unsafe path, no link, no special entry, no duplicate member, and exact root-index membership, mode, size, and SHA-256 identities.

## Raw process evidence

```text
process records                       177
records with JSON output              164
stdout/output byte-exact               164

return codes
  rc 0    144
  rc 44    20
  rc 90     5
  rc 92     4
  rc 93     4
```

All output-bearing process records reopen to the exact recorded result object. Every referenced stdout, stderr, and output file exists. Preflight and lock-contention rejection use rc 44 without unauthorized mutation.

## Recovery acceptance

```text
PREPARED       rc 90
late APPLYING  rc 93
COMMITTED      rc 92

pre-commit first recovery
  ROLLED_BACK

pre-commit second recovery
  NOOP_ROLLED_BACK

committed first recovery
  FINALIZED_COMMIT

committed second recovery
  zero transactions
```

The accepted recovery cross-product covers exact-owned, modified-owned regular, modified-owned symlink, and unowned-file subjects.

## Accepted final-state boundary

Gate 3D distinguishes and accepts all of the following without conflation:

```text
registry empty
matching owned payload absent
approved modified-owned residual preserved and deregistered
unowned sentinel preserved and unchanged
required non-empty ancestors retained only when needed
transaction inventory empty or one accepted ROLLED_BACK tombstone
prefix root physically empty or non-empty according to the residual class
```

Both composed-product addon teardown orders, both one-addon states, runtime-only teardown, guarded rejection, repeated uninstall rejection, residual classes, recovery, locking, and final audits passed.

## Evidence files

```text
experiments/stage3c-installed-runtime-lifecycle/gate3d-final-uninstall-acceptance.json
docs/evidence/STAGE3C_PHASE5_GATE3D_EXTERNAL_AUDIT.json
docs/evidence/STAGE3C_PHASE5_GATE3D_FINAL_UNINSTALL_ACCEPTANCE_RESULT.md
```

External audit JSON sha256:

```text
55f1411cb6ef88f8641d6b3ef74324d07e1be20080070dfe0cf8ead1aae25c63
```

## Claim boundary

Gate 3D final uninstall and ownership handling is frozen PASS for the accepted three-artifact product. This does not authorize upgrade or downgrade. Gate 4 requires a second complete frozen product identity, a separately frozen cross-product design, target execution, and independent archive inspection. Synthetic version labels are not acceptable evidence.
