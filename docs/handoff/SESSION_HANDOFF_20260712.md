# Session Handoff — 2026-07-12

> **Repository:** `daylight-00/cpython-android-cli`
> **Target:** Termux on Android arm64
> **Current stage:** Stage 3-C Phase 5 Gate 1
> **Read first:** `docs/handoff/COLLABORATION_PROTOCOL.md`
> **Identity ledger:** `docs/handoff/STAGE3C_EVIDENCE_LEDGER.md`

## Executive state

Stage 3-C Phases 1–4 are frozen.

Phase 4 integrated durability was accepted from authoritative Termux evidence and is fully closed:

```text
STAGE3C_PHASE4=FROZEN
```

The active work is now:

```text
Stage 3-C Phase 5 Gate 1
installed runtime-base baseline
authoritative Termux result pending
```

At the time this handoff was authored, the active code and scope baseline on `main` was:

```text
c216bc21670620024eef307688fd6fd5e3d267ef
Freeze Phase 4 and open installed runtime validation (#27)
```

The handoff-document merge adds a newer documentation-only main commit. It does not change the Phase 5 Gate 1 implementation.

## Required reading order for the successor

```text
1. docs/handoff/COLLABORATION_PROTOCOL.md
2. docs/handoff/SESSION_HANDOFF_20260712.md
3. docs/handoff/STAGE3C_EVIDENCE_LEDGER.md
4. docs/stages/STAGE3C_SCOPE.md
5. docs/stages/STAGE3C_PHASE4_FINAL.md
6. docs/stages/STAGE3C_PHASE5_SCOPE.md
7. experiments/stage3c-installed-runtime-baseline/README.md
```

Do not redesign Phase 5 Gate 1 before reading the existing implementation and claim boundary.

## Last authoritative result

Accepted bundle:

```text
stage3c-phase4-integrated-durability-results-20260712-082135.tgz
```

Archive identity:

```text
sha256
  76bb78f200d9836d96f677cc1eca1e2f1483186f3655efa17a8e1f2361bd0187

size
  23,917,838 bytes

members
  325

regular files / directories
  300 / 25

unsafe, link, or special entries
  0
```

Result identity:

```text
result-index sha256
  878ed426720c48f8d0240e3e4e141ff3434426a30d3be9230da23dd5eba0a4ce

indexed files
  294

independent hash, size, and mode mismatches
  0
```

Machine result:

```text
source integration             29/29 PASS
recovery replay                55/55 PASS
recovery verifier              82/82 PASS
durability replay              64/64 PASS
durability verifier            53/53 PASS
focused exercises              20/20 PASS
trace verifier                 29/29 PASS
overall verifier               36/36 PASS
workflow return codes          all 0
```

Trace result:

```text
files                  25
events             42,941
ordering violations     0
```

The final Phase 4 evidence and frozen contract are already recorded in:

```text
docs/evidence/STAGE3C_PHASE4_INTEGRATED_DURABILITY_RESULT.md
docs/stages/STAGE3C_PHASE4_FINAL.md
docs/stages/STAGE3C_PHASE4_SCOPE.md
```

## Active Phase 5 Gate 1 purpose

The gate asks:

> Does `runtime-base` remain exact, functional, and natively closed after installation through the frozen Phase 4 engine?

The runtime under test must be the newly installed prefix.

The following are forbidden substitutions:

```text
Stage 3-B promoted prefix as the runtime under test
Phase 1 isolated runtime as the runtime under test
direct archive assembly that bypasses Phase 4 installation
synthetic registry state
```

The promoted prefix may be used only as immutable tool Python by the workflow.

## Phase 5 Gate 1 required result

Installation state:

```text
create actions                 714
registry mutation count        715
engine verify                  PASS
registry artifacts               1
registry owned rows            714
manifest-to-registry mapping   exact
installed tree fingerprint     exact
installed prefix mutation      none
```

Runtime state:

```text
Python                         3.14.6
platform                       android
machine                        aarch64
SOABI                          cpython-314-aarch64-linux-android
MULTIARCH                      aarch64-linux-android
sys.executable                 installed prefix/bin/python
sys.prefix/base_prefix         installed prefix
sysconfig paths                inside installed prefix
HTTPS                          status 200
subprocess identity            installed prefix
```

uv state:

```text
uv venv                        PASS
venv base_prefix               installed prefix
uv run --with anyio            PASS
uv run interpreter identity    installed prefix
```

Native state:

```text
symlinks                         3
ELF objects                     81
DT_NEEDED edges                329
RUNTIME_INTERNAL edges          80
ANDROID_SYSTEM edges           249
unresolved edges                 0
inspection errors                0
system SONAME dlopen           5/5
extension imports             67/67
```

Independent verifier:

```text
80/80 checks
```

## First action in the successor session

The assistant should not invent another gate. The first action is to tell the user to run the existing Gate 1 workflow.

