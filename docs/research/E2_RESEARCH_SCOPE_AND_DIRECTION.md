# Epoch 2 Research Scope Review and Direction

> **Status:** independently reviewed and confirmed against the current repository state  
> **Verified:** 2026-07-18  
> **Scope:** the current repository as an experiment and evidence incubator  
> **Explicit exclusion:** this document does not design Epoch 3 or the future clean release repository

## 1. Correct interpretation of the current repository

The current repository is not the final distribution repository. It is an evidence-bearing research environment whose output will inform a later clean repository for an Astral-like Android standalone CPython distribution.

Complex experiments, failed approaches, source reconstruction, detailed evidence, and temporary contracts are therefore legitimate here. They should not be judged by whether every file belongs in the final product.

The correct review question is:

> Does each experiment reduce a real uncertainty about Android standalone CPython or determine a future design choice?

An experiment becomes self-serving when its main result is only a stronger restatement of an already accepted authority, without changing an Android adaptation decision, a product requirement, or a future implementation boundary.

## 2. Epoch 2 mission

Epoch 2 should complete the **fundamental Android adaptation research** required before a later epoch can implement and publish the final Astral-like product form.

Epoch 2 should discover and preserve evidence for:

- how an official embedding-oriented CPython Android prefix becomes a normal command-line interpreter;
- what launcher and environment adaptation Android requires;
- whether the runtime is truly Android/Bionic-native rather than accidentally Termux-linked;
- what relocation, certificate, timezone, temporary-directory, and subprocess behavior is required;
- whether pip, venv, native package builds, and uv workflows behave correctly;
- how upstream CPython Android packages and BeeWare dependency products should be consumed;
- which modern API-floor changes are technically useful;
- whether the same thin adaptation survives upstream patch and minor-version changes;
- what platform constraints a later distribution contract must express.

Epoch 2 should not attempt to finalize the complete release repository, permanent catalog, stable publication workflow, or long-term installer architecture. Those structural choices should be informed by completed experiments rather than becoming substitutes for them.

## 3. What the project has already achieved

### 3.1 Standalone launcher architecture

The project identified and implemented a concrete Android launcher model:

- locate the real executable through `/proc/self/exe`;
- derive the installation prefix and private library directory;
- normalize `LD_LIBRARY_PATH`;
- discover or preserve a CA bundle;
- re-execute once when loader state must be repaired;
- initialize CPython with `PyConfig` and preserve normal argument handling and `Py_RunMain` behavior.

This is core product research. It answers a question that the official embedding package does not answer.

### 3.2 Whole-prefix relocation

The project demonstrated that the runtime can be moved between unrelated paths while preserving runtime identity and behavior. It distinguished product mutation from relocation and developed checks that avoid invalidating the input under test.

This is directly relevant to any install-only or uv-managed distribution.

### 3.3 Native closure and extension surface

The project inventoried the ELF closure, classified runtime-internal and Android-system dependencies, rejected unresolved edges, and checked isolated native-extension imports. The frozen result found no Termux-native ELF dependency.

This establishes the central architectural claim: Termux is the primary shell profile, not the binary ABI provider.

### 3.4 Host data boundaries

The project separated executable/runtime identity from host-provided data such as:

- TLS certificate trust;
- timezone data;
- temporary storage;
- writable user state.

That separation is necessary for a relocatable Android core and should remain a first-class research topic.

### 3.5 Upstream producer understanding

The repository reconstructed and audited the CPython Android producer path and BeeWare dependency inputs. It also proved that a bounded Termux-native source build is possible.

This work established:

- the official upstream chain;
- exact dependency provenance;
- API and NDK decisions;
- source-build fallback feasibility;
- the boundary between upstream production and local adaptation.

The question is now substantially answered. Repeating the full reconstruction for every patch release is not automatically useful.

### 3.6 Artifact and consumer boundaries

Epoch 1 and early Epoch 2 established archive, ownership, lifecycle, transition, acquisition, and consumer-boundary concepts. Epoch 2 also defined a standalone archive shape and a stable build/package/verify façade.

These are useful preparatory results. They should now support experiments rather than continuously expanding before the remaining Android questions are answered.

## 4. The real E2-P3 result confirms the archive boundary

E2-P3 asks an important product-level question:

> Does the final extracted archive, without a producer tree or installer, operate as a standalone Android/Bionic Python product?

The corrected `termux-real` run has now answered that question for one real device profile. It consumed the exact frozen archive without rebuilding or repackaging and produced:

```text
profile             termux-real
host                real Android / Termux / aarch64
host Android API    36
qualification       35/35
result verification 19/19
independent review  38/38
product mutation    none
```

