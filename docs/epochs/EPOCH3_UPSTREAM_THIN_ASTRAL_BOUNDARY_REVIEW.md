# Epoch 3 upstream-thin Astral boundary review

> **Status:** E3-INIT working record — research and classification complete; selection authority not yet issued
> **Recorded:** 2026-07-21
> **Primary structural reference:** Astral `python-build-standalone`
> **Native input authority:** Python.org CPython Android package and its inherited BeeWare dependency products
> **Product model:** Astral-shaped, Python.org-produced, Android-adapted upstream-thin distribution
> **Selection rule:** this document supplies decision inputs; it does not by itself mark any `SEL-*` item selected

## 1. Purpose

Epoch 3 has entered initialization. This record freezes the detailed boundary review needed before the complete selection register, clean repository boundary, and product contract can be issued.

The final release archive has three non-negotiable requirements:

1. use the Python.org Android prebuilt and the BeeWare dependency products inherited through it rather than rebuilding CPython or its native dependency topology;
2. remain Android/Bionic native and require no Termux native provider or hard-coded Termux identity;
3. correspond to Astral's standalone distribution as closely as the upstream input permits, with Astral's archive structure as the highest-priority product-layout reference.

The review classifies every material surface into five groups:

1. Astral-style implementation that is impossible under upstream-thin;
2. implementation that can be identical to Astral's contract;
3. behavior or structure that can be replaced by a bounded Android/upstream adaptation;
4. claims or choices that still require an additional experiment;
5. functionality intentionally abandoned by upstream-thin because it requires a separate producer or dependency build.

## 2. Governing interpretation of “Astral 1:1”

“Astral 1:1” must mean **archive, metadata, flavor relationship, and consumer-contract correspondence**. It cannot mean identical producer internals.

Astral's full archive is the output of a project that builds and manages CPython, dependency sources, object files, static and shared libraries, extension candidates, optimization profiles, and relinking metadata. Python.org's Android release package is an embedding-oriented installed product. It does not contain the complete object and static-library graph needed to reproduce Astral's producer-level `full` semantics.

The Epoch 3 correspondence boundary is therefore:

| Layer | Epoch 3 requirement |
|---|---|
| Archive roots and flavor relationship | machine-checkable correspondence with Astral |
| Install-prefix layout | match Astral's standalone consumer shape where Android/upstream bytes permit |
| `PYTHON.json` schema and semantics | use Astral format and meanings for every truthfully observable field |
| Extraction and direct-execution contract | provide the corresponding standalone experience |
| Native CPython and dependency producer | intentionally different: Python.org and BeeWare remain the producer |
| Object tree, static archives, relinking graph | unavailable unless upstream supplies them |
| Optimization and module variants | inherited from upstream; not independently produced |

The resulting product is accurately described as:

```text
Astral-shaped
Python.org-produced
BeeWare-topology-inheriting
Android-adapted
upstream-thin standalone distribution
```

It must not be described as an Astral-produced Android build, a complete source build, or an object-complete relinking SDK.

## 3. Research basis and authority hierarchy

### 3.1 Project authorities

The local conclusions in this review are grounded in the following frozen authorities:

- [`ADR-0006`](../decisions/ADR-0006-UPSTREAM-DERIVED-EPOCH3-AND-SOURCE-PRODUCER-EPOCH4.md)
- [`ADR-0007`](../decisions/ADR-0007-EPOCH2-EVIDENCE-AND-EPOCH3-SELECTION-GATES.md)
- [`EPOCH3_CHARTER.md`](EPOCH3_CHARTER.md)
- [`EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md`](../roadmap/EPOCH2_REMAINING_WORK_AND_EPOCH3_COMPLETION_GATES.md)
- [`epoch3-initialization-contract.json`](../../experiments/epoch2-upstream-thin-closure/epoch3-initialization-contract.json)
- [`reference-hierarchy.json`](../../experiments/epoch2-upstream-thin-closure/reference-hierarchy.json)
- [`accepted-product-seed-boundary.json`](../../experiments/epoch2-upstream-thin-closure/accepted-product-seed-boundary.json)
- [`closure-authority.json`](../../experiments/epoch2-upstream-thin-closure/closure-authority.json)

The research tracks already closed in Epoch 2 are:

