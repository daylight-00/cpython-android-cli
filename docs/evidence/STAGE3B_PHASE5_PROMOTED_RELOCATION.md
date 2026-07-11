# Stage 3-B Phase 5 Promoted Relocation Evidence

> **Status:** PASS
> **Execution host:** Termux on Android arm64
> **Runtime:** CPython 3.14.6
> **Gate:** production-shape whole-prefix relocation

## Workflow

```text
canonical promoted candidate
  -> copy complete prefix to location A
  -> validate A
  -> move complete prefix A -> B
  -> validate B
```

Inputs:

```text
candidate
  work/termux/stage3b-promoted-runtime/prefix

frozen control
  work/termux/stage2c/runtime/prefix
```

## Functional relocation

Location A passed:

```text
runtime identity re-rooted at A
active sysconfig paths re-rooted at A
HTTPS 200
child interpreter identity re-rooted at A
fresh uv venv PASS
venv base-prefix identity PASS
uv run PASS
uv run base-prefix identity PASS
```

Location B passed after moving the complete prefix:

```text
runtime identity re-rooted at B
active sysconfig paths re-rooted at B
HTTPS 200
child interpreter identity re-rooted at B
fresh uv venv PASS
venv base-prefix identity PASS
uv run PASS
uv run base-prefix identity PASS
stale A-prefix active assertions absent
```

Observed engine markers:

```text
LOCATION_RECONFIRM[A]=PASS
LOCATION_RECONFIRM[B]=PASS
STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS
STAGE3A_PRODUCTION_RELOCATION_RECONFIRM=PASS
```

## Product fidelity

The corrected cross-tree contract compared the canonical candidate and relocated B using complete path-level manifests.

```text
source_entry_count             3155
relocated_entry_count          3155
added_count                       0
removed_count                     0
portable_changed_count            0
pycache_path_count                 0
portable_pass                   true
strict_changed_count               0
strict_pass                     true
```

Portable manifest fingerprint:

```text
source
  79ca7d53f25810b1f5276d18df31f10f2ae981dc24caf67c5f33d37fa75127c8

relocated B
  79ca7d53f25810b1f5276d18df31f10f2ae981dc24caf67c5f33d37fa75127c8
```

Path-level strict diagnostic fingerprint:

```text
source
  f46b5d81917e9d5dbcfc826a7ef33ef84c1b7db127689def7f20966037a57011

relocated B
  f46b5d81917e9d5dbcfc826a7ef33ef84c1b7db127689def7f20966037a57011
```

The same-tree shell fingerprint also matched source and B on this clean rerun:

```text
834f7aeb2e5266f027b6ee43dd77255079b2e01cf049dad56fda5ef39ce048b0
```

The earlier copied-directory `st_size` mismatch did not recur in this run, but the portable contract remains the authoritative cross-tree product definition because it validates actual product content and excludes filesystem allocation metadata.

## Source/control mutation checks

Canonical candidate:

```text
before
  834f7aeb2e5266f027b6ee43dd77255079b2e01cf049dad56fda5ef39ce048b0

after
  834f7aeb2e5266f027b6ee43dd77255079b2e01cf049dad56fda5ef39ce048b0

pass=true
```

Frozen Stage 2-C control:

```text
before
  5a14f213bbf069b844a799615ed2b87eb34b48b4251b0a48bf431337e929ce0e

after
  5a14f213bbf069b844a799615ed2b87eb34b48b4251b0a48bf431337e929ce0e

pass=true
```

## Machine verifier

```text
schema_version      2
check_count        31
failed_checks      []
missing_outputs    []
parse_errors       {}
pass               true
```

All 31 checks passed, including:

```text
workflow exit zero
candidate source unchanged
frozen control unchanged
portable fidelity contract v2 selected
source and B roots correct
entry counts equal and non-zero
no added paths
no removed paths
no portable changes
portable fingerprints equal
status and JSON evidence cross-consistent
A absent after move
B present with executable Python
all four engine markers exactly once
source/A/B log path identities correct
```

## Final markers

```text
LOCATION_RECONFIRM[A]=PASS
LOCATION_RECONFIRM[B]=PASS
STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS
RELOCATED_RUNTIME_PORTABLE_FIDELITY_CHECK=PASS
CANDIDATE_RUNTIME_MUTATION_CHECK=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
STAGE3B_PROMOTED_RELOCATION=PASS
```

## Conclusion

The promoted runtime preserves tested runtime behavior, active path identity, consumer workflows, stale-prefix absence, source/control immutability, and complete relocated-product fidelity after a production-shape whole-prefix move.

Gate 4 is closed.