The accepted checks cover relocation, runtime identity, native closure, 67/67 extension imports, HTTPS, venv, offline pip installation, explicit-interpreter uv workflows, wheel tags, and product fidelity.

This result is not an experiment for its own sake. It validates the actual archive handoff boundary that a future clean repository will depend on.

The real device ran Android API 36, while the artifact itself retains an API-24 minimum. This proves modern-host behavior; it does **not** independently prove execution on the oldest claimed API level.

### Confirmed direction

Run only the remaining `termux-emulator` profile against the same frozen envelope and corrected harness. Do not rerun the producer, package step, or accepted real-device profile. Keep combined E2-P3 acceptance separate from metadata finalization, publication, installer work, and the wider post-E2-P3 research-scope transition.

## 5. Structural work should pause after the remaining E2-P3 boundary

The repository currently contains a detailed chain of producer authority, artifact authority, façade binding, execution authority, envelope authority, qualification contract, and independent verification.

That chain was useful to prove one complete provenance path. Continuing to subdivide the same product into more authority layers is unlikely to answer a new Android question.

### Stop or pause

After the emulator and combined E2-P3 qualification boundary closes, do not make the default next action another layer of:

- binding contracts over already frozen bindings;
- exact Git-blob restatements of an existing commit identity;
- new metadata schemas without a demonstrated consumer requirement;
- repeated full producer reconstruction for each patch release;
- installer transition matrices that repeat already accepted Epoch 1 behavior;
- exact ELF or extension counts treated as permanent cross-version invariants;
- release publication mechanics before the research inputs are stable.

These artifacts may remain as historical evidence. The recommendation is to stop expanding them by default.

## 6. Fundamental experiments that should continue in Epoch 2

### 6.1 Direct upstream-artifact adaptation

The current research should explicitly prove the thinnest intended main path:

```text
verified python.org Android package
  -> extract official prefix
  -> overlay the minimum standalone launcher
  -> normalize only demonstrated Android boundaries
  -> qualify the resulting archive
```

This experiment should compare the result with the reconstructed producer product and determine whether any local source build is actually required for the main path.

**Stop condition:** the direct upstream artifact passes the same essential standalone tests, and all local mutations are enumerated and justified.

### 6.2 Upstream update rehearsal

A future low-maintenance distribution must survive routine upstream changes. Epoch 2 should perform at least one controlled update rehearsal in which the pipeline moves to another official CPython Android patch release by changing primarily:

- version;
- source locator;
- digest;
- expected upstream metadata.

The goal is not to freeze another large authority chain. The goal is to discover hidden version-specific assumptions in launcher, path handling, package filtering, metadata generation, and tests.

**Stop condition:** an upstream patch update requires only bounded configuration changes, or every required code change has a documented Android reason.

### 6.3 Python 3.15 preview adaptation

Python 3.15 should be used as a research input, not a stable product. It can reveal:

- launcher/API compatibility changes;
- standard-library and extension-surface changes;
- path and sysconfig assumptions tied to 3.14;
- Android API interactions such as pidfd-based timed subprocess waits;
- changes required when the official 3.15 Android package becomes available.

**Stop condition:** the project has a concise delta report between the 3.14 adaptation and the current 3.15 prerelease, with no release claim.

### 6.4 API-floor comparison, including API 36

API 36 belongs in Epoch 2 because it is a platform experiment, not a final release policy.

Use three bounded variants:

| Variant | Purpose |
|---|---|
| official upstream control | preserve the accepted API-24 upstream product |
| CPython/launcher API 36 | isolate modern CPython and launcher effects while reusing upstream dependencies |
| all-components API 36 | test dependency-floor unification only if a question remains after the minimal build |

Measure behavior, performance, binary closure, source delta, patch count, and maintenance cost. Do not create a parallel release architecture for the experiment.

**Stop condition:** the measured benefit and required ownership are known well enough to recommend retain, archive, or discontinue.

### 6.5 Oldest-floor and modern-device qualification

The upstream product claims API 24 compatibility. A future distribution should distinguish:

- the minimum supported runtime environment;
- the accepted current real Termux device on API 36;
- a modern emulator or another current device.

The accepted API-36 host result must not be used as proof of API-24 runtime compatibility.

**Stop condition:** the compatibility claim is backed by at least one credible minimum-floor execution environment and one modern environment, or the limitation is explicitly recorded.

### 6.6 16 KB page-size compatibility

Android 15 introduced devices with 16 KB memory pages. Native binaries must have compatible ELF alignment and must not assume a 4 KB page size. The current BeeWare Android environment already uses a 16 KB maximum-page-size linker policy, but the final assembled runtime still requires direct verification.

