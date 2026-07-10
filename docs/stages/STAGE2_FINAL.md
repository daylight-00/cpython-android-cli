# Stage 2 Final Freeze: Native Bootstrap, Relocation, and Project Workflow

> **Status:** FROZEN
> **Decision date:** 2026-07-10
> **Target:** Termux on Android arm64
> **Target ABI:** `aarch64-linux-android24`
> **Python baseline:** CPython 3.14.6
> **Selected frontend:** B0 PyConfig auto-discovery
> **Selected bootstrap:** R2 conditional self re-exec
> **Selected project workflow:** canonical repo-local build output + explicit artifact transport + Termux runtime assembly

## 1. Freeze statement

Stage 2 is frozen.

The frozen Stage 2 result is:

```text
B0 PyConfig auto-discovery frontend
        +
R2 conditional self re-exec bootstrap
        +
Termux CA-bundle integration
        +
canonical out/<target>/<profile>/ artifact layout
        +
explicit workstation -> Termux artifact transport
        +
Termux-local runtime assembly
```

The frozen Stage 2 implementation is represented by:

```text
src/launcher/python.c
scripts/lib/project-env.sh
scripts/build/build-launcher.sh
scripts/sync/push-out.sh
scripts/sync/pull-out.sh
scripts/termux/prepare-runtime.sh
scripts/test/smoke-termux.sh
```

The Stage 2 freeze does **not** claim general Android portability, universal ABI coverage, automatic uv-managed Python downloads, or relocation of an external venv after its base runtime is moved.

The freeze claims only what was exercised and observed on the tested environment and workflows described below.

---

## 2. Problem statement

The project started from a CPython 3.14.6 Android runtime built using upstream CPython Android build infrastructure and a locally built `aarch64-linux-android` prefix.

The central Stage 2 problem was not Python path discovery by itself. The actual problem surface was layered:

```text
CLI frontend semantics
Python initialization
Python prefix/path discovery
native dynamic dependency lookup
CA trust-store integration
subprocess re-entry
venv identity
uv interpreter selection
artifact movement and runtime relocation
```

Stage 1 established that the runtime could behave as a practical Termux CLI interpreter when two external runtime requirements were explicitly supplied:

```text
LD_LIBRARY_PATH=<cpython-prefix>/lib
SSL_CERT_FILE=<termux-prefix>/etc/tls/cert.pem
```

Stage 2 asked:

> Can the runtime discover and activate enough of that environment itself, without regressing Python CLI, subprocess, venv, uv, HTTPS, or relocation behavior?

The answer, on the tested target, is yes with the frozen R2 design.

---

## 3. Pre-Stage-2 frozen input

Stage 2 did not start from an unknown frontend. Stage 1-B had already frozen the Python initialization decision.

### 3.1 B0 frontend

The selected Stage 1-B frontend is:

```c
PyConfig config;
PyStatus status;

PyConfig_InitPythonConfig(&config);

status = PyConfig_SetBytesArgv(&config, argc, argv);
status = Py_InitializeFromConfig(&config);

PyConfig_Clear(&config);
return Py_RunMain();
```

The design intentionally does **not** set `config.home`.

The rejected B1 variant did set `config.home` from `CPYTHON_HOME`. It passed with a correct value but failed hard with an incorrect value when startup could not import `encodings`. That negative control demonstrated that explicit home injection created a real additional runtime dependency.

Therefore Stage 2 inherited:

```text
Python initialization:
  B0 PyConfig auto-discovery

external native-loader state:
  still required before Stage 2

external CA state:
  still required before Stage 2
```

This separation matters: Stage 2 changed bootstrap and host integration, not the frozen Python initialization model.

---

## 4. Stage 2-A: strategy comparison

Stage 2-A compared three bootstrap strategies.

### 4.1 S2-E — setenv-only

Model:

```text
process starts
    |
launcher derives <prefix>/lib
    |
setenv("LD_LIBRARY_PATH", ...)
    |
enter Python in the same process
```

