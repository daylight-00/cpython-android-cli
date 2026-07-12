# Stage 3-C Phase 5 Scope: Installed Runtime and Lifecycle Validation

> **Status:** ACTIVE — Gate 3A reinstall/repair diagnostic census
> **Input:** frozen Stage 3-C Phases 1–4 and frozen Phase 5 Gates 1–2
> **Primary target:** Termux on Android arm64

## Phase question

> Does the frozen runtime remain exact, functional, natively closed, relocatable, repairable, composable, and safely removable after installation through the frozen transaction engine?

## Frozen product identities

```text
runtime-base manifest entries
  714

runtime-base source-tree fingerprint
  9c6b8ee205ab3d41f79fc0cf0a817730af091b3af81db4bde7d1f44449e97796

portable installed-payload fingerprint
  f860cafec28cfb5eb91bd8bcc492ca824e1f912afa4614176df1606a1b006978

runtime-base archive sha256
  2ba7c309b1700926dc423eb4305a9eba1a53c023a11617e490b151be71e49743

runtime-base manifest sha256
  ce48849c9c88c9296264d6a917c3b55b0433e0d67bdda06579d6f18d701f285a

native closure
  81 ELF
  329 DT_NEEDED edges
  0 unresolved
  67/67 extension imports

Phase 4 integrated durability result-index
  878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce
```

## Gate order

```text
Gate 1   installed runtime baseline                              FROZEN
Gate 2   complete installed-root relocation                     FROZEN
Gate 3A0 reinstall/repair diagnostic census                     ACTIVE
Gate 3A  accepted same-version reinstall and repair             BLOCKED
Gate 3B  modified owned-leaf and unowned-sentinel preservation  DEFERRED
Gate 3C  addon lifecycle and dependency enforcement             DEFERRED
Gate 3D  runtime uninstall and final ownership boundary         DEFERRED
Gate 4   upgrade and downgrade with second frozen product       DEFERRED
```

`Gate 3A0` is a diagnostic authority boundary. A PASS classifies behavior; it is not product acceptance.

## Frozen Gate 1 — installed runtime baseline

```text
archive sha256
  06aa75b8b7617dc1310e7c0f3b56781b2297d2cc1ad617c1f4045909af9fb6ea

result-index sha256
  29e6dc1e24b7ad82bd809ac44d70aac1486549e71c24d49eb3ef8cc2dc4fe377

verifier
  80/80 PASS

install / registry
  714 creates
  715 mutations
  1 artifact
  714 owned rows
  manifest mapping exact

runtime
  Python 3.14.6
  Android aarch64
  HTTPS 200
  uv venv and uv run PASS
  81 ELF / 329 edges / 0 unresolved
  5/5 system SONAME dlopen
  67/67 extension imports
```

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_BASELINE_RESULT.md
```

## Frozen Gate 2 — complete installed-root relocation

```text
archive sha256
  8e57399f907aec0c64e033a1d51380f0a27c3806773bc05ed2d88cbd3bf8785e

result-index sha256
  a6607fd9bc88e4cf2776295b0fce329b690b8ccf33aba2426847ba1529e85e3d

location A Gate 1
  80/80 PASS

location B Gate 1
  80/80 PASS

Gate 2 verifier
  46/46 PASS

complete-root fingerprint
  aea9a035d55530ab513458f43dbf7604a1f6aa9628eae4218dd050e688c14a30

complete-root shape
  719 entries
  60 directories
  656 regular files
  3 symlinks
  0 special
```

The complete root, registry, payload identities, runtime, HTTPS, uv, closure, and stale-prefix checks remained exact after a same-filesystem inode-preserving move.

Evidence:

```text
docs/evidence/STAGE3C_PHASE5_INSTALLED_RUNTIME_RELOCATION_RESULT.md
```

## Active Gate 3A0 — reinstall/repair diagnostic census

### Reason for intervention census

The frozen installer plans `repair` whenever a registered non-directory path does not match its registry row.

For an existing path, repair backs it up and publishes the frozen archive member.

For an absent registered leaf, the same path attempts:

```text
durable_move(absent source, backup)
  → os.replace(absent source, backup)
  → expected FileNotFoundError
