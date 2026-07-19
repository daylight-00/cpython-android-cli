# Upstream-Thin Research and Design Plan

> **Status:** design and experiment planning document  
> **Scope:** upstream-derived, Astral-structured Android/Bionic standalone CPython  
> **Primary distribution reference:** Astral `python-build-standalone`  
> **Secondary runtime reference:** official Python.org Android CPython package and the BeeWare dependency products selected by CPython  
> **Out of scope:** full project-owned CPython/dependency producer, independent static/shared topology, PGO/LTO production, expanded desktop module surface, and host-profile-specific product architecture

---

## 1. Purpose

This document defines the remaining research and design work required to produce an **upstream-thin** Android/Bionic standalone CPython distribution.

The target is not merely a Python runtime that happens to execute under Termux. The target is:

> A pure Bionic-native, highly portable standalone CPython distribution that consumes the official Python.org Android product, adopts Astral's standalone archive and consumer architecture wherever binary inheritance permits, and diverges only where Android makes the Astral mechanism structurally unavailable.

The distribution must not require Termux native libraries, hard-coded Termux paths, or Termux-specific product identity. Termux may be a qualification environment, but it is not an ABI provider or architectural dependency.

The current project has already proved that the upstream-derived runtime can support:

- a normal Python command-line interface;
- whole-prefix relocation;
- isolated imports of the complete observed native-extension surface;
- HTTPS with an externally supplied trust source;
- subprocess execution and child-interpreter re-entry;
- fresh virtual environments;
- offline pip installation;
- explicit-interpreter uv workflows;
- Android wheel identity;
- pure Bionic native-library closure on the tested device.

Those results remain valuable evidence. However, some mechanisms used to obtain them—especially `LD_LIBRARY_PATH` mutation, conditional self re-execution, and Termux-specific certificate discovery—are not the intended final upstream-thin design.

This document separates:

1. evidence that should be retained;
2. implementation that should be retained;
3. implementation that should be replaced;
4. unresolved design decisions;
5. experiments required before the clean release repository can be initialized.

---

## 2. Upstream-Thin Definition

The upstream-thin producer begins with the exact official Android package:

```text
verified Python.org Android package
    +
deterministic binary-derived transformations
    +
minimum standalone launcher
    +
Android-mandatory adaptation
    +
Astral-compatible archive, metadata, and consumer contract
    =
upstream-thin distribution
```

### 2.1 Allowed project ownership

The upstream-thin project may own:

- upstream artifact acquisition and checksum verification;
- deterministic extraction and reassembly;
- a minimal standalone executable;
- ELF `RUNPATH` transformations where required;
- runtime and development metadata normalization;
- archive layout and flavor derivation;
- `PYTHON.json`;
- pinned pure-Python or data payloads such as pip or `tzdata`;
- licenses, provenance, mutation manifests, checksums, and release indexes;
- static and runtime qualification;
- uv-facing artifact identity and catalog integration;
- Android-specific adaptation that cannot be inherited from Astral.

### 2.2 Inherited producer decisions

The upstream-thin project does not independently own:

- CPython source patches;
- dependency source recipes;
- dependency versions;
- Android NDK selection;
- Android API floor;
- upstream extension inclusion;
- built-in versus shared extension topology;
- static versus shared dependency topology;
- source-level PGO/LTO;
- the presence or absence of static `libpython`;
- object-level CPython reconstruction material.

### 2.3 Deferred to source-thin or source-full

The following cannot be changed while remaining upstream-thin:

- CPython `getpath` source patches;
- interpreter linkage against static `libpython`;
- Astral's default-static extension topology;
- static relinking of existing OpenSSL, SQLite, compression, or FFI dependencies;
- complete `PYTHON.json.build_info` object graphs;
- PGO, LTO, BOLT, tail-call interpreter, free-threaded, JIT, or debug build profiles;
- API-36 compile-time behavior;
- changes to the official native module surface.

---

## 3. Status Vocabulary

| Disposition | Meaning |
|---|---|
| **Preserve** | Existing evidence and implementation are suitable for the final upstream-thin design. |
| **Preserve evidence, reimplement** | The current project proved feasibility, but the mechanism differs from the intended Astral-style design. |
| **Design required** | The boundary is understood, but the final product policy or representation has not been selected. |
| **Experiment required** | The capability or implementation boundary is not yet established with sufficient evidence. |
| **Defer** | The requirement cannot be satisfied within upstream-thin and belongs to a source-producing profile or a separate product decision. |

---

## 4. Executive Status Matrix