| Track | Frozen authority | Established input |
|---|---|---|
| UT-0 | [`upstream-control-authority.json`](../../experiments/epoch2-upstream-thin-control/upstream-control-authority.json) | exact official archive, topology, dependency closure, provenance |
| UT-1 | [`artifact-prototype-authority.json`](../../experiments/epoch2-upstream-thin-artifact-prototype/artifact-prototype-authority.json) | truthful Astral-style local artifact and metadata prototype |
| UT-2 | [`loader-relocation-authority.json`](../../experiments/epoch2-upstream-thin-loader-relocation/loader-relocation-authority.json) | launcher, relative loader closure, whole-prefix relocation |
| UT-3 | [`sysconfig-sdk-authority.json`](../../experiments/epoch2-upstream-thin-sysconfig-sdk/sysconfig-sdk-authority.json) | runtime metadata normalization and bounded on-device SDK evidence |
| UT-4 | [`android-data-policy-authority.json`](../../experiments/epoch2-upstream-thin-android-data-policy/android-data-policy-authority.json) | immutable install, updateable data, writable state separation |
| UT-5 | [`feature-qualification-authority.json`](../../experiments/epoch2-upstream-thin-feature-qualification/feature-qualification-authority.json) | explicit pip, subprocess, venv, multiprocessing boundaries |
| UT-6 | [`platform-portability-authority.json`](../../experiments/epoch2-upstream-thin-platform-portability/platform-portability-authority.json) | bounded Android context and static 16 KiB claims |
| UT-7 | [`upstream-evolution-authority.json`](../../experiments/epoch2-upstream-thin-upstream-evolution/upstream-evolution-authority.json) | patch-update and preview-version maintenance evidence |
| API 36 comparison | [`api36-controlled-comparison-authority.json`](../../experiments/epoch2-upstream-thin-api36-controlled-comparison/api36-controlled-comparison-authority.json) | controlled comparison only; no product input selection |

The raw planning reference closest to the active direction is:

- [`UPSTREAM_THIN_RESEARCH_AND_DESIGN_PLAN.md`](../references/raw/2026-07-19-upstream-thin-plan/UPSTREAM_THIN_RESEARCH_AND_DESIGN_PLAN.md)

The broader recalibration package remains background and Epoch 4 context rather than the immediate product implementation authority:

- [`2026-07-19-epoch2-epoch4-recalibration`](../references/raw/2026-07-19-epoch2-epoch4-recalibration/README.md)

### 3.2 External primary references reviewed

Astral:

- `docs/distributions.rst`: full archive, `PYTHON.json`, `build_info`, install-only projection
- `docs/running.rst`: flavor behavior, extraction and runtime expectations
- `docs/quirks.rst`: build-time path normalization and portability limitations
- `docs/status.rst`: Android is not an existing official Astral target
- `latest-release.json`: current release metadata observed on 2026-07-21 pointed to tag `20260718`

Official source locations:

- <https://github.com/astral-sh/python-build-standalone/blob/main/docs/distributions.rst>
- <https://github.com/astral-sh/python-build-standalone/blob/main/docs/running.rst>
- <https://github.com/astral-sh/python-build-standalone/blob/main/docs/quirks.rst>
- <https://github.com/astral-sh/python-build-standalone/blob/main/docs/status.rst>
- <https://github.com/astral-sh/python-build-standalone/blob/latest-release/latest-release.json>

CPython and BeeWare:

- CPython Android package/build README
- CPython's minimal POSIX launcher implementation in `Programs/python.c`
- BeeWare's CPython Android source-dependency project and precompiled dependency releases

Official source locations:

- <https://github.com/python/cpython/blob/main/Android/README.md>
- <https://github.com/python/cpython/blob/main/Programs/python.c>
- <https://github.com/beeware/cpython-android-source-deps>

## 4. Exact official upstream input currently frozen

```text
CPython version             3.14.6
target                      aarch64-linux-android
official minimum API        24
archive                     python-3.14.6-aarch64-linux-android.tar.gz
archive SHA-256             38bbe77d3167b5cd554e03b1021324926f09f3825202b065951dd7638e9c37e5
archive size                22,358,404 bytes
archive members             3,193
regular files               2,952
packaged ELF objects        80
native extensions           67
unresolved native edges     0
```

The inherited packaged dependency products observed in the exact official package are:

```text
libcrypto_python.so
libssl_python.so
libsqlite3_python.so
```

The official archive remains the immutable native input. API 36 source-equivalent variants are comparison evidence and are not product input unless a separate Epoch 3 decision selects them.

## 5. Meaning of “use the prebuilt unchanged”

A literal rule that every final file byte must equal the upstream archive is incompatible with the standalone requirement because:

- the official Android package does not provide a normal CLI executable;
- native objects need an accepted relative lookup topology for whole-prefix relocation without project-required `LD_LIBRARY_PATH`;
- runtime and consumer metadata may contain producer or staging paths inappropriate for the relocated product;
- standalone command and data surfaces may require project-owned wrappers or payloads.

