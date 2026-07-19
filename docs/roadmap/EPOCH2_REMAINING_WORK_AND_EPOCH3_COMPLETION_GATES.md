# Epoch 2 Remaining Work and Epoch 3 Completion Gates

> **Status:** canonical detailed planning authority
> **Date:** 2026-07-19
> **Decision authorities:** ADR-0006 and ADR-0007
> **Raw research input:** `docs/references/raw/2026-07-19-upstream-thin-plan/UPSTREAM_THIN_RESEARCH_AND_DESIGN_PLAN.md`
> **Scope:** upstream-derived, Astral-structured Android/Bionic standalone CPython
> **Primary distribution reference:** Astral `python-build-standalone`
> **Primary runtime input:** verified Python.org Android package and the BeeWare dependency products selected by CPython

## 1. Governing model

```text
Epoch 2
  official upstream control
  + controlled experiments
  + Android adaptation evidence
  + explicit evidence dispositions
        ↓
Epoch 3 selection register
  adopt / adopt-with-redesign / exclude / defer-to-epoch4
        ↓
Epoch 3 clean release repository
  selected upstream-derived Astral-structured product
        ↓
Epoch 4
  full Astral-like source producer reproducing the selected product contract
```

Epoch 2 determines what is possible, what is structurally required, what is unsafe, and what remains source-dependent. Epoch 3 decides what the clean product should contain.

A successful Epoch 2 experiment is not an automatic Epoch 3 feature. External pip is the simplest example: successful installation and operation proves feasibility, while Epoch 3 may still omit base pip to reduce maintenance, mutation, security, or relocation burden.

## 2. Status and decision vocabularies

### 2.1 Epoch 2 evidence disposition

| Disposition | Meaning |
|---|---|
| `pass` | The experiment satisfies its complete stated acceptance boundary. |
| `bounded-pass` | A useful subset passes and the unsupported boundary is explicit. |
| `fail` | The candidate mechanism does not satisfy the required boundary. |
| `unavailable` | Credible execution was not possible; the missing authority and consequence are explicit. |

### 2.2 Existing implementation disposition

| Disposition | Meaning |
|---|---|
| `preserve` | Keep the existing evidence and mechanism. |
| `preserve-evidence-reimplement` | Keep feasibility evidence but replace the mechanism. |
| `design-required` | The mechanism boundary is known but product policy is not selected. |
| `experiment-required` | More evidence is required. |
| `defer-to-epoch4` | The behavior requires project-owned source production or a separate architecture decision. |

### 2.3 Epoch 3 selection disposition

| Disposition | Meaning |
|---|---|
| `adopt` | Use the proven mechanism or payload substantially as tested. |
| `adopt-with-redesign` | Keep the capability but replace or narrow its implementation. |
| `exclude` | Deliberately omit it from the Epoch 3 product. |
| `defer-to-epoch4` | Do not include it until source production or deeper architecture work exists. |

Every selectable item must record rationale, ownership, update/security burden, artifact impact, consumer impact, and qualification impact.

## 3. Preserved evidence baseline

The following historical evidence remains regression input:

- pure Bionic plus Android-public native closure on the accepted target;
- zero observed Termux native-library providers;
- isolated import of the complete observed native-extension surface;
- whole-prefix relocation behavior;
- Python subprocess child re-entry and identity;
- fresh venv creation;
- offline pip installation;
- explicit-interpreter uv workflows;
- Android wheel identity;
- deterministic archive safety, manifests, checksums, provenance, and mutation accounting.

The following implementations are not presumed final:

- `LD_LIBRARY_PATH` mutation;
- conditional loader-bootstrap self re-execution;
- `/proc/self/exe` as the primary relocation mechanism;
- Termux-specific certificate discovery;
- the current custom launcher unless proven necessary;
- non-Astral archive hierarchy;
- Termux-oriented canonical profile metadata.

## 4. Mandatory Epoch 3 product invariants

Epoch 2 must produce sufficient evidence for Epoch 3 to enforce all of the following:

```text
direct verified Python.org/BeeWare derivation
enumerated local byte mutations
pure Bionic + Android-public native closure
Termux native provider edges = 0
hard-coded Termux product identity = absent
fresh extraction executes
accepted whole-prefix relocation works
project-required LD_LIBRARY_PATH = absent
loader-bootstrap self re-exec = absent
truthful Astral top-level archive structure
truthful PYTHON.json without fabricated build facts
exact provenance, licenses, checksums, and qualification
consumer-visible target and ABI identity
```

These are not optional feature selections.