| Area | Existing result | Final upstream-thin expectation | Disposition |
|---|---|---|---|
| Official package acquisition | Upstream and producer provenance understood | Exact Python.org package must be the direct product input | **Experiment required** |
| Standalone CLI feasibility | Proven with a custom PyConfig launcher | Minimal CPython-like executable with no unnecessary custom initialization | **Preserve evidence, reimplement** |
| Pure Bionic native closure | No observed Termux native edges; no unresolved edges | Keep semantic closure verifier | **Preserve** |
| Native extension surface | 67/67 observed extension imports passed | Re-run after every transformation | **Preserve** |
| Whole-prefix relocation | A-to-B relocation passed | Reproduce without project-required `LD_LIBRARY_PATH` | **Preserve evidence, reimplement** |
| Native loader resolution | Conditional self re-exec succeeded | Object-relative ELF search paths | **Preserve evidence, reimplement** |
| Active Python paths | Runtime paths re-rooted correctly | Maintain as regression requirement | **Preserve** |
| Development/sysconfig paths | Absolute residue fully classified | Normalize to portable runtime and SDK semantics | **Design and experiment required** |
| Subprocess | Child execution and identity proved | Qualify the wider core API matrix | **Preserve plus experiment** |
| Virtual environments | Fresh venv and relocated-base workflows passed | Extend symlink, copied venv, and pre-existing venv matrix | **Preserve plus experiment** |
| pip | Offline installation into venv passed | Decide and validate Astral-style pinned base pip | **Design and experiment required** |
| uv | Explicit-interpreter workflows passed | Define Astral-like artifact/catalog consumption | **Preserve plus experiment** |
| HTTPS | Successful through Termux CA discovery | Replace host-specific fallback with portable policy | **Preserve evidence, reimplement** |
| Timezone data | First-party `tzdata` fallback passed | Select bundle/dependency policy | **Design required** |
| Archive safety | Deterministic serialization and validation exist | Reuse mechanics within Astral hierarchy | **Preserve mechanics, redesign structure** |
| `PYTHON.json` | Not yet authoritative | Produce an Astral-compatible runtime description | **Design and experiment required** |
| Native extension SDK | Headers and shared `libpython` exist | Build, package, install, import, and relocate a test wheel | **Experiment required** |
| Minimum API | Compile floor known; minimum runtime not proved | Real or credible API-24 qualification | **Experiment required** |
| 16 KiB pages | Not established | Validate complete assembled product | **Experiment required** |
| `multiprocessing` | Not qualified | Produce a capability-by-capability result | **High-risk experiment required** |
| API-36 compile floor | Not expressible through official bytes | Source-producing research only | **Defer** |

---

## 5. Evidence That Should Be Preserved

### 5.1 Pure Bionic native closure

The current project established that, on the accepted test target, the runtime closure was resolved entirely by:

```text
runtime-internal libraries
+
Android public system libraries
```

with:

```text
Termux native dependency edges = 0
unresolved native dependency edges = 0
```

This is one of the strongest existing results and directly supports the upstream-thin architecture.

The exact historical counts—such as the number of ELF objects, `DT_NEEDED` edges, or extension modules—should remain observations for the frozen package. They should not become permanent cross-version contracts.

The final semantic requirements should be:

```text
unresolved dependency edges             = 0
unexpected external native providers    = 0
Termux native providers                 = 0
required extension import failures      = 0
unsafe absolute runtime-native paths    = 0
```

The existing inventory, classification, fresh-process `dlopen`, and isolated import techniques should be retained.

### 5.2 Complete observed extension imports

All observed extension modules in the active `lib-dynload` directory imported successfully in isolated fresh processes.

This test should remain a mandatory post-transformation regression gate because ELF `RUNPATH`, stripping, archive re-rooting, pip installation, and sysconfig normalization can accidentally break native imports even when the original product was valid.

### 5.3 Whole-prefix relocation as a behavioral requirement

The existing project proved that the assembled prefix could be validated at location A, moved as a unit to location B, and validated again with runtime identity re-rooted to B.

The following observations should remain acceptance requirements:

- `sys.executable`;
- `sys.prefix`;
- `sys.base_prefix`;
- `sys.path`;
- active `sysconfig.get_paths()`;
- native extension imports;
- HTTPS;
- subprocess child identity;
- fresh venv identity;
- pip and uv workflows.

What must change is the mechanism used to maintain native-library resolution, not the behavioral claim itself.

### 5.4 Basic subprocess feasibility

The project already proved:

- Python child execution through `sys.executable`;
- correct child interpreter identity;
- native imports in child processes;
- subprocess operation from the base runtime;
- subprocess operation through venv and uv workflows.

The question “Can the official Android runtime execute subprocesses in a standalone environment?” is substantially answered.