Epoch 2 should verify:

- ELF load-segment alignment across the complete runtime;
- execution on a 16 KB Android environment;
- absence of unsafe hard-coded page-size assumptions in project-owned code;
- unchanged extension imports and subprocess behavior.

**Stop condition:** the upstream-derived archive and project launcher run in a 16 KB environment without compatibility fallback, or the exact incompatible component is identified.

### 6.7 Native extension build capability

A standalone distribution intended for pip and uv workloads must do more than install a pure-Python wheel. The development payload should support a small, controlled Android-native extension build.

The experiment should establish:

- correct headers and `libpython` development metadata;
- compiler and linker discovery policy;
- Android wheel tag generation;
- whether building on-device, cross-building, or both are supported claims;
- how upstream package limitations affect third-party native extensions.

This is more fundamental than adding another release sidecar because it determines whether the development payload has real consumer value.

**Stop condition:** one minimal native extension can be built, installed, imported, relocated, and rebuilt from a clean environment, or the unsupported boundary is explicitly defined.

### 6.8 Shell and host-profile boundary

The charter correctly says Termux-first, not Termux-bound. The core binary should not require the Termux package identity or native libraries.

Epoch 2 should retain Termux as the primary interactive profile but add bounded probes for at least one non-Termux Android execution context where practical, such as an adb or controlled app-private shell environment.

The purpose is not to provide a polished UX outside Termux. It is to discover which assumptions belong to the core and which belong to the Termux profile, especially for CA trust, home, temporary storage, and terminal behavior.

**Stop condition:** the core launcher/runtime boundary is documented by evidence from more than one host profile, or the reasons for a Termux-only claim are explicit.

### 6.9 License and source-offer evidence

The current standalone envelope records the CPython license but marks dependency-license completion as unfinished. Because the product redistributes native dependency binaries, Epoch 2 should identify the authoritative license texts and corresponding source provenance for every distributed component.

Final presentation belongs to the future release repository, but the source-of-truth mapping is fundamental research and should be completed now.

**Stop condition:** every distributed upstream component maps to an exact version, source, license identity, and redistributable license text.

### 6.10 Consumer requirements for uv

Epoch 2 should continue explicit-interpreter uv tests and determine the minimum catalog and installation properties needed for managed-Python integration.

It should not yet design the final upstream contribution, permanent catalog format, or full installer. The research output should be a consumer-requirements report:

- canonical target identity;
- archive root and executable path;
- relocation expectations;
- download and checksum requirements;
- Python version/ABI/platform metadata;
- upgrade and uninstall assumptions;
- Android-specific discovery constraints.

**Stop condition:** the project can state exactly what a future uv integration must consume, without implementing the final integration architecture.

## 7. Experiments that should normally end

The following questions now have enough evidence to stop being default workstreams.

### 7.1 Whether a standalone launcher is possible

Answered. Future launcher work should be driven by a specific failing behavior or cross-version experiment.

### 7.2 Whether the prefix can relocate

Answered for the tested product. Future work should validate new upstream products, not redesign relocation without evidence.

### 7.3 Whether the current runtime has unresolved or Termux-native ELF edges

Answered for the frozen product. Keep the verifier, but do not turn exact object and edge counts into permanent product identity.

### 7.4 Whether the official producer can be reconstructed

Substantially answered. Preserve the source-build path as experimental fallback and use it for API-36 research, not as a mandatory main-release stage.

### 7.5 Whether a highly detailed authority chain can be constructed

Answered. Further detail should require a concrete consumer, security, or reproducibility need.

### 7.6 Full installer lifecycle expansion

Epoch 1 already explored ownership, recovery, transitions, acquisition, and publication boundaries. Do not repeat the entire lifecycle before uv consumer requirements and the final artifact input are known.

## 8. Experiment admission rule

Every new Epoch 2 experiment should begin with five explicit fields:

```text
Question
What is not yet known?

Decision
What future choice changes based on the result?

Variants
What control and comparison builds are required?

Measurements
What evidence answers the question?

Stop condition
When is the question considered closed?
```

A proposed experiment should be rejected or reduced when its only decision is “create a stronger authority for the same already accepted result.”

## 9. Evidence policy

Detailed evidence remains appropriate in this repository. The adjustment is not to reduce rigor, but to connect rigor to research questions.

Preferred evidence:

- exact input identities and upstream references;
- reproducible commands and machine-readable results;
- positive and negative behavioral probes;
- before/after product fingerprints where mutation matters;
- device, Android, kernel, NDK, and page-size identity;
- explicit local patches and source deltas;
- comparison results between controlled variants;
- documented failed approaches that explain a selected design.

