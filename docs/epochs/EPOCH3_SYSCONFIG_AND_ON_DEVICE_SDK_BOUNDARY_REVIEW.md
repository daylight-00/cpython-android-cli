# Epoch 3 sysconfig and on-device SDK boundary review

## 1. Status and purpose

This review reopens the current sysconfig and on-device native-extension SDK design before release selection. It does **not** alter any frozen archive, accepted authority, release-family identity, or product claim.

The review was triggered by the first RB-3 managed-Python qualification. The exact frozen install-only archive passed every system-interpreter uv path, but `uv python install` returned an error because the project renderer replaced CPython's canonical `_sysconfigdata_` header comment.

The immediate header defect is real, but it exposes a broader design question: whether the canonical runtime archive should continue to carry a project-wide reconstruction of producer metadata, or whether it should preserve the Python.org metadata and add only measured Android consumer adaptations.

## 2. Governing priorities

The decision order is:

1. preserve truthful Python.org and CPython upstream material wherever it already works;
2. match Astral's archive and consumer contract wherever the Android producer boundary permits;
3. add only bounded Android adaptations that are demonstrated necessary;
4. keep producer provenance distinct from runtime and SDK convenience;
5. do not promote an on-device SDK claim that depends on an undocumented post-build mutation;
6. supersede, rather than rewrite, frozen artifacts if a later profile is selected.

## 3. Evidence reviewed

The static review compared:

- the exact official `python-3.14.6-aarch64-linux-android.tar.gz` payload embedded in the canonical full artifact;
- the exact normalized `python/install/**` metadata from canonical full r4;
- `components/upstream-thin/lib/normalize.py`;
- the frozen UT-2 loader and relocation authority;
- the frozen UT-3 sysconfig and SDK authority;
- the exact Astral 3.14.6 golden observation used by E3 full qualification;
- the failed RB-3 r1 owner result using uv 0.11.28 for Android AArch64.

Machine-readable measurements are in:

- `experiments/epoch3-upstream-thin-release-blockers/rb3-sysconfig-boundary-static-review.json`

## 4. Findings

### 4.1 Runtime relocation did not require UT-3 normalization

UT-2 froze bounded Android runtime, relative native loader closure, subprocess re-entry, fresh venv creation after movement, and whole-prefix relocation before UT-3 introduced metadata normalization.

Therefore the current evidence does not support a claim that rewriting `_sysconfigdata_`, Makefile, pkg-config, or build-details is necessary for the core runtime.

CPython 3.14 also initializes core runtime prefix variables from `sys.prefix`, `sys.exec_prefix`, and their base-prefix equivalents after loading `_sysconfigdata_`. The raw producer file is not the sole authority for the active runtime prefix.

### 4.2 The current normalizer is not minimal

The exact comparison found:

- 84 changed literal `_sysconfigdata_` keys;
- 54 import-time override keys;
- seven mutated active metadata files;
- six explicit producer-provenance or build-directory overrides;
- four target-identity values redundantly overridden even though the official upstream values already match.

The current import-time block combines five distinct concerns:

1. runtime relocation;
2. consumer path convenience;
3. on-device compiler and linker policy;
4. producer provenance sanitization;
5. target identity.

These concerns do not have the same authority or mutation need and should not be treated as one indivisible profile.

### 4.3 Producer provenance is being replaced by consumer policy

The current profile replaces or synthesizes values such as:

- `BUILD_GNU_TYPE`;
- `CONFIG_ARGS`;
- `abs_builddir`;
- `abs_srcdir`;
- `builddir`;
- `srcdir`.

For example, the official producer truth records the Darwin build host, while the current active profile rewrites `BUILD_GNU_TYPE` to an Android target triple. That is convenient for a consumer view but is not producer provenance.

A selected successor must preserve producer facts or clearly expose them in a separate immutable producer record while keeping any consumer override explicitly named and bounded.

### 4.4 Zero producer absolute paths is not an Astral contract

The exact Astral golden `PYTHON.json` observation contains producer/build paths rooted under `/build`, `/install`, and `/tools`. The static review counted 52 such tokens.

Therefore the UT-3 condition that every active metadata string contain zero producer paths is a project-added condition. It is not required for Astral archive parity and must be justified field-by-field rather than treated as a global sanitization rule.

### 4.5 The RB-3 header failure was introduced by the project renderer