The enforceable upstream-thin rule is:

### 5.1 Required

- do not rebuild CPython;
- do not rebuild or replace the inherited native dependency products;
- do not relink upstream `.so` files against a project-selected dependency topology;
- preserve the exact original archive and checksum as provenance input;
- copy every file unchanged unless it is covered by an enumerated transformation class;
- record every changed file with pre-change hash, post-change hash, operation, tool identity, and justification;
- classify all project-added bytes separately from upstream-derived bytes;
- inherit upstream module, API-floor, dependency-version, and shared/static topology decisions by default.

### 5.2 Forbidden

- replacing OpenSSL, SQLite, libffi, or another inherited provider with a project build;
- adding an upstream-missing C extension to the base product by building its dependencies;
- claiming a different NDK/API or optimization profile from the one evidenced by the official product;
- manufacturing fake object files, static archives, inittab artifacts, or producer metadata;
- describing project transformations as if Python.org or BeeWare produced those transformed bytes.

The producer split is:

```text
native producer identity          Python.org / BeeWare
product transformation authority  this project
```

## 6. Android-native and Termux-independence boundary

### 6.1 Already established statically and in the bounded runtime

The frozen evidence supports the following:

- Android/Bionic target identity;
- complete package-internal or Android-public native dependency closure;
- no unresolved packaged ELF dependency;
- no required Termux native library provider;
- no required hard-coded Termux prefix;
- no project-required `LD_LIBRARY_PATH`;
- no loader-bootstrap self re-execution;
- whole-prefix relocation;
- subprocess child re-entry using the same runtime identity;
- preservation of 16 KiB `PT_LOAD` alignment through accepted mutation;
- all required native extensions loading in the bounded tested context.

The direct runtime context was a Termux app process in the Android linker namespace. Termux served as an execution context, not as the native ABI or dependency provider.

### 6.2 Not yet established generally

The following remain unqualified unless separately tested and selected:

- arbitrary `adb shell` execution;
- root shell execution;
- app-private native executable execution;
- APK/JNI embedding;
- Android service processes;
- every vendor linker namespace and SELinux policy;
- emulator execution;
- other Android ABIs;
- actual runtime on a 16 KiB page-size device.

The initial CLI archive does not need APK packaging as a prerequisite. A non-Termux qualification is, however, the strongest remaining experiment for the final no-Termux-dependency claim.

## 7. Astral distribution contract observed

### 7.1 Full archive

Astral's canonical output is a `.tar.zst` archive. All archive members are prefixed with `python/`. The well-known layout is:

```text
python/
├── PYTHON.json
├── build/
└── install/
```

`python/install/` contains the working self-contained installation. `python/build/` conventionally contains build artifacts. `PYTHON.json` is the machine-readable consumer interface and must be used instead of path heuristics.

### 7.2 Install-only projection

Astral defines install-only as an exact projection of the full archive:

```text
full:         python/install/<path>
install-only: python/<path>
```

Everything outside `python/install/` is excluded from install-only. The Epoch 3 implementation must preserve this derivation relationship rather than producing full and install-only independently.

### 7.3 Install-only stripped

Astral defines `install_only_stripped` as install-only with debug symbols removed. The Epoch 2 prototype found no byte change after stripping 80 upstream ELF files. Epoch 3 therefore cannot assume this is a meaningful separate product without a new section-level and size-delta verification.

### 7.4 `PYTHON.json`

The current documented format version is 8. Important common fields include:

- `target_triple`;
- Python version and major/minor version;
- PEP 425 Python, ABI, and platform tags;
- implementation name, version, hexadecimal version, and cache tag;
- `python_paths` and `python_paths_abstract`;
- normalized `python_config_vars`;
- `python_exe`;
- source, bytecode, optimized-bytecode, debug-bytecode, and extension suffixes;
- bytecode magic;
- `libpython_link_mode`;
- extension loading modes;
- licenses and license paths;
- optional `build_info` describing producer build artifacts.

Astral's `build_info` is explicitly designed to enable downstream relinking and custom built-in extension assembly from core and extension object files. That producer-level purpose is the central semantic gap in upstream-thin.

## 8. Classification 1 — Astral-style implementation that is impossible

The following are structurally unavailable or forbidden under the current upstream-thin producer model.

### 8.1 Producer-complete Astral `full`

The official Android package does not include:

- CPython core object files;
- per-extension object files;
- static `libpython`;
- dependency static archives;
- a complete relinkable inittab object/source bundle;
- a complete compile and link command graph.

Therefore Epoch 3 cannot produce the same producer-complete `python/build/` or complete `build_info` that Astral can produce from its own source-build graph.

Epoch 3 may still produce a `python/build/` directory, but it must contain only truthful upstream-derived or project-produced audit material, such as:

```text
python/build/
├── upstream/
│   ├── input-manifest.json
│   └── input-checksums.json
├── launcher/
│   ├── source.c
│   └── build-record.json
├── mutations/
│   └── mutation-manifest.json
└── audit/
    ├── elf-inventory.json
    ├── extension-inventory.json
    └── dependency-closure.json
```

This is an **upstream-derived full archive**, not an object-complete producer full archive.

### 8.2 Astral static and relinking topology

The official Android package supplies shared `libpython` and shared native extensions. Thin cannot truthfully provide:

- static `libpython`;
- a default-static extension topology;
- extension-to-builtin conversion;
- custom built-in interpreter assembly;
- static dependency relinking;
- object-level extension variant selection.

`PYTHON.json` must report the actual shared linking and shared-library extension-loading modes.

### 8.3 Astral optimization-product matrix

Thin cannot independently produce or claim upstream-unavailable variants such as:

- `pgo`;
- `lto`;
- `pgo+lto`;
- BOLT variants;
- debug builds;
- free-threaded builds;
- JIT builds;
- separate noopt/optimized products;
- detached debug-symbol products.

`build_options` may contain only values proven by upstream metadata or direct evidence. An optimization profile must never be inferred from expected release practice.

### 8.4 Complete cross-build SDK

The official package does not supply a complete relocatable cross-build environment containing:

- NDK;
- Android sysroot;
- target compiler and toolchain closure;
- API-specific complete link environment;
- static dependency development archives;
- producer object graph.

A bounded on-device extension SDK is a different product and does not satisfy the complete Astral relinking SDK meaning.

### 8.5 Desktop-equivalent native module inventory

The official upstream package defines the maximum default native module surface. Modules or features absent because of Android platform policy or upstream build decisions cannot be restored in thin by building separate dependencies.

Any such addition would change the producer and dependency topology and belongs to Epoch 4 or a separate non-thin product.

## 9. Classification 2 — implementation that can be identical

The following should be tested for structural equality or exact semantic correspondence with Astral.

### 9.1 Canonical archive roots

Full:

```text
<distribution>-full.tar.zst
└── python/
    ├── PYTHON.json
    ├── build/
    └── install/
```

Install-only:

```text
<distribution>-install_only.tar.gz
└── python/
    ├── bin/
    ├── include/
    ├── lib/
    └── ...
```

The exact naming grammar will be frozen after the golden-archive comparison, but the `python/`, `python/install/`, and install-only projection rules are mandatory.

### 9.2 Standard standalone prefix shape

The final installed tree can use the normal standalone prefix shape:

```text
python/install/
├── bin/
│   ├── python
│   ├── python3
│   └── python3.14
├── include/
├── lib/
│   ├── libpython3.14.so
│   ├── python3.14/
│   ├── pkgconfig/
│   └── packaged upstream dependency products
└── share/                  # only when selected
```

Exact aliases, symlink direction, modes, and optional directories must be determined from the Astral golden fixture rather than memory or convention.

### 9.3 Common `PYTHON.json` schema fields

The following are observable and can be represented with Astral's schema and meanings:

- format version 8;
- target triple;
- Python version and major/minor version;
- Python, ABI, and platform tags;
- implementation fields;
- bytecode magic and suffixes;
- extension suffixes;
- `python_paths`;
- `python_paths_abstract`;
- runtime-appropriate `python_config_vars`;
- `python_exe` after launcher selection;
- shared libpython path and link mode;
- built-in and shared-library extension-loading support;
- licenses and license paths;
- truthful shared extension inventory.

### 9.4 Deterministic archive production

The project can equal or exceed Astral's consumer-facing determinism requirements through:

- sorted tar member order;
- normalized uid/gid;
- normalized timestamps;
- normalized permissions;
- safe relative symlinks;
- path-traversal rejection;
- reproducible compression parameters;
- content manifest;
- archive checksum;
- provenance and license aggregation;
- fail-closed verification;
- exact full-to-install-only projection testing.

### 9.5 Direct extraction and execution

The product can expose the expected standalone use pattern:

```sh
tar -xf <install-only-archive>
./python/bin/python3.14
```

No activation step, Termux package dependency, project-required `LD_LIBRARY_PATH`, or loader self-reexecution should be necessary.