```

Prior Phase 4 evidence proved in-place byte-corruption repair. It did not close missing regular or symlink repair.

Therefore product acceptance must not assume that all registered corruption classes are repairable.

### Diagnostic matrix

```text
exact same-version reinstall            expected NOOP
regular byte mismatch                   expected supported repair
regular mode mismatch                   expected supported repair
symlink target mismatch                 expected supported repair
registered regular replaced by dir      expected supported repair
registered regular absent               expected unsupported
registered symlink absent               expected unsupported
```

### Diagnostic scenario isolation

One fresh runtime-base seed installation is independently copied to seven scenario roots.

Required clone checks:

```text
root inode separation
registry inode separation
representative payload inode separation
```

Hardlink-based scenario seeds are forbidden.

### Exact NOOP evidence

```text
noop                         true
action_counts                {noop: 714}
mutation_count               0
registry identity            unchanged
portable identity            unchanged
transactions                 empty
engine verify                PASS
```

### Supported in-place repair evidence

Each supported scenario must show:

```text
pre-verify bad paths         exactly one
install actions              {noop: 713, repair: 1}
mutation_count               2
post-verify                  PASS
registry identity            unchanged
portable identity            restored
transactions                 empty
final path                   exact manifest identity
```

### Missing-leaf diagnostic evidence

The source-derived expected observation is:

```text
pre-verify                   one missing bad path
install                      rc=44 / FileNotFoundError
journal before recovery      APPLYING
first recovery               ROLLED_BACK
retained journal             ROLLED_BACK
second recovery              NOOP_ROLLED_BACK
post-recovery verify         same missing bad path
registry row                 retained
leaf                         absent
```

A match is a diagnostic PASS and a product-acceptance blocker.

### Diagnostic verifier

```text
scenario checks              17
independent verifier         31
```

The independent verifier must read raw engine outputs and journal inventories rather than trusting scenario `pass` fields.

### Diagnostic workflow

```text
experiments/stage3c-installed-runtime-lifecycle/
├── README.md
├── run-gate3a-reinstall-repair-diagnostic.sh
├── run-gate3a-reinstall-repair-diagnostic.py
└── verify-gate3a-reinstall-repair-diagnostic.py
```

### Post-diagnostic decision

If missing-leaf failure is confirmed:

```text
preserve authoritative TGZ evidence
freeze only the diagnostic census
keep Gate 3A product acceptance blocked
decide whether Phase 4 architecture intervention is required
```

Any intervention must explicitly reopen affected frozen authority and identify downstream revalidation requirements. It must not be hidden inside a Phase 5 validation change.

## Deferred lifecycle boundaries

### Gate 3A product acceptance

Requires an explicit decision after the diagnostic census. Product acceptance must cover exact NOOP and all approved repair classes, including final runtime validation.

### Gate 3B preservation

```text
modified owned regular leaf
modified owned symlink
unowned sentinel file
unowned sentinel directory
exact preservation or replacement policy derived from frozen contract
```

### Gate 3C addons

```text
runtime-base
→ development-addon
→ test-addon
→ dependency-order rejection
→ test-addon removal
→ development-addon removal
→ runtime-base revalidation
```

### Gate 3D uninstall

```text
runtime-base-only state
approved unowned sentinels
frozen-engine uninstall
owned payload removal
unowned preservation
registry transition
transaction residue check
empty-state engine verification
```

### Gate 4 upgrade/downgrade

Deferred until a second complete frozen product identity exists. Synthetic version labels are forbidden.

## Non-reopening rule

Gate 3 diagnostic work may add orchestration and independent verification only.

It must not silently change:

```text
source archives
manifests
installation contract
registry schema or ownership semantics
transaction operations
recovery behavior
durability helpers
```

A frozen-engine defect requires a separately authorized architecture intervention.

## Claim boundaries

A Gate 3A0 diagnostic PASS proves only the target classification matrix.

It does not prove:

```text
Gate 3A product acceptance
missing-leaf repair
preservation policy
addon lifecycle
uninstall
upgrade or downgrade
cross-filesystem relocation
physical power-loss persistence
```

## Results layout

```text
results/termux/stage3c-phase5-gate3a-reinstall-repair-diagnostic/
work/termux/stage3c-phase5-gate3a-reinstall-repair-diagnostic/
```
