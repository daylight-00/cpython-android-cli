# Stage 3-C Phase 5 Gate 3A Diagnostic Scope

> **Status:** ACTIVE — authoritative target census pending
> **Purpose:** classify frozen same-version reinstall and repair behavior before product acceptance

## Diagnostic boundary

This scope is intentionally narrower than Gate 3A product acceptance.

```text
exact reinstall NOOP
in-place registered repair classes
missing-leaf install failure
recovery journal state and residue
```

It does not authorize changes to the frozen engine.

## Expected classification matrix

```text
exact same-version reinstall            supported NOOP
regular byte mismatch                   supported repair
regular mode mismatch                   supported repair
symlink target mismatch                 supported repair
registered regular wrong type           supported repair
registered regular absent               expected unsupported
registered symlink absent               expected unsupported
```

## Diagnostic completion

The census is complete only after an authoritative Termux TGZ independently proves:

```text
scenario checks                         17/17
independent verifier                    31/31
Phase 4 input before/after              exact
result-index                            exact
all scenario roots inode-separated      true
```

## Post-census decision

A confirmed missing-leaf defect blocks Gate 3A product acceptance. The next action is an explicit architecture intervention decision, not Gate 3B.

A repair change would reopen frozen Phase 4 behavior and require impact analysis for recovery, durability, Gate 1 installed identity, and Gate 2 relocation evidence.