## 10. Classification 3 — bounded replacements and adaptations

### 10.1 Standalone launcher

The official Android package is embedding-oriented and does not provide a normal Python CLI executable. The accepted replacement candidate is LA-2, based on CPython's own POSIX `Programs/python.c` model:

```c
#include <Python.h>

int main(int argc, char **argv) {
    return Py_BytesMain(argc, argv);
}
```

Classification:

```text
producer                 project
behavioral reference     CPython Programs/python.c
reason                   official Android package has no standalone executable
scope                    minimum CLI entry point only
```

The frozen UT-2 evidence already supports this launcher family with whole-prefix relocation and subprocess child re-entry. Epoch 3 must decide adoption and then run final-archive regression qualification rather than reopen launcher exploration without a new failure.

### 10.2 Relocatable native loader closure

Astral controls its link topology while building. Thin inherits already-built ELF files, so the accepted replacement is LR-3:

- object-specific relative `RUNPATH` values;
- `$ORIGIN`-relative package-internal lookup;
- no project-required `LD_LIBRARY_PATH`;
- no loader bootstrap or self re-execution;
- preserved 16 KiB `PT_LOAD` alignment;
- exact pre/post mutation records;
- relocated extension import and subprocess re-entry.

This differs at the producer-byte level but can provide the corresponding standalone consumer contract.

### 10.3 Runtime and sysconfig normalization

The embedding package and its producer metadata may retain absolute build or staging paths. Astral also documents build-time path residue and expects consumers such as uv to repair installation paths.

The thin replacement must separate:

- immutable producer provenance, which is preserved;
- runtime-active paths, which are recomputed or normalized to the current prefix;
- SDK metadata, which is included only for a selected SDK flavor.

Runtime-only products must not imply a complete cross-build environment.

### 10.4 Upstream-derived `full`

The producer-artifact role of Astral `full` is replaced by an upstream-derived reconstruction and audit role containing:

- exact upstream input identity and checksum;
- upstream archive member manifest;
- final install tree;
- launcher source and build record;
- accepted ELF mutation manifest;
- before and after hashes;
- dependency and extension inventories;
- licenses and provenance;
- qualification records;
- final `PYTHON.json`.

Allowed description:

```text
Astral-structured upstream-derived full archive
```

Forbidden descriptions:

```text
Astral-equivalent producer full
complete relinkable build
source-built distribution
complete object-tree archive
```

### 10.5 Dependency management

Astral's source, version, patch, and link ownership is replaced with upstream inheritance and closure auditing:

```text
dependency ownership       Python.org / BeeWare
dependency selection       inherited from the official CPython Android package
dependency bytes           extracted from the exact official package
build metadata             only upstream-available evidence
project responsibility     inventory, closure verification, provenance, mutation accounting
```

The project is a dependency-closure auditor and product transformer, not the dependency producer.

### 10.6 pip

Astral normally includes pip for end-user package installation. The official Android package does not contain an already-installed base pip command surface, but it contains upstream `ensurepip` material.

The thin replacement candidate is:

1. identify the exact upstream-provided pip wheel or bootstrap material;
2. install package contents deterministically into the final prefix when base pip is selected;
3. avoid relocation-bound absolute shebang scripts;
4. define `python -m pip` as the minimum stable interface;
5. add relocation-safe `pip`, `pip3`, and `pip3.14` wrappers only if command parity is selected and qualified.

This remains a selection decision, not an automatic consequence of a passing experiment.

### 10.7 CA and timezone data

CA and timezone payloads can be project-supported without changing native producer identity. The established three-root model is:

```text
INSTALL_ROOT  immutable relocatable Python product
DATA_ROOT     independently updateable CA and timezone payloads
STATE_ROOT    caller-provided writable cache, temp, user-site, venv, and bytecode state
```

A selected payload requires provider identity, version, license, deterministic transformation, update owner, rollback lineage, caller override, and missing/corrupt-data behavior.

### 10.8 Bounded on-device SDK

The official package contains headers, shared `libpython`, pkg-config material, and enough metadata for a bounded on-device extension build. UT-3 demonstrated an Android-tagged native wheel build, installation, prefix relocation, and import in the tested environment.

The truthful name is:

```text
upstream-derived on-device extension SDK
```

It does not include or imply:

- static relinking;
- custom built-in modules;
- host cross-compilation;
- dependency rebuilding;
- complete object-level `build_info`.

## 11. Classification 4 — additional experiments still required

Existing Epoch 2 experiments must not be repeated unless a final product choice or an unresolved claim requires it. The remaining bounded experiments are:

### E3-X1 — Astral golden archive conformance

Freeze one current POSIX Astral release as a golden structural fixture and capture:

- full member tree;
- install-only member tree;
- stripped member tree;
- archive filename grammar;
- root and directory structure;
- symlink names and targets;
- file modes;
- empty-directory behavior;
- test-package and test-extension filtering;
- complete `PYTHON.json` key set;
- absent versus null versus empty-field conventions;
- compression formats and options;
- exact full-to-install-only projection delta.

Expected records:

```text
astral-golden-contract.json
astral-full-members.txt
astral-install-only-members.txt
astral-python-json-observation.json
```

The current Astral release pointer observed during this review was tag `20260718`; the fixture must pin exact archive asset checksums rather than only the mutable latest pointer.

### E3-X2 — Final launcher behavior parity

This is final-product regression qualification, not a new launcher search. Test:

- `-c`;
- `-m`;
- script path;
- stdin;
- interactive REPL;
- common command-line flags;
- exit status;
- signals;
- `sys.executable`;
- `sys.prefix` and `sys.base_prefix`;
- real path, in-tree symlink, and external symlink execution;
- relative and absolute `argv[0]`;
- arbitrary working directory;
- whole-prefix relocation;
- subprocess child identity;
- read-only install.

### E3-X3 — Install-only filtering

Use the golden Astral fixture to determine whether and how install-only excludes:

- pure-Python `test` packages;
- test-only C extensions;
- producer-only metadata;
- development-only files.

Every removal must preserve the selected native closure and direct-execution contract. Size reduction alone is not sufficient authority for divergence.

### E3-X4 — `install_only_stripped` meaning

Run an exact section census and strip comparison covering:

- `.debug_*` sections;
- `.symtab` and `.strtab`;
- archive and installed size delta;
- Android LLVM strip versus other strip tools;
- build-id preservation;
- relative `RUNPATH` preservation;
- 16 KiB alignment preservation;
- runtime and extension-import regression.

Allowed outcomes:

| Result | Product decision enabled |
|---|---|
| meaningful safe byte and size difference | separate stripped flavor |
| exact byte identity | do not present it as a distinct product |
| identity but catalog compatibility requires the name | explicit alias with identical checksum disclosure |
| runtime, alignment, or provenance damage | exclude stripped flavor |

### E3-X5 — pip command wrappers

Required only if `pip`, `pip3`, and `pip3.14` executable parity is selected beyond `python -m pip`.

Test:

- no absolute shebang dependency;
- whole-prefix relocation;
- symlinked `bin` execution;
- paths containing spaces;
- read-only install;
- `/system/bin/sh` or binary-wrapper contract;
- subprocess identity;
- venv wrapper interaction.

### E3-X6 — Real Astral consumer compatibility

Test the resulting `PYTHON.json` and release records with at least one real Astral/PBS-aware consumer or parser. Verify:

- format version 8 parsing;
- Android target triple handling;
- `python_exe` resolution;
- shared `libpython` handling;
- absent or partial `build_info` handling;
- unknown project extension-field handling;
- archive flavor selection;
- catalog lookup.

If a consumer requires complete producer `build_info`, that consumer feature must be declared unsupported. Fake object metadata is forbidden.

### E3-X7 — Non-Termux Android execution

To strengthen the final Termux-independence claim, qualify at least one context whose native execution is not hosted by the Termux app process.

Priority order:

1. ordinary `adb shell` or another direct Android shell context;
2. app-private native executable context;
3. APK/JNI embedding as a separate consumer integration, not an initial CLI prerequisite.

Check executable permissions, Android dynamic linking, linker namespace, SELinux denial, relative `RUNPATH`, writable state, CA/timezone discovery, extension imports, and selected subprocess behavior.

### E3-X8 — Minimum API and actual 16 KiB device support

Keep separate fields and claims for:

```text
upstream_build_api_floor
project_qualified_minimum_api
```

The official package's API 24 floor is not by itself proof that the complete transformed product has been qualified on API 24.

Likewise distinguish:

```text
static 16 KiB ELF compatibility
actual 16 KiB page-size device runtime qualification
```

The first is already supported in the accepted mutation path. The second requires a real qualifying device.

### E3-X9 — Production CA and timezone payloads

Before product adoption, verify:

- exact provider and source;
- version pin;
- checksums;
- deterministic transformation;
- licenses;
- payload manifest;
- update and rollback;
- environment override;
- missing and corrupt payload failure behavior;
- continued read-only install operation.