## 5. Selectable Epoch 3 capabilities and policies

The following require explicit Epoch 3 selection even when Epoch 2 proves feasibility:

- bundled base pip;
- `pip`, `pip3`, and `pip3.X` wrappers;
- bundled CA bundle versus caller-supplied trust;
- bundled `tzdata` versus companion dependency or raw zoneinfo tree;
- supported subprocess secondary features;
- supported venv move/update cases;
- multiprocessing primitives and start methods;
- runtime-only versus on-device SDK versus cross-build SDK metadata;
- uv catalog and installation integration details;
- optional symbols, debug, test, or SDK artifacts;
- host integration helpers;
- any API-36-derived product input.

## 6. Remaining Epoch 2 work program

## UT-0 — Exact official upstream control

**Question:** What exactly exists in the unmodified official Python.org Android package and its inherited BeeWare dependency set?

**Required work:**

1. acquire the exact official package by versioned URL;
2. verify checksum, target, version, minimum API, and package identity;
3. extract without mutation;
4. inventory every member, ELF object, shared dependency, native extension, sysconfig surface, license, and upstream metadata source;
5. freeze a no-mutation fingerprint;
6. compare with the reconstructed producer authority without treating reconstruction as the product input.

**Required outputs:**

- upstream input manifest;
- package and file hashes;
- ELF and extension inventories;
- dependency-provider map;
- sysconfig census;
- package-layout map;
- source, patch, recipe, license, and binary provenance links;
- bounded delta against the reconstructed producer.

**Exit condition:** the official package can be used as the sole CPython runtime input with no unidentified provenance or topology.

**Epoch 3 decisions enabled:** exact acquisition policy, pinned-input representation, direct-adaptation go/no-go.

## UT-1 — Astral artifact and metadata prototype

**Question:** Can a binary-derived upstream product be represented truthfully within Astral's standalone archive and consumer architecture?

**Canonical full root:**

```text
python/
├── PYTHON.json
├── build/
└── install/
```

The upstream-thin `build/` area must retain upstream packages, metadata, project overlays, mutations, licenses, manifests, and qualification evidence. It must not fabricate object files, static `libpython`, extension object lists, static dependency archives, or relinkable inittab material that the official package does not provide.

**Required variants:**

- full upstream-derived audit artifact;
- `install_only`;
- `install_only_stripped`;
- optional symbols/debug/SDK artifact proposals, without automatic adoption.

**Required outputs:**

- `PYTHON.json` schema mapping;
- explicit unavailable-field policy;
- deterministic derivation rules;
- archive root and path contract;
- exact member manifests and checksums;
- artifact-flavor decision inputs;
- consumer extraction contract.

**Exit condition:** a consumer can understand target, runtime, ABI, paths, features, provenance, and limitations without knowledge of the laboratory repository.

**Epoch 3 decisions enabled:** final artifact family, optional artifact inclusion, metadata schema, release index design.

## UT-2 — Loader, relocation, launcher, and getpath

**Question:** Can the official binaries satisfy the standalone relocation contract without process-global loader workarounds?

### Loader variants

```text
LR-0  current LD_LIBRARY_PATH + conditional self-reexec control
LR-1  launcher-only relative RUNPATH
LR-2  launcher plus direct extension RUNPATH
LR-3  complete per-object relative native closure
LR-4  clean candidate with no project LD_LIBRARY_PATH and no self-reexec
```

### Launcher variants

```text
LA-0  current PyConfig launcher
LA-1  minimal Py_BytesMain frontend
LA-2  CPython Programs/python.c-equivalent frontend
LA-3  LA-2 plus only evidenced Android-mandatory initialization
```

### Executable discovery matrix

- direct real path;
- relative and absolute in-tree symlinks;
- external symlink;
- altered `argv[0]`;
- copied executable without prefix;
- venv symlink and copy modes;
- runtime moved before fresh venv creation;
- pre-existing venv after base move;
- patch-level base replacement.

### Native loader evidence

For every transformed ELF record:

- pre/post SHA-256;
- ELF type and machine;
- SONAME;
- `DT_NEEDED`;
- `DT_RPATH`;
- `DT_RUNPATH`;
- exact mutation;
- reason and consumer;
- 16 KiB alignment preservation.

A bounded Android comparison must establish Bionic behavior for `$ORIGIN`, direct and transitive lookup, `dlopen`, minimum API, and modern linker namespaces. `DT_RUNPATH` is preferred; `DT_RPATH` requires explicit evidence.

**Exit condition:**