The official file begins with CPython's canonical line:

```python
# system configuration generated and used by the sysconfig module
```

The current renderer replaces it with:

```python
# system configuration normalized for relocatable Android consumers
```

Python execution ignores this semantic distinction, but uv's managed-Python installer uses the canonical header as a static format/provenance marker. System uv consumption passed because it executed an already installed interpreter; managed installation failed during archive post-processing.

A canonical-header-only profile is therefore a necessary control, but not by itself a sufficient final design decision.

### 4.6 User-built wheel repair is not a distributor contract

UT-3 successfully built, installed, relocated, and imported an Android native-extension wheel. The raw extension also contained a Termux toolchain RUNPATH:

```text
/data/data/com.termux/files/usr/bin/../../usr/lib
```

That RUNPATH belongs to the later user-controlled build environment and package build flow. It is not part of the distributed CPython artifact, and Astral-style standalone distribution does not imply automatic repair of every wheel later built by a consumer.

The earlier `patchelf --remove-rpath` experiment remains useful historical evidence that an external repair flow is possible. It is no longer an RB-3 acceptance condition and no built-in wheel repair feature is added to the upstream-thin product. Such work belongs to auditwheel-like external tooling or a separate future toy project.

The distributor remains responsible for Android-specific properties that it directly controls: all distributed ELF objects must be 16 KiB compatible, and the baseline extension produced with the compile/link flags supplied by profile M must also have 16 KiB LOAD alignment.

### 4.7 Existing selection records contain a tension

SEL-05 excludes a separate runtime-only flavor for Astral archive parity. SEL-06 places normalized sysconfig and the bounded on-device SDK inside the normal install tree.

That combination is valid only if the integrated SDK adaptation is both minimal and consumer-compatible. Current evidence does not yet establish that condition. The target profile experiment must resolve this tension before changing either selection.

## 5. Classification of current mutations

### Preserve from upstream unless a target test proves otherwise

- canonical `_sysconfigdata_` header;
- `CONFIG_ARGS`;
- `BUILD_GNU_TYPE`;
- actual producer build/source directories in the immutable producer record;
- already-correct Android `SOABI`, `MULTIARCH`, `EXT_SUFFIX`, and API level;
- dependency and build provenance.

### Candidate bounded consumer-path adaptations

- active include, library, config, and script paths derived from the moved runtime root;
- `python3.14-config` invocation that selects the exact runtime interpreter;
- Python pkg-config prefixes relative to `pcfiledir`;
- build-details paths and suffixes that are factually incorrect for the installed Android artifact.

### Candidate bounded on-device toolchain adaptations

- `CC`, `CXX`, `AR`, and `ARFLAGS`;
- Android-safe compile and shared-link flags;
- explicit 16 KiB linker policy;
- 16 KiB LOAD alignment produced by the supplied Android linker flags.

These must be measured independently from runtime relocation and producer provenance.

## 6. Required target profiles

No profile is selected by this static review.

### C — current control

The exact frozen install-only archive without modification.

Purpose:

- reproduce the current system pass and managed header failure;
- preserve a direct control for all other profile measurements.

### H — current profile with canonical header only

The exact current payload with only the first `_sysconfigdata_` line restored to the CPython canonical header.

Purpose:

- prove whether the observed uv failure is exactly the header contract;
- measure whether any later uv post-install check exposes another metadata issue.

This is an immediate compatibility control, not the preferred design by default, because it retains the broad provenance and identity overrides.

### U — upstream metadata restored

Keep the canonical launcher, RUNPATH adaptations, install tree, pip, and archive structure, but restore the official upstream versions of:

- `_sysconfigdata_`;
- `_sysconfig_vars_*.json`;
- `build-details.json`;
- Python Makefile;
- `python-config.py`;
- Python pkg-config files.

Purpose:

- determine whether raw upstream metadata already supports runtime, relocation, and uv managed installation;
- identify exactly which development surfaces fail without project adaptation.

### M — upstream-preserved minimal consumer/SDK overlay

Start from U, then add only measured consumer-path and on-device toolchain overrides. Preserve canonical header, producer `CONFIG_ARGS`, producer `BUILD_GNU_TYPE`, upstream target identity, and immutable producer records.

Purpose:

