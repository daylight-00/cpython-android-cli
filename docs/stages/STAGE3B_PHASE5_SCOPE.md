# Stage 3-B Phase 5 Scope: Target Runtime and Closure Equivalence

> **Status:** ACTIVE
> **Input:** isolated promoted runtime candidate
> **Execution host:** Termux on Android arm64
> **Baseline:** frozen Stage 3-A runtime and closure model

## Question

> Does the runtime assembled from promoted products preserve the frozen Stage 2 behavior and Stage 3-A closure invariants on the actual target?

## Candidate and baseline

```text
candidate
  work/termux/stage3b-promoted-runtime/prefix

baseline
  work/termux/stage2c/runtime/prefix
```

The baseline is read-only evidence during this phase. Candidate-specific observations are written under new `results/termux/stage3b-*` directories.

## Validation order

```text
1. canonical behavior smoke
2. complete prefix inventory
3. ELF and DT_NEEDED closure
4. 67-extension isolated import surface
5. active runtime/sysconfig paths
6. CA and timezone boundary behavior
7. subprocess, uv and venv identity
8. whole-prefix relocation
```

A failure in an earlier gate is analyzed before later gates proceed.

## Gate 1 result: promoted canonical smoke

Command:

```sh
bash experiments/stage3b-target-validation/smoke-promoted-runtime.sh
```

Observed:

```text
candidate executable/prefix/base_prefix identity   PASS
native stdlib smoke                                PASS
HTTPS                                               200
subprocess identity                                PASS
uv venv creation                                   PASS
venv prefix/base_prefix identity                   PASS
uv run                                             PASS
frozen runtime mutation check                      PASS
```

Final markers:

```text
STAGE2C_SMOKE=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
STAGE3B_PROMOTED_SMOKE=PASS
```

Evidence:

```text
docs/evidence/STAGE3B_PHASE5_PROMOTED_SMOKE.md
```

## Gate 2 result: promoted closure equivalence

The first promoted-closure run matched the frozen semantic closure model but failed the candidate mutation control.

Observed semantic match:

```text
symlink_count                              5
elf_object_count                          81
needed_edge_count                        329
classification edges
  RUNTIME_INTERNAL                        80
  ANDROID_SYSTEM                         249
unresolved_edge_count                      0
inspection_error_count                     0
unique_needed_soname_count                 9
classification unique SONAMEs
  RUNTIME_INTERNAL                         4
  ANDROID_SYSTEM                           5
Android-system SONAME dlopen              5/5
isolated extension imports              67/67
```

Post-failure comparison found:

```text
file entries before   3280
file entries after    3323
delta                    43

new __pycache__ dirs      4
new .pyc files           39
```

Root cause:

```text
probe wrapper environment
  PYTHONDONTWRITEBYTECODE=1
  PYTHONPYCACHEPREFIX=<results>

fresh-process child probes
  python -I -S -c ...

-I isolated mode
  -> ignores PYTHON* environment variables
  -> child imports can write .pyc into candidate prefix
```

The repaired child contract is:

```text
python -I -B -S -c ...
```

The candidate was freshly reassembled from the canonical promoted package rather than cleaned in place.

Clean rerun result:

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
candidate before fingerprint == after fingerprint
frozen before fingerprint == after fingerprint
machine verifier checks                  37/37
```

Final markers:

```text
UNRESOLVED_EDGE_COUNT=0
SYSTEM_SONAME_PROBE=PASS
EXTENSION_IMPORT_PROBE=PASS
CANDIDATE_RUNTIME_MUTATION_CHECK=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
STAGE3B_PROMOTED_CLOSURE=PASS
```

Evidence:

```text
docs/evidence/STAGE3B_PHASE5_PROBE_MUTATION_DIAGNOSIS.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_CLOSURE.md
```

Gate 2 is closed.

## Current action: Gate 3 CA and timezone boundary equivalence

Pre-run review of the Stage 3-A boundary probes found two probe-contract issues:

```text
CA child
  python -I -S -c ...
  -> bytecode-write risk because -I ignores shell PYTHON* controls
  -> repaired to python -I -B -S -c ...