The remaining work is to define the exact supported subprocess surface and prove that it remains correct after loader and relocation redesign.

### 5.5 Fresh venv and uv workflows

The existing evidence for fresh venv creation, correct prefix identity, offline pip installation, explicit uv interpreter selection, `uv run`, and fresh environments after moving the base runtime should remain regression inputs.

### 5.6 Deterministic archive safety mechanics

The project already has useful mechanisms for:

- deterministic member ordering;
- normalized timestamps and ownership;
- safe relative symlinks;
- rejection of traversal, special files, and unsafe links;
- exact member manifests;
- SHA-256 coverage;
- provenance and mutation accounting;
- qualification linkage.

These mechanics should be reused even though the archive hierarchy and metadata model must be changed to follow Astral more closely.

---

## 6. Evidence to Preserve, Implementation to Replace

## 6.1 Native loader activation

### Current implementation

The current launcher derives the runtime library directory and ensures that it appears in `LD_LIBRARY_PATH`. If it is absent at process start, the launcher updates the environment and re-executes itself so that Bionic initializes a new process with the required search path.

```text
resolve actual executable
    ↓
derive prefix/lib
    ↓
prefix/lib absent from LD_LIBRARY_PATH?
    ├── yes: update environment and exec self
    └── no: initialize Python
```

This solved the launcher's direct dependency on `libpython`, extension dependencies on project-shipped OpenSSL and SQLite, transitive runtime-internal dependencies, and child-process re-entry.

### Why it should not be final

The mechanism differs from the intended Astral-style design. It makes correctness depend on a process-global environment variable, a bootstrap re-execution, inherited child-process state, and custom launcher behavior unrelated to normal CPython invocation.

### Target implementation

The intended design is object-relative ELF lookup:

```text
python executable
    DT_RUNPATH = $ORIGIN/../lib

shared extension under lib/pythonX.Y/lib-dynload/
    DT_RUNPATH = relative path to the internal library directory

project-shipped shared dependency
    DT_RUNPATH = only when it has further runtime-internal dependencies
```

The exact relative paths must be derived from the final Astral-compatible install layout.

The final clean profile should satisfy:

```text
LD_LIBRARY_PATH unset
no project mutation of LD_LIBRARY_PATH
no loader-bootstrap self re-exec
all required native extensions import
all internal dependencies resolve relative to their consumers
subprocess children require no inherited project loader variable
whole-prefix relocation passes
```

### Required experiment matrix

| Variant | Description | Purpose |
|---|---|---|
| `LR-0` | Current conditional re-exec | Behavioral control |
| `LR-1` | Launcher-only relative `RUNPATH` | Confirm direct `libpython` lookup |
| `LR-2` | Launcher plus direct extension `RUNPATH` | Resolve immediate extension dependencies |
| `LR-3` | Complete per-object relative closure | Eliminate global loader configuration |
| `LR-4` | Final clean profile with self re-exec removed | Candidate upstream-thin design |

Each variant must record:

- pre/post file digests;
- ELF type, SONAME, `DT_NEEDED`, `RPATH`, and `RUNPATH`;
- exact mutation reason;
- unresolved edges;
- extension import results;
- HTTPS;
- subprocess;
- venv;
- pip;
- uv;
- relocation;
- symlink invocation.

### `DT_RUNPATH` versus `DT_RPATH`

The project should not assume that Linux/glibc behavior and Bionic behavior are identical.

A bounded Android comparison should determine:

- direct dependency resolution;
- transitive dependency behavior;
- `$ORIGIN` expansion;
- minimum-API behavior;
- modern linker-namespace behavior;
- interaction with `dlopen`;
- interaction with extension modules loaded after startup.

The preferred result is `DT_RUNPATH`. A fallback to `DT_RPATH` should require explicit evidence that Bionic transitive lookup semantics make it necessary.

### Stop condition

```text
project-required LD_LIBRARY_PATH = absent
loader-bootstrap re-exec         = absent
unresolved internal edges        = 0
extension import failures        = 0
```

---

## 6.2 Launcher design

### Current implementation

The existing launcher initializes CPython through `PyConfig`, sets the argument vector, and enters `Py_RunMain`. It intentionally avoids assigning `config.home`, because a negative-control experiment proved that explicit home injection introduced a fragile runtime requirement.

This is sound evidence.

### Remaining uncertainty

The final launcher should not be more custom than necessary. Astral's product is intended to behave like a normal standalone CPython executable. The project should determine whether a launcher closer to CPython's normal `Programs/python.c` entry path is sufficient after ELF loader correction.

### Required variants