```text
project-required LD_LIBRARY_PATH = absent
loader-bootstrap self-reexec     = absent
unresolved internal edges        = 0
required extension failures      = 0
whole-prefix relocation          = pass
subprocess child re-entry        = pass
```

**Epoch 3 decisions enabled:** final launcher, accepted Android divergence from stock `getpath`, ELF mutation policy, supported symlink/venv relocation boundary.

## UT-3 — Sysconfig and native-extension SDK

**Question:** Can the binary-derived distribution expose portable runtime and development metadata?

**Audit surfaces:**

- `_sysconfigdata_*.py`;
- `sysconfig.get_paths()` and config variables;
- installed `Makefile`;
- `pyconfig.h`;
- `pythonX.Y-config`;
- pkg-config files;
- include, library, `DESTSHARED`, SOABI, multiarch, extension suffix, compiler, linker, sysroot, and Android wheel-tag variables.

**Phases:**

```text
SC-0  frozen absolute-path census
SC-1  runtime-facing path normalization
SC-2  consumer metadata normalization
SC-3  real Android C-extension wheel build/install/import/relocate
SC-4  runtime-only, on-device SDK, and cross-build SDK separation
```

The native-extension probe must at minimum include `Python.h`, compile for Android, produce an Android-tagged wheel, install into a venv, import, move the base distribution where supported, and import again.

**Exit condition:**

```text
unknown producer absolute paths       = 0
stale active install prefixes         = 0
runtime paths re-root after movement  = true
native extension wheel build          = pass
wheel identity                        = correct
relocated extension import            = pass
```

**Epoch 3 decisions enabled:** runtime-only versus SDK product surface, SDK artifact flavor, supported build modes, normalized metadata contract.

## UT-4 — Android-mandatory data and writable-state policy

**Question:** Which data or writable locations must the standalone product own because Android lacks normal Unix distribution assumptions?

### CA trust candidates

- caller-supplied `SSL_CERT_FILE` only;
- pinned bundled CA bundle;
- bundled default with caller override;
- generic Android trust extraction;
- native Android trust bridge.

### Timezone candidates

- pinned `tzdata` in the install tree;
- required companion dependency;
- bundled raw zoneinfo tree;
- host discovery, expected to be rejected unless proven portable.

### Additional boundaries

- temporary directory;
- cache and bytecode policy;
- user site;
- venv writable locations;
- read-only installation behavior;
- subprocess and venv inheritance;
- data update independent of Python update.

**Required negative scans:**

```text
/data/data/com.termux
/data/user/0/com.termux
com.termux
historical build prefixes
producer workspaces
host NDK paths
stale /usr/local paths
```

**Exit condition:** every required runtime data source and writable location has a host-neutral policy, provenance, update owner, relocation behavior, and failure mode.

**Epoch 3 decisions enabled:** CA and timezone packaging, writable-state contract, data update cadence. A passing bundled-data experiment does not require bundling in Epoch 3.

## UT-5 — Feature capability and product-surface qualification

**Question:** What feature surface is technically feasible, and which subset should Epoch 3 support?

### Subprocess core matrix

- `run`, `Popen`, pipes, capture, binary/text modes;
- `cwd`, custom `env`, executable lookup and absolute execution;
- return codes, `poll`, `wait`, `communicate`, timeouts;
- terminate, kill, large output, nested Python;
- child native imports;
- relocated base and venv execution;
- `asyncio` subprocess exec and shell.

### Subprocess secondary matrix

- `shell=True` and explicit shell;
- sessions and process groups;
- signal forwarding;
- `pass_fds`, `close_fds`, `preexec_fn`;
- PTY;
- background lifecycle and zombie cleanup.

### Venv matrix

- symlink and copy modes;
- base moved before new venv;
- pre-existing venv after base move;
- venv moved without base;
- patch-level base replacement;
- console-script shebangs;
- native extension in venv;
- uv-created venv;
- pip-generated scripts after relocation.

### Base pip variants

```text
PIP-0  install through the target interpreter
PIP-1  deterministic wheel extraction
PIP-2  host-side target-scheme installer
PIP-3  pip package without command wrappers
PIP-X  omit base pip from the Epoch 3 product
```

Epoch 2 must compare deterministic installation, generated absolute paths, relocation, venv behavior, uv coexistence, version/update ownership, archive growth, and security burden.

### Multiprocessing matrix

- processes and available start methods;
- `fork`, `spawn`, `forkserver`;
- pipes, connections, queues, pools;
- locks, semaphores, events, conditions;
- shared values and arrays;
- manager, process pool executor, resource tracker;
- shared memory;
- termination and cleanup.

