# CPython Android CLI + uv: Stage 3 Project Context

> **Status:** Current handoff context
> **Architecture:** Stage 2 frozen, Stage 3-A frozen, Stage 3-B Phases 1–4 frozen
> **Active work:** Stage 3-B Phase 5 corrected final relocation rerun
> **Primary target:** Termux on Android arm64 (`aarch64-linux-android`)
> **Host build environment:** Separate Linux workstation
> **Python baseline:** CPython 3.14.6

## 1. Project

This project is:

> **A CLI adaptation of an upstream CPython Android build for Termux, with uv integration.**

It preserves and studies:

```text
normal CPython CLI semantics
native stdlib imports
HTTPS trust
subprocess behavior
virtual environments
uv explicit-interpreter workflows
whole-prefix runtime relocation
```

It is not currently a general Python distribution, a Termux Python replacement, a uv-managed provider, or a CPython fork.

## 2. Working principle

```text
understand -> reproduce -> measure -> compare -> design -> optimize
```

Separate domains:

```text
runtime semantics
native loader behavior
Python path discovery
host data integration
build provenance
distribution contract
consumer integration
```

A solution in one domain is not assumed to solve another.

## 3. Stage status

```text
Stage 1-A  explicit runtime baseline                    FROZEN
Stage 1-B  PyConfig frontend comparison                 FROZEN
Stage 2-A  bootstrap strategy comparison                COMPLETE
Stage 2-B  conditional re-exec and relocation           COMPLETE
Stage 2-C  synthesis and project workflow               COMPLETE
Stage 2    native bootstrap and workflow architecture   FROZEN
Stage 3-A  runtime closure census and boundary model    FROZEN
Stage 3-B  reproducible build-input promotion           ACTIVE
Stage 3-C  distribution archive/installation contract  DEFERRED
Stage 3-D  consumer integration                         DEFERRED
```

## 4. Frozen Stage 2 architecture

```text
R2 conditional self re-exec
        +
B0 PyConfig auto-discovery frontend
```

Flow:

```text
shell / uv / venv entry
        |
        v
launcher
        |
        +-- resolve /proc/self/exe
        +-- derive actual prefix and <prefix>/lib
        +-- normalize LD_LIBRARY_PATH
        +-- preserve or discover SSL_CERT_FILE
        |
        +-- libdir absent at process start
        |       -> execv(actual executable, original argv)
        |
        +-- libdir already present
                -> PyConfig auto-discovery
                -> Py_RunMain
```

Frozen invariants:

```text
clean launch performs bootstrap re-exec
ready process avoids redundant re-exec
self-location follows actual executable
loader normalization uses exact path components
Python path discovery remains automatic
CA path repair stays separate from loader repair
venv prefix/base_prefix identity remains correct
uv explicit interpreter remains supported
whole-prefix relocation remains supported
```

## 5. Frozen Stage 3-A result

Inventory and native closure:

```text
file entries             3280
symlinks                    5
ELF objects                 81
DT_NEEDED edges            329
RUNTIME_INTERNAL edges      80
ANDROID_SYSTEM edges       249
UNRESOLVED edges              0
inspection errors             0
```

Extension surface:

```text
67 candidates
67 isolated imports PASS
0 FAIL
```

Runtime paths re-rooted correctly under relocation while some development/build metadata retained producer provenance. Runtime correctness and development-metadata relocation were intentionally distinguished.

CA boundary:

```text
clean default                PASS
explicit Termux CA           PASS
missing path repair          PASS
existing empty regular file  preserved, HTTPS FAIL
```

Timezone boundary, corrected follow-up:

```text
default POSIX TZPATH          unavailable on tested host
explicit Termux TZPATH        delivered but unavailable
base first-party tzdata       absent
uv tzdata 2026.3 fallback     PASS for UTC, Asia/Seoul, America/New_York
```

Final Stage 3-A markers:

```text
STAGE2C_SMOKE=PASS
LOCATION_RECONFIRM[A]=PASS
LOCATION_RECONFIRM[B]=PASS
STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS
STAGE3A_PRODUCTION_RELOCATION_RECONFIRM=PASS
STAGE3A=FROZEN
```

## 6. Stage 3-B producer result

Phases 1–4 made explicit and reproducible:

```text
exact CPython source identity
NDK 27.3.13750724
SDK/API/target identities
host build Python and build tools
third-party dependency versions and archive hashes
configure/build command model
promoted dependency products
promoted CPython dev/runtime products
promoted launcher build inputs
transport and isolated Termux assembly
```

Promoted candidate:

```text
work/termux/stage3b-promoted-runtime/prefix
```

Frozen control:

```text
work/termux/stage2c/runtime/prefix
```