| Variant | Description |
|---|---|
| `LA-0` | Existing PyConfig launcher |
| `LA-1` | Minimal `Py_BytesMain` frontend |
| `LA-2` | CPython `Programs/python.c`-equivalent frontend with relative `RUNPATH` |
| `LA-3` | `LA-2` plus only proven Android-mandatory initialization |

### Required behavioral matrix

- script execution;
- `-c`;
- `-m`;
- stdin execution;
- interactive REPL;
- `sys.argv`;
- `sys.executable`;
- `sys.prefix`;
- `sys.base_prefix`;
- environment-related command-line flags;
- isolated mode;
- UTF-8 and filesystem encoding;
- exit codes;
- signals;
- native extension imports;
- subprocess;
- venv;
- pip;
- uv;
- symlink invocation;
- whole-prefix relocation.

Retain the custom PyConfig launcher only if it demonstrably solves an Android requirement that the CPython-like frontend cannot solve.

---

## 6.3 Executable discovery and stock `getpath`

### Current implementation

The current launcher uses `/proc/self/exe` to find the actual executable and derive the runtime prefix. This works through external symlink invocation and avoids relying on current working directory, `argv[0]`, a build-time prefix, or shell-visible symlink text.

### Why this remains unresolved

Astral normally addresses difficult relocation and symlink cases through CPython `getpath` patches. Upstream-thin cannot modify frozen CPython source logic.

The project must establish exactly which cases the official upstream Android binary handles correctly on its own.

### Required matrix

| Case | Expected observation |
|---|---|
| Direct invocation through real executable path | Baseline correctness |
| Relative symlink inside install tree | Correct installation discovery |
| Absolute symlink inside install tree | Correct installation discovery |
| External symlink outside install tree | Determine stock behavior |
| Altered `argv[0]` | Determine whether discovery trusts the process path |
| Copied executable without surrounding prefix | Predictable failure |
| Venv symlink executable | Correct base interpreter |
| Venv copied executable | Correct or explicitly unsupported behavior |
| Whole runtime moved before fresh venv creation | Must pass |
| Pre-existing venv after base runtime move | Must be classified |
| Base runtime replaced by a patch update | Must be classified |

### Decision rule

1. If stock upstream `getpath` passes the required matrix, remove project executable discovery from runtime path logic.
2. If only bounded cases fail, define the smallest launcher correction.
3. If complete Astral behavior requires source patching, document the limitation in upstream-thin and move exact parity to source-thin.
4. Do not hide a structural limitation behind a broad `/proc/self/exe` wrapper unless that wrapper is the explicitly accepted Android divergence.

---

## 6.4 CA trust

### Existing evidence

The project has proved that `_ssl` and OpenSSL operate correctly, HTTPS succeeds when an appropriate PEM bundle is provided, an explicit regular-file `SSL_CERT_FILE` can be preserved, and certificate path discovery is separate from semantic validation.

### Current implementation to remove

The current fallback includes Termux-specific locations. This is useful qualification evidence but must not become canonical product behavior.

The final payload and metadata must not require or encode:

```text
/data/data/com.termux
/data/user/0/com.termux
com.termux
$PREFIX as a product-specific variable
```

### Candidate policies

| Candidate | Portability | Maintenance | Notes |
|---|---:|---:|---|
| Caller-supplied `SSL_CERT_FILE` only | High | Low | Weak default HTTPS experience |
| Bundled CA bundle | High | Project-owned | Requires update policy |
| Bundled default with caller override | High | Moderate | Most predictable standalone behavior |
| Generic Android trust-store extraction | Medium | High | Android-specific implementation |
| Native Android trust bridge | Medium | High | Strong platform integration, larger divergence |

### Required experiments

- HTTPS with no environment variables;
- caller-provided valid CA bundle;
- caller-provided invalid path;
- caller-provided empty or invalid regular file;
- bundled CA after relocation;
- CA update replacement without changing Python;
- subprocess and venv inheritance;
- no Termux strings in final payload or metadata.

A pinned bundled CA bundle with normal caller override semantics is the most portable likely direction, but this remains a design decision until provenance, update burden, and archive size are measured.

---

## 7. Partially Solved Areas Requiring Final Design

## 7.1 Sysconfig and development metadata normalization

### Existing result

The current project distinguished:

```text
active runtime paths
    relocation-aware

build and development metadata
    partially stale
```

Absolute path residue was inventoried and classified. Observed classes included upstream install-prefix residue, producer workspace paths, NDK/toolchain paths, host build-tool paths, destination scheme paths, and timezone search metadata.

No unknown runtime dependency remained, but the metadata was not normalized.

### Upstream-thin requirement

Astral treats sysconfig as a consumer surface, not merely a record of the producer host.