Evidence should record counts as observations, while contracts should primarily protect semantic invariants such as zero unresolved dependencies and zero failed extension imports.

## 10. Suggested remaining Epoch 2 sequence

This is a research sequence, not an Epoch 3 design:

1. run the separate `termux-emulator` qualification against the exact frozen E2-P3 input;
2. close combined E2-P3 qualification without rerunning the accepted producer, package, or real-device profile;
3. validate direct adaptation of the official upstream artifact;
4. perform one upstream patch-update rehearsal;
5. perform Python 3.15 preview adaptation research;
6. run the API-36 comparison beginning with the minimal variant;
7. validate the API-24 floor and modern/16 KB environments;
8. prove one native extension build with the development payload;
9. test the Termux-first/non-Termux-bound core boundary;
10. complete dependency license/source mapping;
11. write the uv consumer-requirements conclusion;
12. close Epoch 2 with a research synthesis stating what is ready to inform a later epoch.

The order may change when an earlier experiment exposes a dependency, but structural release implementation should not displace these questions.

## 11. Epoch 2 completion criteria

Epoch 2 is complete when it can provide a future design effort with evidence-backed answers to all of the following:

- What exact upstream Android product is consumed?
- What project-owned mutations are unavoidable?
- How is the interpreter launched and relocated?
- What binary and host-data dependencies exist?
- What Android API floor is inherited, and what do higher floors change?
- Does the product work at the oldest claimed API and on modern 16 KB systems?
- Do subprocess, HTTPS, venv, pip, uv, and native extension workflows work?
- Does the approach survive an upstream patch update and a 3.15 preview?
- Which source-build capabilities are useful fallback experiments rather than main policy?
- What must a later archive, catalog, and consumer integration express?
- What licensing and source provenance must accompany redistributed bytes?

Epoch 2 does not need to answer how the final clean repository is organized or how Epoch 3 is governed.

## 12. Final conclusion

The project has not primarily been performing useless experiments. Its launcher, relocation, closure, host-boundary, upstream-provenance, and archive work resolved real uncertainties.

The accepted real-Termux E2-P3 result now confirms that the frozen archive works as a standalone product on one modern real-device profile. The remaining highest-value Epoch 2 work is comparative and platform-focused: emulator closure, direct upstream consumption, version portability, API 36, minimum-floor compatibility, 16 KB pages, native extensions, host-profile separation, license provenance, and uv consumer requirements.

The principal adjustment is:

> Stop expanding product-form authorities as the default activity. Use the existing structure to finish the unresolved Android adaptation research that a future Astral-like release repository will need.

## References

### Current repository

- [Project README](../../README.md)
- [Current Epoch 2 context](../CURRENT_CONTEXT.md)
- [Epoch 2 charter](../epochs/EPOCH2_CHARTER.md)
- [Epoch 2 roadmap](../roadmap/EPOCH2_ROADMAP.md)
- [E2-P1 standalone artifact contract](../contracts/E2P1_STANDALONE_ARTIFACT_CONTRACT.md)
- [E2-P2 standalone façade contract](../contracts/E2P2_STANDALONE_FACADE_CONTRACT.md)
- [E2-P3 archive qualification contract](../contracts/E2P3_ARCHIVE_QUALIFICATION_CONTRACT.md)
- [E2-P3 real Termux qualification authority](../evidence/E2P3_REAL_TERMUX_ARCHIVE_QUALIFICATION_AUTHORITY_FREEZE.md)
- [Frozen launcher source](../../src/launcher/python.c)
- [Frozen CPython 3.14.6 product lock](../../config/products/cpython-3.14.6-aarch64-linux-android.lock.json)
- [Frozen dependency archive lock](../../config/dependencies/android-source-deps-aarch64-linux-android.lock.json)

### External platform and distribution references

- [Python 3.14: Using Python on Android](https://docs.python.org/3.14/using/android.html)
- [Android: Support 16 KB page sizes](https://developer.android.com/guide/practices/page-sizes)
- [Android wheel platform compatibility tags](https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/#android)
- [Astral distribution archive model](https://github.com/astral-sh/python-build-standalone/blob/main/docs/distributions.rst)
- [uv managed Python model](https://docs.astral.sh/uv/concepts/python-versions/)
- [CPython 3.15 changes](https://docs.python.org/3.15/whatsnew/3.15.html)

### Companion research conclusions

- [CPython Android API-level matrix](E2_CPYTHON_ANDROID_API_LEVEL_MATRIX.md)
- [Upstream provenance and standalone models](E2_UPSTREAM_PROVENANCE_AND_STANDALONE_MODELS.md)
