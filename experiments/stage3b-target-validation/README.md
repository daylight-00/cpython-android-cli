# Stage 3-B Phase 5 Target Validation

Run these gates on Termux after isolated promoted runtime assembly.

Candidate runtime:

```text
work/termux/stage3b-promoted-runtime/prefix
```

Frozen baseline:

```text
work/termux/stage2c/runtime/prefix
```

The baseline is an observation and mutation-control input only. These workflows do not write results into the frozen Stage 3-A result directory.

## Gate 1: canonical behavior smoke

```sh
bash experiments/stage3b-target-validation/smoke-promoted-runtime.sh
```

Candidate-specific results:

```text
results/termux/stage3b-promoted-smoke
```

Observed final result:

```text
STAGE2C_SMOKE=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
STAGE3B_PROMOTED_SMOKE=PASS
```

Evidence:

```text
docs/evidence/STAGE3B_PHASE5_PROMOTED_SMOKE.md
```

## Gate 2: inventory and native closure equivalence

```sh
bash experiments/stage3b-target-validation/validate-promoted-closure.sh
```

The wrapper reuses the frozen Stage 3-A inventory, closure, system-SONAME, and extension-import engines with candidate-specific paths.

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

The first run exposed validation-induced mutation because isolated child probes ignored shell-level `PYTHON*` controls. The repaired child contract is:

```text
python -I -B -S -c ...
```

The candidate was freshly reassembled before the clean rerun.

Observed final result:

```text
candidate file entries                  3155
ELF objects                               81
DT_NEEDED edges                          329
unresolved edges                           0
Android-system SONAME dlopen             5/5
extension imports                       67/67
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

The Stage 3-A boundary probes were corrected before reuse:

```text
CA child
  add explicit -B to isolated child

zoneinfo child
  remove -I because PYTHONTZPATH is the variable under test
  sanitize ambient PYTHON* variables
  use -B -P -s
  record actual input and flags
```

The corrected workflow runs CA, direct-zoneinfo, and uv-tzdata probes against both candidate and frozen runtime under the same Termux host state.

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
uv base-prefix identity                   PASS for both
candidate mutation control               PASS
frozen mutation control                  PASS
```

Final markers:

```text
CA_BOUNDARY_EQUIVALENCE=PASS
ZONEINFO_BOUNDARY_EQUIVALENCE=PASS
TZDATA_FALLBACK_EQUIVALENCE=PASS
CANDIDATE_RUNTIME_MUTATION_CHECK=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
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

The workflow reuses the Stage 3-A production relocation engine with the promoted source prefix:

```text
promoted candidate
  -> copy complete prefix to location A
  -> validate A
  -> move A prefix to location B
  -> validate B
```

At both locations it validates:

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

The Stage 3-B wrapper adds:

```text
candidate source before/after fingerprint
frozen control before/after fingerprint
final B fingerprint versus source candidate fingerprint
A absent and B present after move
B Python executable
structured machine verdict
```

The relocation engine exports both:

```text
PYTHONDONTWRITEBYTECODE=1
PYTHONPYCACHEPREFIX=<results>
```

so validation must not create bytecode in the relocated prefix.

Expected final markers:

```text
LOCATION_RECONFIRM[A]=PASS
LOCATION_RECONFIRM[B]=PASS
STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS
RELOCATED_RUNTIME_FIDELITY_CHECK=PASS
CANDIDATE_RUNTIME_MUTATION_CHECK=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
STAGE3B_PROMOTED_RELOCATION=PASS
```

Results:

```text
results/termux/stage3b-promoted-relocation
```

Primary verdict:

```text
results/termux/stage3b-promoted-relocation/promoted-relocation-verification.json
```

The source candidate remains canonical and read-only. Relocation is performed on a copy under `work/termux/stage3b-promoted-relocation`.