The distribution should normalize or replace values that:

- point to nonexistent producer paths;
- expose host-specific NDK locations;
- encode stale install prefixes;
- cause `python-config` to emit unusable flags;
- break source builds after relocation;
- misidentify extension output paths.

### Files and surfaces to audit

- `_sysconfigdata_*.py`;
- `sysconfig.get_paths()`;
- `sysconfig.get_config_vars()`;
- installed `Makefile`;
- `pyconfig.h`;
- `pythonX.Y-config`;
- pkg-config files, if present;
- `DESTSHARED`;
- `LIBDIR`;
- include-directory variables;
- compiler and linker command variables;
- sysroot and target flags;
- SOABI;
- multiarch;
- extension suffix;
- Android wheel platform tag.

### Required phases

#### `SC-0` — Frozen baseline census

Retain the existing exact path classification.

#### `SC-1` — Runtime normalization

Ensure runtime-facing paths are relative to, or derived from, the active installation.

#### `SC-2` — Consumer metadata normalization

Ensure SDK-facing metadata does not refer to the producer host.

#### `SC-3` — Minimal extension build

Build an extension containing at least:

```c
#include <Python.h>
```

Then compile for Android, link, produce an Android wheel, install into a venv, import, relocate the base distribution, and import again.

#### `SC-4` — Build-mode separation

Determine whether the product needs distinct representations for:

- on-device native extension builds;
- workstation-to-Android cross builds;
- runtime-only metadata.

### Stop condition

```text
unknown producer absolute paths       = 0
stale active install prefixes         = 0
runtime paths re-root after movement  = true
minimal native extension build        = pass
wheel platform identity               = correct
relocated extension import            = pass
```

---

## 7.2 Astral-compatible archive and metadata design

### Existing mechanics to preserve

The existing archive work already provides strong mechanics for deterministic serialization, safety validation, exact manifests, checksums, provenance, and qualification.

### Required hierarchy

The canonical full archive should follow Astral's structure:

```text
python/
├── PYTHON.json
├── build/
└── install/
```

A corresponding install-only artifact should derive from `python/install/` according to Astral's consumer convention.

### Upstream-thin `build/` semantics

Because the official package does not contain a full CPython object graph, the upstream-thin full archive must not pretend to provide Astral's source-relink capability.

A truthful layout could be:

```text
python/
├── PYTHON.json
├── build/
│   ├── upstream/
│   │   ├── official-package/
│   │   └── upstream-metadata/
│   ├── overlay/
│   │   ├── launcher/
│   │   ├── elf-transformations/
│   │   ├── sysconfig-normalization/
│   │   └── pure-python-payloads/
│   ├── manifests/
│   ├── licenses/
│   └── qualification/
└── install/
    └── ...
```

This preserves Astral's top-level design while accurately describing a binary-derived producer.

### `PYTHON.json`

The file should expose, where truthfully known:

- schema version;
- Android target triple;
- Python version and implementation tags;
- Python ABI tag;
- Android platform tag;
- implementation cache tag;
- executable path;
- stdlib and include paths;
- normalized sysconfig paths;
- extension suffixes;
- shared `libpython` link mode;
- supported extension loading mechanisms;
- build options inherited from upstream;
- licenses;
- test runner path, if shipped;
- runtime and development layout;
- Android minimum API;
- Bionic identity;
- upstream package identity;
- local mutation summary.

Fields that require unavailable object-level build material must be absent or explicitly represented as unavailable. The schema must never invent core object lists, static `libpython`, extension object lists, relinkable inittab inputs, or dependency static archives.

Astral-compatible `PYTHON.json` should be the primary in-archive distribution description. Project-specific sidecars may still exist for exact member manifests, upstream provenance, local mutations, qualification, attestations, and release indexes.

---

## 7.3 Timezone data

### Existing evidence

The base runtime did not have a usable timezone source in the tested environment. CPython's first-party `tzdata` package fallback worked without mutating the base runtime.

### Remaining policy choices

| Policy | Portability | Update ownership | Runtime behavior |
|---|---:|---:|---|
| Bundle pinned `tzdata` package | High | Project | Works without host data |
| Declare `tzdata` as a required companion | Medium | Consumer | Requires installation |
| Bundle raw zoneinfo tree | High | Project | Separate data layout |
| Discover host zoneinfo | Low | Host | Not sufficiently portable |

### Recommended experiment

Compare no bundled timezone data, pinned `tzdata` installed into `python/install`, and a separately bundled zoneinfo tree.

Measure archive size, lookup behavior, `zoneinfo.available_timezones()`, relocation, update procedure, licensing, provenance, and interaction with venv.

---

