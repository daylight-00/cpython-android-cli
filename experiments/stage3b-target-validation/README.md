# Stage 3-B Phase 5 Target Validation

> **Status:** FROZEN
> **Execution host:** Termux on Android arm64

Inputs:

```text
candidate
  work/termux/stage3b-promoted-runtime/prefix

frozen baseline
  work/termux/stage2c/runtime/prefix
```

The frozen baseline is an observation and mutation-control input only. Candidate-specific evidence is written under `results/termux/stage3b-*`.

## Gate 1: canonical behavior smoke — PASS

```sh
bash experiments/stage3b-target-validation/smoke-promoted-runtime.sh
```

```text
STAGE2C_SMOKE=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
STAGE3B_PROMOTED_SMOKE=PASS
```

Results:

```text
results/termux/stage3b-promoted-smoke
```

## Gate 2: inventory and native closure — PASS

```sh
bash experiments/stage3b-target-validation/validate-promoted-closure.sh
```

Observed semantic gates:

```text
candidate file entries                  3155
symlinks                                   5
ELF objects                               81
DT_NEEDED edges                          329
RUNTIME_INTERNAL edges                    80
ANDROID_SYSTEM edges                     249
unresolved edges                           0
inspection errors                          0
system SONAME dlopen                     5/5
extension imports                       67/67
candidate mutation control              PASS
frozen mutation control                 PASS
machine verifier checks                37/37
STAGE3B_PROMOTED_CLOSURE=PASS
```

The first attempt exposed validation-induced bytecode mutation because isolated children ignored shell `PYTHON*` controls. The repaired child contract is:

```text
python -I -B -S -c ...
```

The candidate was freshly reassembled rather than cleaned in place.

Results:

```text
results/termux/stage3b-promoted-closure
```

## Gate 3: CA and timezone boundaries — PASS

```sh
bash experiments/stage3b-target-validation/validate-promoted-boundaries.sh
```

Observed machine result:

```text
check_count        28
failed_checks      []
missing_outputs    []
parse_errors       {}
pass               true
```

Boundary result:

```text
CA policy matrix                          equivalent
corrected direct-zoneinfo scenarios      equivalent
base runtime timezone source             unavailable in both
uv first-party tzdata version            2026.3
uv tzdata representative keys            3/3 PASS for both
candidate mutation control               PASS
frozen mutation control                  PASS
STAGE3B_PROMOTED_BOUNDARIES=PASS
```

The direct-zoneinfo probe avoids isolated mode because `PYTHONTZPATH` is the input under test.

Results:

```text
results/termux/stage3b-promoted-boundaries
```

## Gate 4: production-shape whole-prefix relocation — PASS

```sh
rm -rf \
  work/termux/stage3b-promoted-relocation \
  results/termux/stage3b-promoted-relocation

bash \
  experiments/stage3b-target-validation/validate-promoted-relocation.sh
```

Workflow:

```text
promoted candidate
  -> copy complete prefix to location A
  -> validate A
  -> move A prefix to location B
  -> validate B
```

At A and B it validates:

```text
sys.executable, sys.prefix and sys.base_prefix
active sysconfig paths
native imports and libc loadability
HTTPS through Termux CA integration
subprocess identity
fresh uv venv and venv base identity
uv run and uv run base identity
forbidden stale-prefix absence
```

Final observed markers:

```text
LOCATION_RECONFIRM[A]=PASS
LOCATION_RECONFIRM[B]=PASS
STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS
RELOCATED_RUNTIME_PORTABLE_FIDELITY_CHECK=PASS
CANDIDATE_RUNTIME_MUTATION_CHECK=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
STAGE3B_PROMOTED_RELOCATION=PASS
```

Machine verdict:

```text
schema_version      2
check_count        31
failed_checks      []
missing_outputs    []
parse_errors       {}
pass               true
```

Relocated-product result:

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

Portable source/B fingerprint:

```text
79ca7d53f25810b1f5276d18df31f10f2ae981dc24caf67c5f33d37fa75127c8
```

Path-level strict diagnostic source/B fingerprint:

```text
f46b5d81917e9d5dbcfc826a7ef33ef84c1b7db127689def7f20966037a57011
```

Candidate mutation fingerprint:

```text
834f7aeb2e5266f027b6ee43dd77255079b2e01cf049dad56fda5ef39ce048b0
```

Frozen mutation fingerprint:

```text
5a14f213bbf069b844a799615ed2b87eb34b48b4251b0a48bf431337e929ce0e
```

### Fidelity contract

Same-tree candidate/frozen before-and-after controls use the strict metadata-sensitive fingerprint.

Source/B cross-tree product fidelity requires:

```text
same relative path set
same type, mode and mtime
same regular-file size and SHA-256
same symlink target
```

Directory `st_size` is ignored only for cross-tree product identity and retained as a diagnostic observation.

### Outputs

```text
results/termux/stage3b-promoted-relocation/
  workflow-status.txt
  candidate-runtime-mutation-check.txt
  frozen-runtime-mutation-check.txt
  relocated-runtime-fidelity-check.txt
  relocation-location-state.txt
  fidelity-diagnosis/
    source-manifest.jsonl
    relocated-manifest.jsonl
    tree-delta.json
    tree-delta.tsv
    fidelity-status.txt
  promoted-relocation-verification.json
```

## Evidence

```text
docs/evidence/STAGE3B_PHASE5_PROMOTED_SMOKE.md
docs/evidence/STAGE3B_PHASE5_PROBE_MUTATION_DIAGNOSIS.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_CLOSURE.md
docs/evidence/STAGE3B_PHASE5_BOUNDARY_PROBE_REASSESSMENT.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_BOUNDARIES.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_RELOCATION_FIDELITY_INCIDENT.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_RELOCATION_FIDELITY_RESOLUTION.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_RELOCATION.md
docs/evidence/STAGE3B_PHASE5_FINAL_SUMMARY.md
```

## Final marker

```text
STAGE3B_PHASE5=FROZEN
```