- find the smallest truthful integrated profile that supports required consumers;
- prove that the supplied SDK builds and imports a correctly aligned Android extension without claiming publication portability for the user-built wheel.

## 6.1 Host assembly result

The profile builder was run twice against the exact full and install-only artifacts. All four outputs were byte-identical across the two assemblies. The control output was byte-for-byte identical to the canonical install-only input.

| Profile | SHA-256 | Size | Host interpretation |
|---|---|---:|---|
| C | `84315c6967e56ed2ad3587ffcd459597835b18897f4988de9fc7c67a1bf38d76` | 23,841,726 | exact canonical install-only control |
| H | `4e8d4ae1292d729c629c3a8044ed7acb601bfe1493d9609f9c462862bd50686f` | 23,841,713 | header-only control |
| U | `e6460a41a4154c45be0bbd7ca6b70426d83221d487677c77018a1c1059aaeb55` | 23,842,209 | official active metadata restored |
| M | `d08e63dab00a7b43994cd6f7788ee827dfedfeeaf9bf183f40c9d5ee30df6639` | 23,843,530 | upstream-preserved minimal overlay probe |

These are experiment inputs only. None is a newly selected canonical artifact.

Machine evidence:

- `experiments/epoch3-upstream-thin-release-blockers/rb3-sysconfig-profile-host-assembly.json`

## 7. Required measurements for every profile

Each profile must record:

1. deterministic profile archive identity from two independent assemblies;
2. fresh extraction and moved-prefix Python identity;
3. all expected Android `SOABI`, `MULTIARCH`, platform, and version values;
4. uv system find, venv, run, and sync;
5. uv custom-catalog managed install, find, direct launch, venv, no-op reinstall, uninstall;
6. `python3.14-config` outputs;
7. Python pkg-config outputs;
8. a raw native-extension wheel build using the profile without prior mutation;
9. raw extension `DT_NEEDED`, RUNPATH/RPATH, ELF machine, and LOAD alignment;
10. hard confirmation that the baseline extension has 16 KiB LOAD alignment;
11. import before and after prefix relocation;
12. frozen input-family invariance.

RUNPATH/RPATH and `DT_NEEDED` for the user-built wheel are diagnostic inventory only. Repair or publication portability is outside this product contract.

## 8. Selection rules

A profile may be selected only if:

- it passes core runtime and relocation;
- uv managed install returns success, not merely a usable partially installed tree;
- it preserves truthful Android identity;
- every mutation has a field-level reason and pre/post identity;
- producer provenance is not silently replaced by consumer policy;
- the baseline native extension builds, installs, imports, and has 16 KiB LOAD alignment;
- no Termux native dependency or identity is introduced into the distributed product bytes;
- the old frozen family remains unchanged during the experiment.

If U passes every required consumer except on-device native builds, the default recommendation is to preserve upstream runtime metadata and revisit SEL-06 rather than retain broad canonical-runtime rewriting merely to keep an integrated SDK claim.

If M is necessary, it becomes a proposed successor profile and must trigger a new full → install-only → stripped → release-family lineage. Old frozen artifacts and authorities remain historical accepted evidence and are explicitly superseded; they are never edited in place.

## 9. Current conclusion

The current broad normalization is **not accepted as final design** by this review. It remains the frozen control artifact only.

The evidence presently supports these statements:

- upstream metadata was sufficient for the proven UT-2 runtime and relocation boundary;
- the global zero-producer-path rule was not inherited from Astral;
- the managed uv header failure was introduced by the HW-T whole-file renderer;
- user-built wheel postprocessing is outside the distributor contract, while 16 KiB alignment remains an Android distributor requirement;
- a target profile comparison is required before choosing header-only repair, upstream restoration, minimal overlay, or SDK boundary redesign.

No artifact byte, blocker closure, selectability claim, or publication claim changes until that experiment is accepted.

## 10. Accepted target result and profile selection

The C/H/U/M target probe completed successfully and returned a complete self-indexed result archive. The independent audit verified all four profile identities, protected-family invariance, and protected real managed-root invariance.

The observed decision matrix is:

| Profile | Runtime and uv | Native extension build | Producer truth | Decision |
|---|---|---|---|---|
| C | managed install fails on project header | passes | replaced by broad consumer profile | reject |
| H | passes | passes | still replaced by broad consumer profile | reject as non-minimal |
| U | passes | fails on unavailable macOS NDK compiler path | preserved | insufficient for local SDK |
| M | passes | passes | preserved | **selected** |

