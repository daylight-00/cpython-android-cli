# CPython Android CLI + uv: Stage 3 Project Context

> **Status:** HISTORICAL SNAPSHOT — superseded by `PROJECT_CONTEXT_STAGE3C.md`
> **Snapshot boundary:** Stage 2 frozen, Stage 3-A frozen, Stage 3-B frozen
> **Recorded next work at this snapshot:** Stage 3-C archive and installation contract design
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
Stage 3-B  reproducible build-input promotion           FROZEN
Stage 3-C  distribution archive/installation contract  NEXT
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

CA boundary:

```text
clean default                PASS
explicit Termux CA           PASS
missing path repair          PASS
existing empty regular file  preserved, HTTPS FAIL
```

Timezone boundary:

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

## 6. Frozen Stage 3-B producer result

Stage 3-B made explicit and reproducible:

```text
exact CPython source identity
NDK 27.3.13750724
SDK/API/target identities
host build Python and build tools
third-party dependency versions and archive hashes
configure/build command model
promoted dependency products
promoted CPython dev/runtime products
promoted launcher build inputs and output
transport and isolated Termux assembly
```

Promoted candidate:

```text
work/termux/stage3b-promoted-runtime/prefix
```

Frozen comparison/control runtime:

```text
work/termux/stage2c/runtime/prefix
```

These are generated local products. Git tracks the producer, assembly, validation, documentation, and evidence logic rather than runtime tree bytes.

## 7. Frozen Stage 3-B target-equivalence result

Canonical behavior:

```text
STAGE3B_PROMOTED_SMOKE=PASS
```

Closure equivalence:

```text
candidate entries                         3155
symlinks                                     5
ELF objects                                 81
DT_NEEDED edges                            329
RUNTIME_INTERNAL edges                      80
ANDROID_SYSTEM edges                       249
unresolved edges                             0
inspection errors                            0
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

Production-shape relocation:

```text
LOCATION_RECONFIRM[A]=PASS
LOCATION_RECONFIRM[B]=PASS
STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS
RELOCATED_RUNTIME_PORTABLE_FIDELITY_CHECK=PASS
CANDIDATE_RUNTIME_MUTATION_CHECK=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
STAGE3B_PROMOTED_RELOCATION=PASS
```

Relocation verifier:

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

Portable source/B fingerprint:

```text
79ca7d53f25810b1f5276d18df31f10f2ae981dc24caf67c5f33d37fa75127c8
```

Candidate source/control fingerprint:

```text
834f7aeb2e5266f027b6ee43dd77255079b2e01cf049dad56fda5ef39ce048b0
```

Frozen control fingerprint:

```text
5a14f213bbf069b844a799615ed2b87eb34b48b4251b0a48bf431337e929ce0e
```

Final Stage 3-B markers:

```text
STAGE3B_PHASE5=FROZEN
STAGE3B=FROZEN
```

## 8. Frozen validation lessons

### Validation must not mutate products

The first promoted-closure attempt created 43 bytecode-related entries because isolated children ignored shell `PYTHON*` controls. Child probes were corrected to use explicit `-B`, and the candidate was freshly reassembled rather than cleaned in place.

### Probe flags must preserve the tested input

The direct-zoneinfo probe originally tested `PYTHONTZPATH` under `-I`, which invalidated the test. The corrected probe sanitizes ambient Python variables without ignoring the explicit variable under test.

### Same-tree mutation and cross-tree fidelity are separate

Same-tree before/after controls use strict metadata-sensitive fingerprints.

Cross-tree source/B product fidelity requires:

```text
same relative path set
same entry type, mode and mtime
same regular-file size and SHA-256
same symlink target
```

Directory `st_size` is excluded because it represents filesystem allocation metadata. Strict differences remain non-gating diagnostic evidence.

### Raw aggregate file count is not semantic equality

The frozen historical runtime has `3280` entries and the promoted runtime has `3155`. Complete inventories are retained; acceptance is based on runtime behavior, native closure, extension surface, active identity, host/data boundaries, relocation, source immutability, and relocated-product fidelity.

## 9. Stage 3-C entry boundary

Stage 3-C may consume the frozen Stage 3-B promoted product model and design the distribution archive and installation contract.

The first task is contract design, not immediate packaging implementation:

```text
select archive payload boundary
select install-prefix and ownership model
select metadata and manifest format
select archive reproducibility definition
select installer/upgrade/uninstall transaction model
select validation matrix for unpacked and installed forms
```

Stage 3-C must not reopen producer or runtime semantics merely to simplify packaging. Any archive or installation transformation must preserve or explicitly revalidate:

```text
runtime and subprocess identity
native closure
extension surface
CA integration policy
timezone data boundary
uv and venv workflows
whole-prefix relocatability
product path/content/symlink fidelity
```

Deferred to later contract choices:

```text
uv managed-Python provider metadata
multi-ABI/API release matrix
signing
SBOM
published provenance attestations
```

## 10. Repository-state split

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

## 11. Reading order

```text
README.md
    -> docs/PROJECT_CONTEXT_STAGE3.md
    -> docs/stages/STAGE2_FINAL.md
    -> docs/stages/STAGE3A_FINAL.md
    -> docs/stages/STAGE3B_FINAL.md
    -> docs/evidence/STAGE3B_PHASE5_FINAL_SUMMARY.md
    -> docs/stages/STAGE3_SCOPE.md
    -> docs/evidence/
    -> docs/GITHUB_COLLABORATION_WORKFLOW.md
```