## 8. Additional Upstream-Byte Capability Experiments

## 8.1 Subprocess support matrix

The basic capability is already established. The remaining experiment defines the supported surface.

### Core matrix

- `subprocess.run`;
- `Popen`;
- stdin/stdout/stderr pipes;
- `capture_output`;
- binary and text modes;
- encoding and error handling;
- `cwd`;
- custom `env`;
- executable lookup;
- absolute executable path;
- return codes;
- `poll`;
- `wait`;
- `communicate`;
- timeout;
- termination;
- kill;
- large-output handling;
- nested Python child;
- child native extension imports;
- child execution from relocated base;
- child execution from venv;
- `asyncio.create_subprocess_exec`;
- `asyncio.create_subprocess_shell`.

### Secondary matrix

- `shell=True`;
- explicit shell executable;
- `start_new_session`;
- process groups;
- signal forwarding;
- `pass_fds`;
- `close_fds`;
- `preexec_fn`;
- PTY child;
- background-child lifecycle;
- zombie cleanup.

### Completion criteria

```text
project loader environment required by children = no
child executable identity                    = correct
timeout and termination leaks               = none observed
core subprocess matrix                      = pass
host-dependent cases                        = explicitly classified
```

---

## 8.2 Virtual-environment completeness

| Case | Purpose |
|---|---|
| Standard symlink venv | Normal POSIX behavior |
| Copy-based venv | Filesystem and packaging compatibility |
| Venv moved without moving base | Determine supported boundary |
| Base moved before creating fresh venv | Must pass |
| Venv created before base is moved | Existing untested boundary |
| Base replaced by patch update | Update portability |
| Console-script shebangs | Absolute-path leakage |
| Native extension installed in venv | Loader and SDK |
| uv-created venv | Consumer parity |
| pip-created scripts after relocation | Packaging behavior |

The experiment must produce a precise support statement rather than a general “venv works” claim.

---

## 8.3 Astral-style base pip

### Goal

Astral disables `ensurepip` and installs a pinned pip wheel into the standalone distribution. Upstream-thin should evaluate the same approach.

### Candidate installation methods

| Variant | Method |
|---|---|
| `PIP-0` | Run the target Android interpreter and install the wheel |
| `PIP-1` | Deterministically extract wheel contents into the target scheme |
| `PIP-2` | Use a host-side installer library with explicit target scheme |
| `PIP-3` | Install only the pip package and omit generated command wrappers |

### Questions

- Can the installation be deterministic?
- Do generated scripts contain absolute build prefixes?
- Should `python -m pip` be the canonical entrypoint?
- Are `pip`, `pip3`, and `pip3.X` scripts required for Astral parity?
- Can scripts survive whole-prefix relocation?
- Can pip and uv coexist without modifying the base product?
- Which pip version and update cadence are project-owned?

### Required validation

- `python -m pip --version`;
- offline pure-Python wheel installation;
- online index installation where network access is allowed;
- console-script generation;
- relocation;
- venv;
- uv coexistence;
- no producer-host path residue.

---

## 8.4 `multiprocessing` capability matrix

This is the highest-risk upstream-byte feature experiment. A successful subprocess implementation does not imply complete multiprocessing support.

### Required probes

- `multiprocessing.Process`;
- available start methods;
- `fork`;
- `spawn`;
- `forkserver`;
- `Pipe`;
- `Connection`;
- `SimpleQueue`;
- `Queue`;
- `Pool`;
- `Lock`;
- `RLock`;
- `Semaphore`;
- `BoundedSemaphore`;
- `Event`;
- `Condition`;
- shared `Value`;
- shared `Array`;
- `Manager`;
- `ProcessPoolExecutor`;
- resource tracker;
- `multiprocessing.shared_memory`;
- termination and cleanup.

### Classification

| Result | Meaning |
|---|---|
| **Pass without adaptation** | Eligible for upstream-thin support |
| **Pass with Android-mandatory adaptation** | Candidate bounded divergence |
| **Fail because of missing Bionic primitive** | Explicitly unsupported in upstream-thin |
| **Fail because of a CPython build decision** | Defer to source-thin investigation |
| **Fail because of test environment** | Re-run with adequate evidence |

The final distribution must not claim blanket multiprocessing support unless the complete matrix justifies it.

---

## 9. New Portability Experiments

## 9.1 Direct adaptation of the official package

The current project includes reconstructed producer evidence. The upstream-thin product must instead prove the direct binary-consumption path.

```text
download exact Python.org package
    ↓
verify version, identity, and checksum
    ↓
extract without mutation
    ↓
inventory exact upstream product
    ↓
apply enumerated standalone transformations
    ↓
assemble Astral-compatible archive
    ↓
qualify
```