zoneinfo child
  tested PYTHONTZPATH while using -I
  -> invalid control because -I ignores the variable under test
  -> repaired to sanitized environment + python -B -P -s -c ...
```

The old zoneinfo evidence remains valid for:

```text
default runtime lookup failure
host $PREFIX/share/zoneinfo absence at the filesystem check
uv-injected first-party tzdata fallback PASS
```

The direct `PYTHONTZPATH` scenario claims are reopened and must be rerun with a child that actually consumes the scenario input.

Detailed reassessment:

```text
docs/evidence/STAGE3B_PHASE5_BOUNDARY_PROBE_REASSESSMENT.md
```

Run on Termux:

```sh
git pull --ff-only

rm -rf \
  results/termux/stage3b-promoted-boundaries

bash \
  experiments/stage3b-target-validation/validate-promoted-boundaries.sh
```

The Gate 3 workflow runs corrected CA, direct-zoneinfo, and uv-tzdata probes against both:

```text
candidate
  work/termux/stage3b-promoted-runtime/prefix

frozen control
  work/termux/stage2c/runtime/prefix
```

and writes to:

```text
results/termux/stage3b-promoted-boundaries
```

Expected final markers:

```text
CA_BOUNDARY_EQUIVALENCE=PASS
ZONEINFO_BOUNDARY_EQUIVALENCE=PASS
TZDATA_FALLBACK_EQUIVALENCE=PASS
CANDIDATE_RUNTIME_MUTATION_CHECK=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
STAGE3B_PROMOTED_BOUNDARIES=PASS
```

Primary machine-readable verdict:

```text
results/termux/stage3b-promoted-boundaries/promoted-boundary-verification.json
```

## Frozen semantic closure gates

The candidate preserves:

```text
symlink_count                              5
elf_object_count                          81
needed_edge_count                        329
classification edges
  RUNTIME_INTERNAL                        80
  ANDROID_SYSTEM                         249
unresolved_edge_count                      0
inspection_error_count                     0
unique_needed_soname_count                 9
classification unique SONAMEs
  RUNTIME_INTERNAL                         4
  ANDROID_SYSTEM                           5
Android-system SONAME dlopen              5/5
isolated extension imports              67/67
```

Active runtime identity points to the promoted candidate:

```text
sys.executable
sys.prefix
sys.base_prefix
sys.exec_prefix
active sysconfig paths
active lib-dynload discovery
LD_LIBRARY_PATH candidate component
Termux CA file
```

Both the candidate and frozen runtime fingerprints remained unchanged across the completed Gate 2 workflow.

## File-entry count policy

The frozen Stage 3-A aggregate was:

```text
file_entry_count=3280
```

The fresh promoted candidate aggregate was:

```text
file_entry_count=3155
```

The complete candidate `files.tsv` is retained and the aggregate delta is reported, but raw file count is not a semantic pass/fail gate. Closure structure, active runtime identity, import surface, and mutation controls are the gates.

The earlier `+43` incident is separately preserved as validation-induced mutation evidence and is not conflated with the clean candidate's `-125` aggregate product difference.

## Acceptance conditions

```text
[x] base runtime starts
[x] native stdlib imports pass
[x] HTTPS passes
[x] subprocess re-entry passes
[x] uv venv creation passes
[x] venv prefix/base_prefix identity passes
[x] uv run passes
[x] full inventory captured
[x] unresolved DT_NEEDED edges = 0
[x] provider classification matches reviewed model
[x] 67/67 extension imports pass
[x] active runtime and sysconfig paths point to candidate
[x] frozen runtime mutation control passes in Gate 2
[x] candidate mutation failure root cause diagnosed
[x] probe child bytecode-write repair applied
[x] repaired clean rerun candidate mutation control passes
[x] repaired clean rerun machine verdict passes
[ ] corrected CA boundary equivalence passes
[ ] corrected timezone boundary equivalence passes or is intentionally reviewed
[ ] candidate and frozen mutation controls pass in Gate 3
[ ] whole-prefix relocation passes
```

Phase 5 remains active until all open conditions are either passed or explicitly reviewed and reopened.
