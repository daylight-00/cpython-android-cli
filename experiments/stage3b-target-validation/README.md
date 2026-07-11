# Stage 3-B Phase 5 Target Validation

Run these gates on Termux after isolated promoted runtime assembly.

```text
candidate
  work/termux/stage3b-promoted-runtime/prefix

frozen baseline
  work/termux/stage2c/runtime/prefix
```

The frozen baseline is an observation and mutation-control input only. Candidate-specific evidence is written under `results/termux/stage3b-*`.

## Gate 1: canonical behavior smoke

```sh
bash experiments/stage3b-target-validation/smoke-promoted-runtime.sh
```

Observed final result:

```text
STAGE2C_SMOKE=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
STAGE3B_PROMOTED_SMOKE=PASS
```

Results:

```text
results/termux/stage3b-promoted-smoke
```

Evidence:

```text
docs/evidence/STAGE3B_PHASE5_PROMOTED_SMOKE.md
```

## Gate 2: inventory and native closure equivalence

```sh
bash experiments/stage3b-target-validation/validate-promoted-closure.sh
```

Hard semantic gates:

```text
symlinks                         5
ELF objects                    81
DT_NEEDED edges              329
RUNTIME_INTERNAL edges        80
ANDROID_SYSTEM edges         249
unresolved edges               0
unique needed SONAMEs          9
runtime-internal SONAMEs       4
Android-system SONAMEs         5
system SONAME dlopen          5/5
extension imports           67/67
inspection errors              0
```

The first run exposed validation-induced `.pyc` mutation because isolated children ignored shell `PYTHON*` controls. The repaired child contract is:

```text
python -I -B -S -c ...
```

Clean rerun:

```text
candidate file entries                  3155
candidate mutation control              PASS
frozen mutation control                 PASS
machine verifier checks                37/37
STAGE3B_PROMOTED_CLOSURE=PASS
```

Results:

```text
results/termux/stage3b-promoted-closure
```

Evidence:

```text
docs/evidence/STAGE3B_PHASE5_PROBE_MUTATION_DIAGNOSIS.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_CLOSURE.md
```

## Gate 3: CA and timezone boundary equivalence

```sh
bash experiments/stage3b-target-validation/validate-promoted-boundaries.sh
```

The corrected probes compare candidate and frozen runtime under the same host state.

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

Results:

```text
results/termux/stage3b-promoted-boundaries
```

Evidence:

```text
docs/evidence/STAGE3B_PHASE5_BOUNDARY_PROBE_REASSESSMENT.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_BOUNDARIES.md
```

## Gate 4: production-shape whole-prefix relocation

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

### First-run fidelity incident

The first run passed all functional relocation checks and candidate/frozen mutation controls, but the source/B strict fingerprint differed.

Read-only diagnosis found:

```text
source entries               3155
relocated entries            3155
added paths                     0
removed paths                   0
portable changed paths          0
pycache paths                    0
portable fidelity             PASS
```

The only strict difference was directory `st_size` for:

```text
lib/python3.14/lib-dynload
```

Source `st_size` was `12288`; copied B `st_size` was `20480`. File content, modes, mtimes, symlinks, and path sets were identical.

Classification:

```text
FINGERPRINT CONTRACT FALSE POSITIVE
```

Evidence:

```text
docs/evidence/STAGE3B_PHASE5_PROMOTED_RELOCATION_FIDELITY_INCIDENT.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_RELOCATION_FIDELITY_RESOLUTION.md
```

### Corrected comparison model

Candidate and frozen before/after mutation controls still use the same-tree strict fingerprint.

Source/B cross-tree fidelity now requires:

```text
same path set
same type, mode and mtime
same regular-file size and SHA-256
same symlink target
```

Directory `st_size` is ignored only for cross-tree product fidelity and retained as a non-gating diagnostic observation.

The corrected wrapper writes:

```text
results/termux/stage3b-promoted-relocation/
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

Expected final markers:

```text
LOCATION_RECONFIRM[A]=PASS
LOCATION_RECONFIRM[B]=PASS
STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS
RELOCATED_RUNTIME_PORTABLE_FIDELITY_CHECK=PASS
CANDIDATE_RUNTIME_MUTATION_CHECK=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
STAGE3B_PROMOTED_RELOCATION=PASS
```

The source candidate remains canonical and read-only. Relocation is performed only on a copy under `work/termux/stage3b-promoted-relocation`.