Profile M is selected because it preserves CPython's canonical header, upstream target identity, producer `CONFIG_ARGS`, producer `BUILD_GNU_TYPE`, and the upstream `_sysconfig_vars_` JSON while overlaying only measured consumer paths and the local Android compiler/linker entry points.

The selection does not make the experimental M archive canonical. It authorizes a successor full build from the exact official input using the production implementation of the same semantic boundary.

Machine authority:

- `experiments/epoch3-upstream-thin-release-blockers/rb3-sysconfig-profile-selection-authority.json`
- `experiments/epoch3-upstream-thin-release-blockers/rb3-sysconfig-boundary-r1-return-inspection.json`

## 11. Distributor and user-built-wheel responsibility boundary

Every profile that could build the probe extension recorded the same Termux toolchain RUNPATH. That observation is retained as diagnostic evidence, not converted into a distribution failure.

The selected contract is:

1. profile M must support native-extension build, installation, and import;
2. all distributed ELF objects must satisfy the 16 KiB Android alignment policy;
3. the baseline extension produced by profile M's supplied linker flags must also satisfy 16 KiB LOAD alignment;
4. raw wheel `DT_NEEDED`, RPATH, and RUNPATH are recorded for diagnosis only;
5. removal, dependency repair, rebundling, and publication portability of a user-created wheel belong to the user or external auditwheel-like tooling;
6. upstream-thin will not add a built-in wheel repair path. A separate future tool may explore it without expanding the standalone distribution contract.

Machine authority:

- `experiments/epoch3-upstream-thin-release-blockers/rb3-distributor-responsibility-reassessment.json`

## 12. Successor lineage

The frozen r4 full/install-only/stripped family remains valid and unchanged. It is not edited or silently reclassified.

The next bounded transition is:

```text
exact official archive + accepted launcher + profile M production implementation
  -> deterministic successor full r5 candidate
  -> Android target qualification and independent audit
```

Only after the full candidate is accepted may successor install-only, stripped, legal family, RB-1 binding, RB-2 rebinding, and final RB-3 closure proceed.

## 13. Successor r2 result and uv-managed representation correction

The successor r2 owner run resolved the r1 reproducibility defect. Independent assembly roots produced the same full archive bytes, and the exact candidate passed the complete Android runtime qualification. The direct profile-M baseline extension also built, installed, imported, and reported 16 KiB LOAD alignment.

The remaining failures separated into one verifier defect and one real managed-install representation defect:

1. CPython's upstream Android metadata reports `HOST_GNU_TYPE=aarch64-unknown-linux-android`. The prior verifier incorrectly required `aarch64-linux-android`, even though the preserved producer `CONFIG_ARGS` correctly records `host_alias=aarch64-linux-android`.
2. The first profile-M implementation preserved the upstream literal `build_time_vars` dictionary and appended `build_time_vars.update(...)`. Direct Python execution evaluated the update, but uv's managed installer parses only the canonical literal dictionary and serializes that parsed mapping after install-prefix and compiler normalization. The appended executable update was therefore lost in the managed installation.

The corrected representation keeps the selected profile-M boundary while matching uv's actual standalone consumer contract:

- producer `BUILD_GNU_TYPE`, producer `CONFIG_ARGS`, Android target identity, and `_sysconfig_vars_*.json` remain preserved;
- bounded static toolchain values, the profile marker, Android compile/link flags, and `/install` path placeholders are stored inside the canonical literal `build_time_vars` mapping;
- trailing executable code resolves only unpacked-install-root-dependent paths for direct standalone execution;
- uv replaces `/install` with its managed installation root, normalizes tool names such as `clang` to `cc`, and retains the profile-M marker and Android 16 KiB flags when it rewrites the canonical mapping;
- both direct and managed Python must build, install, and import the baseline native extension and produce a 16 KiB-aligned extension;
- RPATH and RUNPATH remain diagnostic-only user-wheel evidence and are not repaired by this product.

Machine records:

- `experiments/epoch3-upstream-thin-release-blockers/rb3-successor-full-m-r2-return-inspection.json`
- `experiments/epoch3-upstream-thin-release-blockers/rb3-successor-full-m-r3-correction-contract.json`