Observed behavior:

```text
current-process native imports: FAIL
child process inheriting updated environment: PASS
```

Interpretation:

```text
setenv()
    changes environment state exported to future execs

setenv()
    does not retroactively restart the current process dynamic loader
```

This control was important because it separated environment mutation from process-start loader state.

S2-E was rejected as the final bootstrap mechanism.

### 4.2 S2-U — bionic linker-update experiment

Model:

```text
resolve android_update_LD_LIBRARY_PATH dynamically
        |
update linker search state in current process
        |
enter Python without re-exec
```

The experiment attempted symbol resolution through the tested `RTLD_DEFAULT` path.

Observed behavior:

```text
android_update_LD_LIBRARY_PATH:
  unavailable through the tested resolution path

Python startup through this experiment:
  not reached successfully
```

This experiment established a target-specific negative result for the tested symbol lookup path. It is not generalized into a statement about every Android release or every possible private-linker technique.

S2-U was not selected.

### 4.3 S2-R — self re-exec

Model:

```text
process start
    |
derive runtime prefix
    |
set required environment
    |
execv(self, original argv)
    |
fresh process start with prepared environment
    |
enter B0 PyConfig frontend
```

Observed high-level result:

```text
native stdlib imports: PASS
HTTPS: PASS
subprocess: PASS
uv venv: PASS
venv native imports: PASS
uv run: PASS
```

S2-R was selected for refinement.

---

## 5. Stage 2-B: R2 fixed-point refinement

The initial re-exec prototype had two undesirable properties:

```text
1. repeated launcher invocation could prepend the same libdir again
2. every sys.executable child could pay an unnecessary additional re-exec
```

R2 removed the private recursion guard and used the actual loader-path state as the fixed point.

### 5.1 R2 state machine

```text
read /proc/self/exe
        |
        v
derive executable path
        |
        v
derive <prefix>
        |
        v
derive <prefix>/lib
        |
        v
inspect current LD_LIBRARY_PATH components
        |
        +-- required libdir absent
        |       normalize list
        |       prepend required libdir
        |       configure CA state
        |       set environment
        |       execv(actual executable, original argv)
        |
        +-- required libdir present
                normalize duplicate required entries
                configure/repair CA state
                enter B0 PyConfig directly
```

### 5.2 Why the fixed point works

Define:

```text
R = exact string component equal to <derived-prefix>/lib
```

The transition is:

```text
R absent at process start
    -> construct environment containing exactly one R
    -> execv

fresh process starts
    -> R present
    -> direct Python initialization
```

Thus the intended top-level clean trace is:

```text
reexec
    ->
direct
```

A subprocess invoked through `sys.executable` inherits the already-correct environment and therefore takes:

```text
direct
```

without another bootstrap re-exec.

No private recursion variable is necessary.

### 5.3 `LD_LIBRARY_PATH` normalization semantics

R2 treats `LD_LIBRARY_PATH` as a colon-separated component list.

The normalization rule is:

```text
required component absent:
  prepend it

required component present once:
  preserve it

required component duplicated:
  keep first exact occurrence
  remove later exact duplicates

other components:
  preserve relative order

empty components:
  preserve list semantics
```

The comparison is exact component equality, not substring matching.

Example:

```text
input:
  /wrong/path:/runtime/prefix/lib:/runtime/prefix/lib:/other

output:
  /wrong/path:/runtime/prefix/lib:/other
```

Wrong-path profile behavior observed in validation:

```text
input:
  /wrong/path

post-bootstrap:
  <derived-prefix>/lib:/wrong/path
```

The required runtime libdir is activated while unrelated existing path components remain available.

### 5.4 Executable discovery

The launcher resolves:

```text
/proc/self/exe
```

and derives:

```text
<prefix>/bin/<launcher>
        -> parent
<prefix>/bin
        -> parent
<prefix>
        -> append /lib
<prefix>/lib
```