## 12. Classification 5 — intentionally abandoned by upstream-thin

The following are explicit initial thin non-goals rather than silently incomplete work:

| Abandoned surface | Reason |
|---|---|
| Upstream-missing native extensions | separate source and dependency builds would be required |
| Dependency static archives | not present in the official package |
| Static `libpython` | contradicts the inherited topology |
| Custom built-in extension relinking | object and inittab material unavailable |
| Complete Astral producer `build_info` | producer object graph unavailable |
| Complete cross-build SDK and bundled NDK | separate toolchain product required |
| API 36 custom rebuilt product | violates the default official-prebuilt-only rule unless separately selected |
| Independent PGO/LTO/BOLT/debug variants | not supplied as official upstream products |
| Free-threaded or JIT variants | unavailable unless Python.org supplies corresponding official packages |
| Desktop Astral module inventory parity | Android upstream module surface is the thin ceiling |
| Separate readline, curses, Tk, GDBM, or equivalent dependency builds | would make the project a dependency producer |
| All Android ABIs from one input | each ABI needs its own official package and qualification |
| Arbitrary relocation of pre-existing venvs | embedded absolute identity requires recreation or a separately qualified transformer |
| Blanket multiprocessing support | the tested environment provided no passing primitive/start-method surface |
| APK packaging as the initial CLI archive | separate consumer integration layer |
| Source-producer host isolation and libffi producer work | Epoch 4 responsibility |

These exclusions do not prevent a later Epoch 4 source producer from reproducing the selected Epoch 3 product contract with broader producer ownership.

## 13. Proposed canonical archive contract

### 13.1 Full

```text
cpython-3.14.6+<project-release>-aarch64-linux-android-full.tar.zst

python/
├── PYTHON.json
├── build/
│   ├── upstream/
│   │   ├── input.json
│   │   ├── input.sha256
│   │   └── member-manifest.json
│   ├── launcher/
│   │   ├── source.c
│   │   └── build-record.json
│   ├── mutations/
│   │   └── mutation-manifest.json
│   └── audit/
│       ├── elf-inventory.json
│       ├── extension-inventory.json
│       └── dependency-closure.json
└── install/
    ├── bin/
    ├── include/
    ├── lib/
    └── ...
```

The exact internal `build/` names remain subject to E3-X1. The semantic rules are already fixed:

- no fake objects;
- no fake static libraries;
- no inferred build commands;
- upstream-owned and project-owned bytes are separated;
- the archive does not claim producer completeness.

### 13.2 Install-only

```text
cpython-3.14.6+<project-release>-aarch64-linux-android-install_only.tar.gz

python/
├── bin/
├── include/
├── lib/
└── ...
```

It must be generated only by:

```text
select python/install/** from full
remove the leading python/install/
prepend python/
exclude everything else
```

Full and install-only must not be independently staged because that would weaken the projection guarantee.

### 13.3 Install-only stripped

Exactly one policy must be selected:

```text
A. a byte-distinct safe stripped archive;
B. an explicit catalog alias whose identical checksum is disclosed;
C. no stripped publication.
```

## 14. `PYTHON.json` boundary

### 14.1 Directly representable Astral fields

The final metadata can truthfully provide:

```text
version
target_triple
python_tag
python_abi_tag
python_platform_tag
python_version
python_major_minor_version
python implementation fields
python_paths
python_paths_abstract
python_config_vars
python_exe
python_suffixes
python_bytecode_magic_number
libpython_link_mode
python_extension_module_loading
licenses
license_path
```

After launcher adoption, `python_exe` should be a distribution-relative path such as:

```json
{
  "python_exe": "install/bin/python3.14"
}
```

The final path must follow the exact Astral full-archive convention observed by E3-X1.

### 14.2 Fields that must be absent, partial, or explicitly unavailable

The following cannot be populated as if complete:

```text
build_info.core.objs
build_info.core.static_lib
build_info.core.inittab_object
build_info.core.inittab_source
build_info.extensions[*].objs
build_info.extensions[*].static_lib
complete dependency relinking graph
```

Shared-library paths and other directly observable material may be represented where the Astral schema permits partial information.

### 14.3 Project-specific metadata

Project provenance may need additional information such as:

```text
distribution model
upstream provider and checksum
Android API floor
mutation manifest path
producer completeness
Termux native provider count
qualification claim boundary
```

The preferred design is either:

1. a namespaced `PYTHON.json` extension if real consumers tolerate unknown keys; or
2. a separate adjacent project metadata document if consumers reject unknown top-level keys.

E3-X6 decides this. Standard Astral fields must never be repurposed with project-specific meanings.