Each capability is classified as pass, Android-mandatory adaptation, missing Bionic primitive, upstream build decision, or inadequate environment.

**Exit condition:** feasibility and support boundaries are explicit for each matrix; no blanket subprocess, venv, pip, or multiprocessing claim exceeds the evidence.

**Epoch 3 decisions enabled:** selected feature surface. Passing external pip or multiprocessing probes do not require inclusion.

## UT-6 — Platform portability

**Question:** Does the assembled product satisfy the intended Android support boundary?

### Required environments or equivalent evidence

- minimum claimed API, preferably API 24;
- accepted modern Android target;
- 16 KiB page-size environment;
- clean extraction in a non-Termux canonical path where feasible;
- Termux, ADB, and root differential probes where access permits.

### Static 16 KiB checks

For every final ELF:

- `PT_LOAD` alignment;
- segment offsets;
- relocation sections;
- stripping effects;
- post-RUNPATH mutation layout.

### Runtime checks

- launcher and `libpython`;
- all required native imports;
- internal shared libraries;
- subprocess;
- venv;
- selected pip and uv paths;
- relocation;
- native-extension wheel where selected.

**Exit condition:** every public platform claim has target evidence or is explicitly withheld. Modern-device success is not used as minimum-API proof.

**Epoch 3 decisions enabled:** minimum release API, supported page-size claim, supported contexts, withheld claims.

## UT-7 — Upstream evolution and maintenance portability

**Question:** Can the adaptation survive normal upstream evolution with a bounded local burden?

### Patch-update rehearsal

Perform one official CPython 3.14 patch update. Record every change beyond:

- version;
- URL;
- checksum;
- upstream metadata;
- expected package identity.

Audit layout, extensions, shared-library names, RUNPATH targets, sysconfig keys, wheel tags, pip compatibility, `PYTHON.json`, and qualification.

### Python 3.15 preview

Produce a delta report covering:

- package and prefix layout;
- launcher and getpath;
- sysconfig;
- extension surface;
- wheel and ABI tags;
- pidfd-related subprocess behavior;
- pip strategy;
- version-specific transformations.

This is evidence, not a release claim.

**Exit condition:** update burden, version-specific assumptions, security ownership, and configuration-only boundaries are explicit.

**Epoch 3 decisions enabled:** supported version policy, update automation, maintenance staffing and release cadence.

## API-36 controlled source-equivalent comparison track

This track is mandatory Epoch 2 work even though the Epoch 3 product remains upstream-derived.

### Control classes

```text
A  exact official Python.org/BeeWare binary product

B  same upstream CPython and launcher source revisions and patches,
   API changed to 36,
   official BeeWare dependency binaries retained

C  same upstream CPython and BeeWare dependency source revisions,
   patches, recipes, module decisions, NDK/toolchain identity,
   linkage topology, and build options as practical,
   API changed to 36
```

### Controlled-variable rule

The Android compile API is the intended changed variable. Every unavoidable additional delta must be enumerated.

### Measurements

- required Android symbols and minimum runtime;
- ELF metadata and dependency closure;
- native TLS and low-level runtime behavior;
- subprocess, filesystem, and timing APIs;
- startup and selected benchmarks;
- size;
- extension imports;
- wheel tags and sysconfig;
- build and provenance burden;
- behavior on modern and minimum environments where meaningful.

### Product-decision rule

The API-36 variants answer whether a higher floor changes behavior or burden. They do not automatically become Epoch 3 inputs. Epoch 3 may retain the exact official API-floor product, adopt a bounded API-36-derived input through a separate product decision, or defer API-36 production to Epoch 4.

## 7. Epoch 2 closure gates

### E2-G1 — Exact upstream control

The official product and dependency provenance are exact, verified, and mutation-free at intake.

### E2-G2 — Direct-adaptation viability

A complete local mutation manifest exists and direct official bytes can satisfy the mandatory product invariants, or the blocking reason is explicit.

### E2-G3 — Clean loader and relocation decision

The final candidate eliminates project-required `LD_LIBRARY_PATH` and loader-bootstrap re-execution, or Epoch 3 is blocked pending an explicit architecture decision.

### E2-G4 — Truthful Astral artifact contract

Full, install-only, stripped, `PYTHON.json`, provenance, unavailable-field semantics, and deterministic derivation are defined.

### E2-G5 — Runtime and SDK evidence

Runtime sysconfig is portable; SDK feasibility and product modes are proven or explicitly excluded/deferred.