This design intentionally uses the actual executable location rather than:

```text
argv[0]
current working directory
build-time absolute prefix
shell symlink text
```

The Stage 2-B external-symlink test showed that invocation through an external symlink still allowed correct runtime-prefix derivation from the actual executable location.

### 5.5 CA-bundle policy

CA configuration is independent from native-loader activation.

R2 uses this policy:

```text
existing SSL_CERT_FILE points to a regular file?
    yes -> preserve
    no  -> try $PREFIX/etc/tls/cert.pem
            |
            +-- regular file -> use it
            |
            +-- otherwise try fixed Termux fallback:
                /data/data/com.termux/files/usr/etc/tls/cert.pem
```

If no CA bundle is found, the launcher warns but does not convert that condition into a synthetic Python-startup failure.

This separation allows the following profile:

```text
native loader already ready
SSL_CERT_FILE invalid
    -> repair CA in-process
    -> no re-exec required
```

### 5.6 Launcher-level RUNPATH

The Stage 2-C build places:

```text
RUNPATH=$ORIGIN/../lib
```

on the launcher.

This solves the launcher's direct lookup of:

```text
libpython3.14.so
```

relative to the runtime prefix layout.

This RUNPATH must not be confused with the broader native dependency problem exercised by extension modules and their transitive native dependencies. Stage 2's bootstrap environment remains relevant for that broader dependency surface.

---

## 6. Stage 2-B main validation matrix

The final validator used five environment profiles.

### 6.1 Profiles

```text
clean
  LD_LIBRARY_PATH unset
  SSL_CERT_FILE unset

ready
  correct <prefix>/lib already present
  correct Termux CA bundle present

wrong-ld
  unrelated incorrect loader path present
  valid CA present

wrong-ca
  correct loader path present
  SSL_CERT_FILE points to nonexistent path

duplicate
  <prefix>/lib appears twice
  valid CA present
```

### 6.2 Results

```text
PROFILE_RESULT[clean]=PASS
PROFILE_RESULT[ready]=PASS
PROFILE_RESULT[wrong-ld]=PASS
PROFILE_RESULT[wrong-ca]=PASS
PROFILE_RESULT[duplicate]=PASS
```

Additional checks:

```text
clean trace:
  reexec -> direct
  PASS

ready trace:
  direct only
  PASS

unrelated cwd:
  PASS

external symlink invocation:
  PASS

subprocess re-entry:
  PASS

subprocess child redundant re-exec avoidance:
  PASS

uv venv:
  PASS

clean venv interpreter launch:
  PASS

venv identity:
  PASS

uv run:
  PASS
```

### 6.3 Clean-profile final state

Observed clean-profile state included:

```text
LD_LIBRARY_PATH:
  exactly <runtime-prefix>/lib

SSL_CERT_FILE:
  /data/data/com.termux/files/usr/etc/tls/cert.pem

sys.prefix:
  runtime prefix

sys.base_prefix:
  runtime prefix

HTTPS:
  status 200

sys.platform:
  android

sysconfig.get_platform():
  android-24-arm64_v8a
```

### 6.4 Subprocess trace invariant

The intended and observed logical action sequence was:

```text
parent clean launch:
  reexec
  direct

child via sys.executable:
  direct
```

Combined:

```text
reexec
direct
direct
```

This is a key Stage 2-B property.

---

## 7. Stage 2-B relocation validation

### 7.1 Test shape

The relocation test performed:

```text
copy prepared runtime prefix to location A
        |
validate A
        |
move entire prefix A -> B
        |
validate B
```

At each location it exercised:

```text
base runtime probe
native stdlib imports
HTTPS
subprocess re-entry
uv venv creation
clean venv launch
uv run
```

### 7.2 Result matrix