Compare against the reconstructed producer using file inventory, ELF inventory, extension surface, native closure, dependency identities, sysconfig, wheel tags, package layout, archive size, startup, subprocess, venv, pip, uv, relocation, and local mutation count.

The main path should remain binary-derived if the direct official artifact satisfies the required standalone contract with a bounded and explainable local delta.

---

## 9.2 Minimum API-floor qualification

Running an API-24 binary on an API-36 device does not prove API-24 runtime compatibility.

The minimum-floor experiment should validate extraction, startup, all native imports, HTTPS, subprocess, venv, pip, wheel identity, relocation, ELF closure, and filesystem assumptions.

The environment must be a real API-24 device or a sufficiently credible emulator or system image whose limitations are recorded.

---

## 9.3 16 KiB page-size compatibility

The complete assembled product must be checked, not only the upstream package.

### Static checks

For every ELF object:

- `PT_LOAD` alignment;
- segment offsets;
- page-alignment warnings;
- relocation sections;
- stripping effects;
- post-`RUNPATH`-mutation layout.

### Runtime checks

- launcher execution;
- `libpython`;
- all native extension imports;
- internal shared libraries;
- subprocess;
- venv;
- pip;
- uv;
- whole-prefix relocation.

### Disposition rule

- If the official bytes pass, record compatibility as inherited and verified.
- If a local binary transformation breaks compatibility, repair the transformation.
- If an upstream ELF is incompatible, classify the issue as requiring a new upstream package or source-thin build.

---

## 9.4 Upstream patch-update rehearsal

One official patch update should be performed with the goal that most changes are configuration-only:

- version;
- upstream URL;
- checksum;
- upstream metadata;
- expected package identity.

Record every required code or transformation change, especially changed layout, extension inventory, shared-library names, `RUNPATH` targets, sysconfig keys, Android wheel tags, pip compatibility, `PYTHON.json` generation, and qualification expectations.

---

## 9.5 Python 3.15 preview

The preview should answer:

- Does the official Android package preserve the same prefix layout?
- Does the launcher remain compatible?
- Does `getpath` behavior change?
- Does sysconfig require different normalization?
- Does the extension surface change?
- Does subprocess timed-wait behavior change through pidfd support?
- Do wheel and ABI tags change?
- Does the pip installation strategy remain valid?
- Are any local transformations version-specific?

This is a delta report, not a release claim.

---

## 10. Product Identity and Host Neutrality

The canonical identity should include only product properties:

```text
CPython implementation and version
target triple
Android ABI
minimum Android API
Bionic libc
Python tag
ABI tag
SOABI
Android wheel platform tag
build options
archive flavor
upstream artifact identity
local transformation identity
```

The following must not be part of canonical identity:

```text
Termux
adb
root shell
APK host
shell path
host CA path
host HOME
host TMPDIR
host package name
```

Host environments may appear in qualification evidence, but not as required product properties.

### Required negative scans

The final payload and canonical metadata should be scanned for:

```text
/data/data/com.termux
/data/user/0/com.termux
com.termux
Termux-provided SONAMEs
historical build prefixes
producer workspaces
host NDK paths
stale /usr/local paths
```

Every retained absolute path must have a documented reason.

---

## 11. Proposed Experiment Sequence

## UT-0 — Exact Official Control

**Question:** What exactly is present in the official Python.org package before local adaptation?

**Outputs:** exact archive, checksum, package inventory, ELF inventory, extension inventory, sysconfig census, and no-mutation fingerprint.

## UT-1 — Astral Archive Prototype

**Question:** Can the official product be represented truthfully within Astral's archive and metadata structure?

**Work:** `python/PYTHON.json`, `python/build`, `python/install`, install-only derivation, stripped derivation, deterministic serialization, and truthful absence of unavailable object-level data.

## UT-2 — Loader and Relocation Replacement

**Question:** Can the official binaries operate with object-relative ELF metadata and without project-required global loader environment?

**Acceptance:** no required `LD_LIBRARY_PATH`, no loader-bootstrap re-exec, complete native closure, and successful whole-prefix relocation.

## UT-3 — Sysconfig and SDK Normalization

**Question:** Can the binary-derived distribution expose portable development metadata?

**Work:** normalize runtime paths, eliminate producer-host residue, define on-device versus cross-build metadata, build a minimal native extension, produce and install an Android wheel, and relocate and re-import.

## UT-4 — Android-Mandatory Data Adaptation

**Question:** Which data sources must be bundled because Android does not provide normal Unix standalone assumptions?

