# Stage 3-B Phase 5 Final Summary

> **Status:** FROZEN
> **Question:** Does the promoted runtime preserve frozen Stage 2 behavior and Stage 3-A closure/boundary invariants on the actual target?
> **Answer:** Yes, for the tested Termux/Android arm64 environment and the explicit validation surface below.

## Inputs

```text
promoted candidate
  work/termux/stage3b-promoted-runtime/prefix

frozen control
  work/termux/stage2c/runtime/prefix
```

## Gate 1: canonical behavior smoke

```text
candidate executable/prefix/base_prefix identity   PASS
native stdlib smoke                                PASS
HTTPS                                               200
subprocess identity                                PASS
uv venv creation                                   PASS
venv prefix/base_prefix identity                   PASS
uv run                                             PASS
frozen runtime mutation check                      PASS
STAGE3B_PROMOTED_SMOKE=PASS
```

## Gate 2: complete inventory and native closure

```text
candidate file entries                  3155
symlinks                                   5
ELF objects                               81
DT_NEEDED edges                          329
RUNTIME_INTERNAL edges                    80
ANDROID_SYSTEM edges                     249
unresolved edges                           0
inspection errors                          0
Android-system SONAME dlopen             5/5
extension imports                       67/67
candidate mutation control              PASS
frozen mutation control                 PASS
machine verifier checks                37/37
STAGE3B_PROMOTED_CLOSURE=PASS
```

The first closure attempt produced 43 validation-induced bytecode entries because `python -I -S` ignored shell `PYTHON*` controls. The child contract was corrected to `python -I -B -S`, and the candidate was freshly reassembled rather than cleaned in place.

## Gate 3: CA and timezone boundaries

```text
machine verifier checks                  28/28
CA policy matrix                          equivalent
corrected direct-zoneinfo scenarios      equivalent
base runtime timezone source             unavailable in both
uv first-party tzdata version            2026.3
UTC                                      PASS for both
Asia/Seoul                               PASS for both
America/New_York                         PASS for both
candidate mutation control               PASS
frozen mutation control                  PASS
STAGE3B_PROMOTED_BOUNDARIES=PASS
```

The direct-zoneinfo probe was corrected because `-I` invalidated the `PYTHONTZPATH` input under test. The final base-runtime model is explicit: usable zoneinfo data was absent on the tested host, while first-party `tzdata` injection through uv passed.

## Gate 4: production-shape whole-prefix relocation

```text
LOCATION_RECONFIRM[A]=PASS
LOCATION_RECONFIRM[B]=PASS
STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS
RELOCATED_RUNTIME_PORTABLE_FIDELITY_CHECK=PASS
CANDIDATE_RUNTIME_MUTATION_CHECK=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
STAGE3B_PROMOTED_RELOCATION=PASS
```

Machine verifier:

```text
schema_version      2
check_count        31
failed_checks      []
missing_outputs    []
parse_errors       {}
pass               true
```

Relocated-product fidelity:

```text
source entries               3155
relocated entries            3155
added paths                     0
removed paths                   0
portable changed paths          0
pycache paths                    0
portable fidelity             PASS
strict fidelity               PASS
```

Portable fingerprint for source and B:

```text
79ca7d53f25810b1f5276d18df31f10f2ae981dc24caf67c5f33d37fa75127c8
```

Path-level strict diagnostic fingerprint for source and B:

```text
f46b5d81917e9d5dbcfc826a7ef33ef84c1b7db127689def7f20966037a57011
```

Candidate source mutation fingerprint:

```text
834f7aeb2e5266f027b6ee43dd77255079b2e01cf049dad56fda5ef39ce048b0
```

Frozen control mutation fingerprint:

```text
5a14f213bbf069b844a799615ed2b87eb34b48b4251b0a48bf431337e929ce0e
```

The first relocation attempt exposed a fingerprint-contract false positive caused by copied-directory `st_size`. The final architecture separates same-tree mutation checks from cross-tree product fidelity and hashes every regular file.

## Frozen Phase 5 result

The promoted runtime preserves the tested frozen model across:

```text
base CLI startup
native stdlib surface
HTTPS trust
subprocess re-entry
uv explicit-interpreter use
fresh venv identity
complete native closure
Android-system dependency loadability
67-extension import surface
active runtime/sysconfig identity
CA policy behavior
timezone data boundary behavior
first-party tzdata fallback
whole-prefix relocation
stale-prefix absence
source/control immutability
relocated-product path/content/symlink fidelity
```

## Claim boundary

Phase 5 does not claim:

```text
multi-device equivalence
multi-ABI/API equivalence
archive reproducibility
installer correctness
release signing
SBOM completeness
uv managed-Python provider compatibility
```

Those are later-stage questions.

## Evidence map

```text
docs/evidence/STAGE3B_PHASE5_PROMOTED_SMOKE.md
docs/evidence/STAGE3B_PHASE5_PROBE_MUTATION_DIAGNOSIS.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_CLOSURE.md
docs/evidence/STAGE3B_PHASE5_BOUNDARY_PROBE_REASSESSMENT.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_BOUNDARIES.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_RELOCATION_FIDELITY_INCIDENT.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_RELOCATION_FIDELITY_RESOLUTION.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_RELOCATION.md
```

## Final marker

```text
STAGE3B_PHASE5=FROZEN
```