```sh
cd "$HOME/projects/cpython-android-cli"

git pull --ff-only
git log -3 --oneline

bash \
  experiments/stage3c-installed-runtime-baseline/run-installed-runtime-baseline.sh
```

Expected code/scope baseline in recent history:

```text
c216bc2 Freeze Phase 4 and open installed runtime validation (#27)
```

A newer handoff-document commit is expected above it after this document is merged.

## Expected final markers

```text
INSTALLED_RUNTIME_BASELINE_ACCEPTED_INPUTS=PASS
INSTALLED_RUNTIME_BASELINE_INSTALL=714/714 PASS
INSTALLED_RUNTIME_BASELINE_REGISTRY=714/714 PASS
INSTALLED_RUNTIME_BASELINE_SMOKE=PASS
INSTALLED_RUNTIME_BASELINE_HTTPS=200 PASS
INSTALLED_RUNTIME_BASELINE_UV_VENV=PASS
INSTALLED_RUNTIME_BASELINE_UV_RUN=PASS
INSTALLED_RUNTIME_BASELINE_NATIVE_CLOSURE=81/329/0 PASS
INSTALLED_RUNTIME_BASELINE_EXTENSION_IMPORTS=67/67 PASS
INSTALLED_RUNTIME_BASELINE_VERIFICATION=80/80 PASS
INSTALLED_RUNTIME_BASELINE_MUTATION_CHECK=PASS
STAGE3C_PHASE5_INSTALLED_RUNTIME_BASELINE=PASS
```

## Result bundle command

After the workflow completes, the user should upload this TGZ rather than paste logs:

```sh
RESULTS="$PWD/results/termux/stage3c-phase5-installed-runtime-baseline"
ARCHIVE="$HOME/Downloads/stage3c-phase5-installed-runtime-baseline-results-$(date +%Y%m%d-%H%M%S).tgz"

tar czf "$ARCHIVE" "$RESULTS"
printf 'upload: %s\n' "$ARCHIVE"
```

## Required inspection after upload

The successor must independently inspect:

```text
archive SHA-256, size, and safe member types
result-index integrity
workflow return codes
installed-runtime verifier 80/80
fresh install result: 714 creates and 715 mutations
registry artifact and owned-path counts
manifest-to-registry equality
installed-tree fingerprint and path count
runtime version and all prefix identities
HTTPS 200
subprocess identity
uv venv and uv run identities
81 ELF / 329 edges / 0 unresolved
5/5 system SONAME dlopen
67/67 extension imports
installed prefix before/after fingerprint
Phase 4 input before/after fingerprint
absence of installed pycache and special paths
canonical generated evidence
```

If the gate fails, preserve the TGZ and write a dedicated failure evidence document before changing code.

If the gate passes, freeze Phase 5 Gate 1 before opening Gate 2 relocation.

## Gate 1 claim boundary

A PASS proves exact installed runtime-base identity and behavior only on the original installation path after installation through the frozen Phase 4 engine.

It does not prove:

```text
installed-prefix relocation
same-version reinstall after this baseline
later corruption repair
addon lifecycle
exact uninstall preservation
upgrade
downgrade
physical power-loss persistence
```

Do not combine Gate 1 with relocation or lifecycle work.

## Planned later gates

Only after Gate 1 is frozen:

```text
Gate 2
  relocate the complete installed prefix or installation root
  preserve tree and registry consistency
  revalidate runtime, HTTPS, uv, and native closure
  reject stale source-prefix references

Gate 3
  exact same-version reinstall NOOP
  registered corruption repair
  modified owned leaf preservation
  unowned sentinel preservation
  addon composition and removal
  runtime dependency enforcement
  exact uninstall ownership boundary

Gate 4
  explicit upgrade and downgrade
  only after a second complete frozen product identity exists
```

Synthetic version labels are not acceptable evidence for Gate 4.

## Recent failure history that must remain visible

```text
Gate 3 first recovery run
  hardlink seed clone failed with EACCES on Termux
  corrected to independent copies with inode-separation checks

Gate 5A first inventory run
  add_intent and mark_applied remained UNKNOWN
  gate correctly failed
  both checkpoint calls classified as transaction-metadata
```

These failures are preserved in tracked evidence. Do not delete or rewrite them as if the first run passed.

## Repository history caution

An accidental `placeholder` file was briefly committed to `main` during an earlier connector operation and immediately removed in the next commit. The final tree contains no placeholder file. The two compensating history commits remain in Git history and must not be misrepresented as product changes.

## Handoff completion condition

The successor session is correctly onboarded when it can state all of the following without guessing:

```text
Phase 4 is frozen
Phase 5 Gate 1 is active
Termux TGZ evidence is authoritative
current workflow is installed-runtime-baseline
verifier count is 80/80
runtime under test is the installed prefix
relocation and lifecycle remain deferred
```
