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
fresh-process child
  python -I -S -c ...

-I isolated mode
  -> ignores shell PYTHON* bytecode controls
  -> child imports can write .pyc into candidate prefix
```

Repair:

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

## Gate 3 result: CA and timezone boundary equivalence

Before reuse, the Stage 3-A boundary probes were corrected:

```text
CA child
  old: python -I -S -c ...
  new: python -I -B -S -c ...

zoneinfo child
  old: tested PYTHONTZPATH under -I
  new: sanitized Python environment + python -B -P -s -c ...
```

Command:

```sh
bash experiments/stage3b-target-validation/validate-promoted-boundaries.sh
```

Machine verdict:

```text
check_count        28
failed_checks      []
missing_outputs    []
parse_errors       {}
pass               true
```

CA result for both candidate and frozen runtime:

```text
clean default            Termux CA, HTTPS 200
explicit Termux CA       preserved, HTTPS 200
missing CA path          repaired to Termux CA, HTTPS 200
existing empty file      preserved, HTTPS failure expected
```

Corrected direct-zoneinfo result for both runtimes:

```text
default
  PYTHONTZPATH unset
  configured POSIX TZPATH directories absent
  representative keys FAIL

package-only
  PYTHONTZPATH=""
  zoneinfo.TZPATH=[]
  base tzdata package absent
  representative keys FAIL

explicit Termux path
  PYTHONTZPATH=$PREFIX/share/zoneinfo
  requested path observed by child
  path absent on tested host
  representative keys FAIL
```

uv first-party fallback for both runtimes:

```text
tzdata version           2026.3
PYTHONTZPATH              ""
UTC                       PASS
Asia/Seoul                PASS
America/New_York          PASS
uv sys.base_prefix        expected source runtime
```

Both candidate and frozen runtime fingerprints remained unchanged.

Final markers:

```text
CA_BOUNDARY_EQUIVALENCE=PASS
ZONEINFO_BOUNDARY_EQUIVALENCE=PASS
TZDATA_FALLBACK_EQUIVALENCE=PASS
CANDIDATE_RUNTIME_MUTATION_CHECK=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
STAGE3B_PROMOTED_BOUNDARIES=PASS
```

Evidence:

```text
docs/evidence/STAGE3B_PHASE5_BOUNDARY_PROBE_REASSESSMENT.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_BOUNDARIES.md
```

Gate 3 is closed.

## Current action: Gate 4 whole-prefix relocation

The remaining Phase 5 gate tests the promoted product in the same production shape used for the frozen Stage 3-A relocation proof:

```text
promoted source candidate
  -> copy complete prefix to location A
  -> validate A
  -> move whole prefix A -> B
  -> validate B
```

Command:

```sh
git pull --ff-only

rm -rf \
  work/termux/stage3b-promoted-relocation \
  results/termux/stage3b-promoted-relocation

bash \
  experiments/stage3b-target-validation/validate-promoted-relocation.sh
```

Location A and B validate:

```text
base runtime identity
active sysconfig paths
native stdlib and libc loadability
HTTPS through Termux CA integration
subprocess interpreter identity
fresh uv venv creation
fresh venv base-prefix identity
uv run with explicit interpreter
uv run base-prefix identity
absence of the forbidden stale prefix
```

The promoted wrapper adds outer evidence controls:

```text
canonical candidate source fingerprint unchanged
frozen Stage 2-C control fingerprint unchanged
final B fingerprint identical to source candidate fingerprint
location A absent after move
location B present with executable Python
structured machine verdict retained on completed failure attempts
```

The reused relocation engine now also exports explicit:

```text
PYTHONDONTWRITEBYTECODE=1
```

in addition to its external pycache root, so validation must not write bytecode into the relocated product.

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

Primary machine-readable verdict:

```text
results/termux/stage3b-promoted-relocation/promoted-relocation-verification.json
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

## File-entry count policy

The frozen Stage 3-A aggregate was:

```text
file_entry_count=3280
```

The fresh promoted candidate aggregate was:

```text
file_entry_count=3155
```

Raw file count is not a semantic pass/fail gate. Complete row-level inventory is retained; closure structure, runtime identity, import surface, boundary behavior, relocation, and mutation controls are the gates.

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
[x] closure workflow candidate mutation control passes
[x] closure workflow frozen mutation control passes
[x] CA boundary equivalence passes
[x] corrected timezone boundary equivalence passes
[x] first-party tzdata fallback equivalence passes
[x] boundary workflow candidate mutation control passes
[x] boundary workflow frozen mutation control passes
[ ] whole-prefix relocation A validation passes
[ ] whole-prefix relocation B validation passes
[ ] stale A-prefix assertions pass
[ ] relocated B fingerprint matches source candidate
[ ] relocation workflow candidate and frozen mutation controls pass
[ ] relocation machine verdict passes
```

Phase 5 remains active until the relocation gate passes or new evidence explicitly reopens a prior condition.