```text
RELOCATION_PROBE[A]=0
RELOCATION_UV_VENV[A]=0
RELOCATION_VENV_RUN[A]=0
RELOCATION_UV_RUN[A]=0

move A -> B

RELOCATION_PROBE[B]=0
RELOCATION_UV_VENV[B]=0
RELOCATION_VENV_RUN[B]=0
RELOCATION_UV_RUN[B]=0
```

### 7.3 Path update behavior

At A, observed runtime identity used A-based paths.

After moving the whole prefix to B, observed values changed to B-based paths, including:

```text
sys.executable
sys.prefix
sys.base_prefix
LD_LIBRARY_PATH
uv-selected base interpreter
uv-created venv base_prefix
uv-run ephemeral environment base_prefix
```

No stale A path was accepted as the runtime identity after the move.

### 7.4 Exact relocation claim

Frozen claim:

> The tested runtime prefix can be relocated as a unit, and the R2 launcher re-derives its native runtime path from the actual executable location.

Not claimed:

> An external venv created before moving its base runtime will necessarily continue to work after the base runtime is moved.

That scenario was not exercised by the Stage 2-B relocation test.

---

## 8. Stage 2-C: project-workflow synthesis

Stage 2-C did not select a new runtime architecture.

Its question was:

> Does the selected Stage 2-B R2 + B0 architecture survive a cleaned repository, build, transport, assembly, and smoke-test workflow without the old date-based experiment wiring?

The answer was yes on the tested workflow.

### 8.1 Repository path model

Tracked project state:

```text
src/
scripts/
config/
docs/
experiments/
```

Machine-local configuration:

```text
.local/env
```

Generated state:

```text
out/
work/
results/
dist/
cache/
```

External SDK/upstream working trees kept repo-local but untracked:

```text
tools/
```

### 8.2 Canonical build output

The workstation build writes directly to:

```text
out/aarch64-linux-android24/release/
├── bin/
│   └── python3.14
└── metadata/
    └── build-info.txt
```

Observed launcher properties:

```text
ELF 64-bit LSB PIE
Machine: ARM aarch64
interpreter: /system/bin/linker64
RUNPATH: $ORIGIN/../lib
NEEDED: libpython3.14.so
NEEDED: libdl.so
NEEDED: libm.so
NEEDED: liblog.so
NEEDED: libc.so
```

### 8.3 Build input provenance

The Stage 2-C launcher build used the development prefix at:

```text
experiments/bootstrap-android-build/android-python-work/prefix
```

The build script requires that prefix to contain:

```text
include/python3.14/Python.h
include/python3.14/pyconfig.h
lib/libpython3.14.so
```

This prefix is currently the canonical development input by provenance and practical use, even though its location under `experiments/` is architecturally awkward and may be normalized in a later build-reproducibility stage.

The freeze does not silently reinterpret Stage 2 test copies such as `pristine-test/prefix` as canonical build inputs.

### 8.4 Artifact transport topology

The initial helper assumed workstation-initiated push:

```text
workstation
    -> rsync push
Termux
```

The successful tested topology used Termux-initiated pull because Termux inbound connectivity was unavailable:

```text
workstation canonical out tree
        ^
        |
Termux-initiated rsync pull
```

This transport distinction does not change artifact semantics. The authoritative build artifact remains:

```text
workstation out/<target>/<profile>/
```

and the Termux checkout receives a mirror at the same repo-relative path.

Both push and pull helpers are retained as topology choices.

---

## 9. Stage 2-C end-to-end smoke result

The successful smoke run used the assembled runtime at:

```text
work/termux/stage2c/runtime/prefix
```

### 9.1 Base runtime

Observed:

```text
sys.executable:
  work/termux/stage2c/runtime/prefix/bin/python

sys.prefix:
  work/termux/stage2c/runtime/prefix

sys.base_prefix:
  work/termux/stage2c/runtime/prefix

LD_LIBRARY_PATH:
  work/termux/stage2c/runtime/prefix/lib

SSL_CERT_FILE:
  /data/data/com.termux/files/usr/etc/tls/cert.pem

HTTPS status:
  200
```