**Work:** CA bundle policy, timezone policy, writable-directory assumptions, elimination of Termux-specific defaults, and provenance/update policy for bundled data.

## UT-5 — Feature Qualification

**Question:** What complete feature surface can upstream-thin support?

**Work:** subprocess matrix, venv matrix, base pip, uv consumption, multiprocessing capability matrix, and console-script behavior.

## UT-6 — Platform Portability

**Question:** Does the assembled distribution satisfy the inherited Android support claim across critical platform boundaries?

**Work:** minimum API, modern Android runtime, 16 KiB page size, clean extraction, full relocation, native closure, and no host-specific product dependency.

## UT-7 — Update Portability

**Question:** Does the adaptation survive normal upstream evolution?

**Work:** one CPython 3.14 patch update, Python 3.15 preview, configuration-only versus code-change census, changed package/module surface, and changed transformation burden.

---

## 12. Final Disposition Summary

### Preserve directly

```text
pure Bionic native-closure verification
isolated extension import verification
whole-prefix relocation behavioral tests
subprocess child-identity tests
fresh venv and uv functional tests
deterministic archive serialization mechanics
safe extraction and exact manifest verification
provenance and mutation accounting
```

### Preserve evidence, replace implementation

```text
LD_LIBRARY_PATH-based native dependency resolution
conditional loader-bootstrap self re-exec
/proc/self/exe as the primary relocation mechanism
Termux-specific certificate fallback
current custom launcher unless proven necessary
current non-Astral archive hierarchy
Termux-oriented canonical profile metadata
```

### Design and experiment before release

```text
complete per-object relative RUNPATH closure
stock getpath capability boundary
minimal final launcher
Astral-compatible PYTHON.json
truthful upstream-thin full archive
install-only and stripped derivation
portable sysconfig normalization
native extension SDK
pinned base pip installation
portable CA bundle policy
timezone packaging policy
full subprocess matrix
complete venv matrix
multiprocessing capability matrix
minimum API qualification
16 KiB page-size qualification
patch-update portability
Python 3.15 compatibility
```

### Defer beyond upstream-thin

```text
CPython getpath source patching
static-linked interpreter
Astral default-static extension topology
dependency static relinking
complete object-level reconstruction archive
PGO/LTO/BOLT
tail-call interpreter policy
free-threaded and JIT profiles
API-36 compile-time CPython behavior
expanded native module surface such as curses, readline, Tk, or Berkeley DB
```

---

## 13. Completion Criteria

The upstream-thin research phase is complete when it can answer, with evidence:

1. Can the exact official Python.org package be transformed directly into the product?
2. Is every local byte-level mutation enumerated and justified?
3. Can all internal ELF dependencies resolve without project-required `LD_LIBRARY_PATH`?
4. Can the loader-bootstrap self re-exec be removed?
5. Which relocation and symlink cases work with stock upstream `getpath`?
6. Which bounded executable-path correction, if any, remains unavoidable?
7. Is the archive structurally compatible with Astral?
8. Is `PYTHON.json` truthful and sufficient for consumers?
9. Are unavailable object-level build facts represented as unavailable rather than fabricated?
10. Is sysconfig usable after relocation?
11. Can a real Android native extension wheel be built, installed, imported, and relocated?
12. Does pinned base pip behave like Astral's standalone pip installation?
13. Which subprocess APIs are officially project-supported?
14. Which venv relocation and update cases are supported?
15. Which multiprocessing capabilities work, and which are structurally unavailable?
16. Does the product work at the minimum claimed Android API?
17. Does it work under a 16 KiB page-size environment?
18. Is the product free of Termux native dependencies and hard-coded Termux identity?
19. Does a patch update require only bounded configuration changes?
20. Is the Python 3.15 delta understood before the clean release repository is created?

---

## 14. Final Direction

The three highest-priority upstream-thin experiments are:

```text
1. direct adaptation of the exact official Python.org Android package
2. replacement of LD_LIBRARY_PATH/self-reexec with complete relative ELF lookup
3. Astral-style sysconfig normalization proven by a real native-extension wheel
```

These experiments address the most important distinction between the current research runtime and the intended final distribution:

> The current project has largely proved that the upstream Android bytes can support a standalone Python product. The remaining work must prove that the product can be assembled using an Astral-like standalone design rather than host-specific bootstrap workarounds.

The desired upstream-thin outcome is:

```text
Python.org/BeeWare runtime production decisions
    +
Astral archive, metadata, relocation, and consumer architecture
    +
only structurally necessary Android adaptation
    =
portable Android/Bionic standalone CPython
```

No broader source-producer responsibility should be introduced unless one of the experiments proves that the required Astral-style behavior cannot be obtained from the official binary product.