## 7. Stage 3-B Phase 5 completed gates

Canonical behavior:

```text
STAGE3B_PROMOTED_SMOKE=PASS
```

Closure equivalence:

```text
candidate entries                         3155
ELF objects                                 81
DT_NEEDED edges                            329
unresolved edges                             0
Android-system SONAME dlopen               5/5
extension imports                         67/67
candidate/frozen mutation controls         PASS
machine verifier checks                  37/37
STAGE3B_PROMOTED_CLOSURE=PASS
```

Boundary equivalence:

```text
CA contract equivalence                    PASS
corrected direct-zoneinfo equivalence      PASS
uv tzdata fallback equivalence             PASS
candidate/frozen mutation controls         PASS
machine verifier checks                  28/28
STAGE3B_PROMOTED_BOUNDARIES=PASS
```

## 8. Relocation first-run incident

Production shape:

```text
canonical promoted candidate
  -> copy to A
  -> validate A
  -> move A -> B
  -> validate B
```

Functional result:

```text
LOCATION_RECONFIRM[A]=PASS
LOCATION_RECONFIRM[B]=PASS
STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS
STAGE3A_PRODUCTION_RELOCATION_RECONFIRM=PASS
candidate source mutation control         PASS
frozen control mutation control           PASS
```

The initial machine verdict failed only the source/B strict fingerprint.

Retained-tree diagnosis:

```text
source_entry_count          3155
relocated_entry_count       3155
added_count                    0
removed_count                  0
portable_changed_count         0
pycache_path_count              0
portable_pass                true
```

Only strict delta:

```text
lib/python3.14/lib-dynload
  type        directory
  field       st_size
  source      12288
  relocated   20480
```

No file content, file mode, file mtime, symlink target, directory mtime, or path set differed.

Classification:

```text
FINGERPRINT CONTRACT FALSE POSITIVE
```

## 9. Corrected fidelity design

The earlier gate used one fingerprint for two different questions.

### Same-tree mutation

Candidate and frozen prefixes are measured before and after the workflow with the strict metadata-sensitive fingerprint. The same inode trees must remain unchanged.

### Cross-tree product fidelity

Source and copied B are different inode trees. The corrected product contract requires:

```text
same relative path set
same entry type
same mode
same mtime
same regular-file size and SHA-256
same symlink target
```

Directory `st_size` is excluded because it describes directory allocation, not runtime payload. Strict differences remain retained as non-gating diagnostics.

This contract is stronger for actual payload because it hashes every regular file.

Evidence:

```text
docs/evidence/STAGE3B_PHASE5_PROMOTED_RELOCATION_FIDELITY_INCIDENT.md
docs/evidence/STAGE3B_PHASE5_PROMOTED_RELOCATION_FIDELITY_RESOLUTION.md
```

## 10. Current action

Run corrected Gate 4:

```sh
rm -rf \
  work/termux/stage3b-promoted-relocation \
  results/termux/stage3b-promoted-relocation

bash \
  experiments/stage3b-target-validation/validate-promoted-relocation.sh
```

Expected markers:

```text
LOCATION_RECONFIRM[A]=PASS
LOCATION_RECONFIRM[B]=PASS
STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS
RELOCATED_RUNTIME_PORTABLE_FIDELITY_CHECK=PASS
CANDIDATE_RUNTIME_MUTATION_CHECK=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
STAGE3B_PROMOTED_RELOCATION=PASS
```

Primary outputs:

```text
results/termux/stage3b-promoted-relocation/promoted-relocation-verification.json
results/termux/stage3b-promoted-relocation/relocated-runtime-fidelity-check.txt
results/termux/stage3b-promoted-relocation/fidelity-diagnosis/tree-delta.json
```

The frozen Stage 2-C prefix and canonical promoted source remain read-only controls.

## 11. Repository-state split

Tracked state:

```text
src/
scripts/
config/
docs/
experiments/
```

Generated/local state:

```text
.local/
out/
work/
results/
dist/
cache/
tools/
```

Source/scripts/docs use Git. Generated launcher and runtime products use the documented transport workflow, normally rsync.

Collaboration contract:

```text
docs/GITHUB_COLLABORATION_WORKFLOW.md
```

## 12. Reading order

```text
README.md
    -> docs/PROJECT_CONTEXT_STAGE3.md
    -> docs/stages/STAGE2_FINAL.md
    -> docs/stages/STAGE3A_FINAL.md
    -> docs/stages/STAGE3B_SCOPE.md
    -> docs/stages/STAGE3B_PHASE5_SCOPE.md
    -> docs/evidence/
    -> docs/GITHUB_COLLABORATION_WORKFLOW.md
```