## 15. Provisional E3-INIT disposition candidates

These are strong decision candidates, not the final selection register.

| Selection surface | Provisional direction |
|---|---|
| Base pip | `adopt-with-redesign`: exact upstream bootstrap material, package-only installation |
| pip wrappers | experiment-driven `adopt-with-redesign` or `exclude`; `python -m pip` remains minimum |
| CA payload | `adopt-with-redesign`: DATA_ROOT product with independent update policy |
| timezone payload | `adopt-with-redesign`: DATA_ROOT product with independent update policy |
| Astral install-only | `adopt`: exact full-install projection |
| Separate runtime-only product | preserve as a representationally necessary selected flavor without replacing Astral install-only semantics |
| On-device SDK | optional `adopt-with-redesign`, explicitly bounded |
| Cross-build SDK | `defer-to-epoch4` |
| Subprocess core | bounded `adopt` for individually proven cases |
| Subprocess secondary | individually select; explicit Android shell; exclude `preexec_fn` by default |
| Venv | bounded `adopt`; fresh venv after relocation; recreate pre-existing venv after base movement |
| Multiprocessing | initial thin `exclude` |
| uv | external/system-interpreter contract first; managed catalog only after consumer validation |
| `install_only_stripped` | E3-X4 decides separate flavor, alias, or omission |
| Debug/symbol product | initial thin `exclude` |
| Test material | full preservation and install-only projection determined by E3-X1/E3-X3 |
| Native input | official API-floor Python.org package by default |
| API 36 custom input | `defer-to-epoch4` or a later separate product decision |
| Minimum supported API | separate qualification decision; do not equate automatically with upstream API 24 build floor |
| 16 KiB claim | static compatibility only until a real 16 KiB device passes |
| Execution contexts | bounded current context plus E3-X7; APK is separate integration |
| Release cadence | follow official Python patch releases; separately operate CA/timezone updates |

## 16. Existing contract corrections required

Earlier source-producer-oriented contracts and incubator documents may contain assumptions that must not govern the Epoch 3 upstream-thin release without an explicit new selection. Examples include:

- treating `install_only_stripped` as the primary product without proving a byte difference;
- treating `.tar.zst` as the only install-only compression despite Astral's gzip compatibility publication;
- coupling runtime and complete development/relinking material;
- assuming a complete producer façade behind `full`;
- implying source object/static material that the official package does not contain;
- allowing API 36 or source-build machinery to enter the default product path;
- mixing runtime-only, on-device SDK, and cross-build SDK claims.

The new Epoch 3 product contract must explicitly supersede these assumptions while preserving valid controls:

- deterministic archive generation;
- safe symlinks;
- exact manifest and checksum production;
- fail-closed verification;
- provenance and license closure;
- qualification and claim-boundary records.

## 17. Initialization decision boundary

Epoch 3 Init must transform this review into four controlled outputs:

1. **selection register** — every `SEL-01` through `SEL-18` receives exactly one disposition;
2. **deviation and adaptation register** — every departure from upstream bytes or direct Astral implementation is enumerated;
3. **additional experiment register** — only E3-X experiments required by selected claims are authorized;
4. **product and archive contract freeze** — archive roots, flavors, metadata, producer identity, support claims, update ownership, and release qualification are fixed before implementation expands.

The concise boundary is:

```text
Implement identically:
  Astral archive roots, flavor projection, metadata schema,
  install layout, extraction contract, and release-facing structure.

Replace for Android/upstream constraints:
  executable launcher, loader relocation, active runtime metadata,
  optional pip commands, CA/timezone/state roots.

Inherit exactly from upstream:
  CPython and dependency native products, module topology,
  build API floor, linkage topology, and dependency versions.

Omit truthfully:
  object files, static libraries, complete build_info,
  unavailable modules, and unavailable optimization variants.

Do not perform in thin:
  CPython or dependency builds, custom native modules,
  complete cross-SDK production, API 36 rebuilds,
  or a complete source producer.
```

## 18. Final product definition enabled by this review

The target Epoch 3 product is:

> An aarch64 Android/Bionic standalone CPython distribution derived from the exact official Python.org Android embedding package, inheriting the packaged BeeWare dependency topology without rebuilding it, applying only enumerated minimum launcher, relative-loader, metadata, and selected data adaptations, and serializing the result according to Astral's full/install-only archive and consumer-metadata contract as far as upstream evidence truthfully permits.

This definition satisfies the three top-level requirements without falsely claiming Astral producer internals or project ownership of CPython and dependency builds.