### E2-G6 — Capability and data decision inputs

CA, timezone, writable state, subprocess, venv, pip, uv, multiprocessing, and console-script results have bounded evidence dispositions.

### E2-G7 — Platform and evolution evidence

Minimum API, 16 KiB pages, API-36 comparison, patch update, Python 3.15 preview, and context differences are complete or explicitly unavailable with consequence accounting.

### E2-G8 — Producer-independent evidence export

The export includes:

- exact upstream inputs;
- exact local delta;
- mandatory invariants;
- selectable-item evidence;
- selection candidates and tradeoffs;
- supported and withheld platform claims;
- archive and metadata contract;
- qualification contract;
- unresolved risks;
- one accepted product seed;
- Epoch 4 deferred producer questions.

Epoch 2 closes when all gates are resolved. Resolution may include an explicit blocked or excluded decision; it may not hide missing evidence behind a broad success claim.

## 8. Epoch 3 initialization gates

### E3-I1 — Accepted evidence export

The clean repository starts from a content-addressed E2-G8 export and accepted product seed.

### E3-I2 — Complete selection register

Every selectable item has exactly one disposition:

```text
adopt
adopt-with-redesign
exclude
defer-to-epoch4
```

The register must explicitly cover at least pip, pip command wrappers, CA, timezone data, SDK modes, multiprocessing, venv relocation cases, uv integration, optional artifacts, and any API-36 input.

### E3-I3 — Clean repository boundary

The clean repository imports only product code, bounded provenance, selected tests, release automation, and accepted documentation. It does not import the complete laboratory history.

### E3-I4 — Contract freeze

Target identity, artifact family, archive root, runtime layout, metadata schema, mutation policy, qualification, supported contexts, feature surface, and release ownership are frozen before implementation expands.

## 9. Epoch 3 completion gates

### E3-G1 — Reproducible upstream acquisition

A clean clone acquires and verifies exact Python.org/BeeWare inputs from pinned metadata without relying on the research repository.

### E3-G2 — Deterministic bounded transformation

Every changed byte is produced by versioned code, enumerated, justified, reproducible, and covered by manifests and checksums.

### E3-G3 — Standalone runtime architecture

The selected launcher, getpath boundary, and per-object native lookup satisfy the mandatory invariants without project-required global loader state or bootstrap re-execution.

### E3-G4 — Astral-structured artifact family

Selected full, install-only, stripped, optional artifacts, `PYTHON.json`, release index, licenses, provenance, checksums, and attestations are generated truthfully.

### E3-G5 — Selected runtime and SDK surface

Only selected capabilities are shipped and documented. Excluded or deferred items are absent from product claims and qualification. A passed Epoch 2 experiment is not sufficient evidence of inclusion.

### E3-G6 — Platform qualification

Fresh extraction, relocation, native closure, selected extensions, selected subprocess/venv/pip/uv/SDK behavior, minimum API, page size, and supported Android contexts pass the release contract.

### E3-G7 — Host neutrality

The payload and canonical metadata contain no required Termux native dependency, hard-coded Termux identity, producer workspace, host NDK path, or stale install prefix.

### E3-G8 — Update and security operations

One patch update is reproduced through the clean pipeline; upstream and project-owned security responsibilities, data updates, revocation, rollback, and support policy are documented.

### E3-G9 — Consumer readiness

The release catalog, target matching, extraction, lifecycle, checksums, documentation, and uv-facing consumer contract work without knowledge of the laboratory repository.

### E3-G10 — Epoch 4 substitution boundary

The product contract exported to Epoch 4 is complete enough that a future source producer can replace upstream binaries without silently changing archive classes, runtime paths, target identity, module surface, wheel behavior, relocation, metadata meaning, or consumer behavior.

Epoch 3 completes only when all mandatory gates pass and every selectable capability is consistent with the selection register.

## 10. Immediate execution order

```text
1. UT-0 exact official control
2. UT-1 truthful Astral archive prototype
3. UT-2 loader/relocation/launcher/getpath decision
4. UT-3 sysconfig and real native-extension wheel
5. UT-4 Android data and writable-state decisions
6. UT-5 capability matrices and feature-selection inputs
7. UT-6 minimum API and 16 KiB portability
8. UT-7 patch update and Python 3.15 preview
9. API-36 A/B/C comparison in parallel where source authority permits
10. E2-G8 evidence export and Epoch 3 selection register
```

The three highest-risk architecture experiments remain direct official adaptation, complete relative ELF lookup, and portable sysconfig proven by a real Android native-extension wheel.