The base-runtime subprocess re-entered the same assembled prefix.

### 9.2 uv venv

uv selected:

```text
work/termux/stage2c/runtime/prefix/bin/python
```

and created:

```text
results/termux/stage2c/venv
```

Observed venv identity:

```text
sys.executable:
  results/termux/stage2c/venv/bin/python

sys.prefix:
  results/termux/stage2c/venv

sys.base_prefix:
  work/termux/stage2c/runtime/prefix
```

Therefore:

```text
sys.prefix != sys.base_prefix
```

with the assembled Stage 2-C runtime correctly preserved as the base interpreter.

### 9.3 uv run

The successful `uv run` environment used an ephemeral interpreter under:

```text
~/.cache/uv/builds-v0/.tmp.../bin/python
```

with:

```text
sys.prefix:
  ephemeral uv environment

sys.base_prefix:
  work/termux/stage2c/runtime/prefix
```

`anyio` installation and import succeeded.

The run ended with:

```text
STAGE2C_SMOKE=PASS
```

### 9.4 uv hardlink warning

Observed warning:

```text
Failed to hardlink files; falling back to full copy
```

This was non-fatal. Package installation completed and the smoke test passed.

Frozen interpretation:

```text
functional uv behavior:
  PASS

hardlink optimization in tested filesystem arrangement:
  unavailable

fallback copy mode:
  successful
```

This warning is not a Stage 2 failure.

---

## 10. Final validation matrix

```text
Stage 1-A baseline
  explicit native loader path                PASS
  explicit CA bundle                         PASS
  native stdlib                              PASS
  HTTPS                                      PASS
  uv venv                                    PASS
  venv identity                              PASS
  uv pip / package import                    PASS
  uv run                                     PASS

Stage 1-B
  B0 functional parity                       PASS
  B0 semantic differential surface           PASS
  B1 correct-home control                    PASS
  B1 wrong-home negative control             EXPECTED FAIL
  B0 selected                                YES

Stage 2-A
  S2-E current process                       FAIL
  S2-E inherited child                       PASS
  S2-U tested symbol lookup                  UNAVAILABLE
  S2-R full comparison surface               PASS
  S2-R selected for refinement               YES

Stage 2-B R2
  clean profile                              PASS
  ready profile                              PASS
  wrong-ld profile                           PASS
  wrong-ca profile                           PASS
  duplicate profile                          PASS
  clean trace reexec -> direct               PASS
  ready direct-only                          PASS
  unrelated cwd                              PASS
  external symlink invocation                PASS
  subprocess direct child                    PASS
  uv venv                                    PASS
  clean venv launch                          PASS
  venv identity                              PASS
  uv run                                     PASS

Stage 2-B relocation
  location A probe                           PASS
  location A uv venv                         PASS
  location A venv launch                     PASS
  location A uv run                          PASS
  whole-prefix move A -> B                   DONE
  location B probe                           PASS
  location B uv venv                         PASS
  location B venv launch                     PASS
  location B uv run                          PASS

Stage 2-C workflow
  repo-relative config model                 PASS
  workstation canonical build               PASS
  Android arm64 ELF output                   PASS
  canonical out path                         PASS
  artifact transport                         PASS
  Termux runtime assembly                    PASS
  base runtime                               PASS
  native stdlib                              PASS
  HTTPS                                      PASS
  subprocess                                 PASS
  uv venv                                    PASS
  venv identity                              PASS
  uv run                                     PASS
  final marker STAGE2C_SMOKE=PASS            PASS
```

---

## 11. Frozen architecture

The final Stage 2 architecture is:

```text
                           WORKSTATION

CPython Android dev prefix
        |
        | headers + libpython
        v
src/launcher/python.c
        |
        | NDK cross compile
        v
out/aarch64-linux-android24/release/bin/python3.14
        |
        | artifact transport
        | push or pull depending network topology
        v

                             TERMUX

out/.../bin/python3.14
        +
pristine runtime archive
        |
        v
work/termux/stage2c/runtime/prefix
        |
        v
prefix/bin/python3.14
        |
        +-- launcher RUNPATH -> $ORIGIN/../lib
        |
        +-- /proc/self/exe
        |       -> derive prefix
        |       -> derive prefix/lib
        |
        +-- normalize LD_LIBRARY_PATH
        |
        +-- discover/preserve CA bundle
        |
        +-- loader path absent at process start
        |       -> execv(actual executable, original argv)
        |
        +-- loader path present
                -> B0 PyConfig
                -> Py_RunMain
                |
                +-- normal CLI
                +-- sys.executable subprocess
                +-- uv venv
                +-- venv interpreter
                +-- uv run ephemeral environment
```

---

## 12. Invariants future work must preserve

Any future Stage 3 experiment must preserve or intentionally re-evaluate these invariants.

### 12.1 CLI invariant

The frontend must preserve normal CPython CLI behavior for the tested semantic surface, including argument handling and `Py_RunMain` behavior.

### 12.2 Python discovery invariant

Do not introduce an unnecessary explicit `config.home` dependency without evidence.

### 12.3 Loader invariant

A clean top-level runtime must activate the derived runtime native path before extension-module dependency loading is required.

### 12.4 Subprocess invariant

A child entered through `sys.executable` with an inherited ready loader environment should not pay an unnecessary extra re-exec.

### 12.5 CA invariant

Native-loader repair and CA repair remain separate concerns.

### 12.6 venv invariant

A venv created from the selected runtime must preserve:

```text
sys.prefix = venv
sys.base_prefix = selected base runtime
```

### 12.7 uv invariant

uv must be able to consume the interpreter through explicit `--python` selection without Python downloads.

### 12.8 relocation invariant

Whole-prefix relocation should continue to derive runtime paths from actual executable location rather than build-time absolute paths.

### 12.9 repository invariant

Current scripts must not depend on historical date-based paths such as `~/tmp/260703` or `~/tmp/260704`.

### 12.10 artifact invariant

Canonical generated launcher output remains under:

```text
out/<target>/<profile>/
```

and is separate from Git-tracked source and experiment history.

---

## 13. Explicitly rejected or deferred directions

### Rejected for Stage 2

```text
setenv-only native bootstrap
explicit PyConfig config.home dependency
reliance on tested unavailable linker-update symbol path
unconditional repeated re-exec
machine-specific absolute runtime prefix wiring
stage-local production output directories
cross-machine symlink artifact wiring
```

### Deferred to later research

```text
fully reproducible CPython build dependency promotion
canonical rebuilding of the current development prefix
automatic artifact manifests beyond current build-info
multi-ABI support
multi-API-level matrix
automatic uv-managed Python download integration
standalone distribution packaging
broad ELF dependency closure engineering
possible reduction or elimination of external host CA dependency
external venv behavior after moving its base runtime
release artifact signing and provenance metadata
```

---

## 14. Evidence references

Frozen Stage 2 evidence summaries:

```text
docs/evidence/STAGE2B_VALIDATION_SUMMARY.md
docs/evidence/STAGE2B_RELOCATION_SUMMARY.md
docs/evidence/STAGE2C_E2E_SMOKE_SUMMARY.md
```

Historical implementation and harness provenance:

```text
experiments/stage2a-bootstrap-strategies/
experiments/stage2b-conditional-reexec/
```

Current selected implementation:

```text
src/launcher/python.c
```

---

## 15. Freeze decision

Final decision:

```text
Stage 2-A:
  comparison complete

Stage 2-B:
  R2 selected
  main validation PASS
  relocation PASS

Stage 2-C:
  canonical build PASS
  artifact transport PASS
  runtime assembly PASS
  end-to-end smoke PASS

STAGE 2:
  FROZEN
```

The next project phase should begin with a separate Stage 3 question rather than silently extending Stage 2.
