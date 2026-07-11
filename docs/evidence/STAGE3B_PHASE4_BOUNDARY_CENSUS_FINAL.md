# Stage 3-B Phase 4.1 Product-Boundary Census Final

> **Status:** FROZEN
> **Result:** PASS — direct successor boundary established
> **Execution host:** Victor Linux workstation

## Host boundary

Phase 4.1 correctly ran on Victor.

```text
Victor responsibilities
  source/toolchain/dependency replay
  archive and prefix census
  ELF/static metadata comparison
  product locking and launcher cross-build

Termux responsibilities
  Android execution
  loader and extension import probes
  CA/uv/venv behavior
  whole-prefix relocation
  Stage 3-A closure equivalence
```

No Android runtime claim is made from workstation-only inspection.

## Complete successor accounting

```text
historical prefix entries     3155

replay package prefix entries 3151
  byte-identical entries      3077
  semantic-identical ELF        69
  producer metadata deltas       5
  package-only entries            0

historical assembly entries      4
  bin/
  bin/python3.14
  bin/python3
  bin/python
```

The four assembly entries explain the entire structural count difference.

## Native surface

All 69 regenerated CPython ELF objects matched at their loader and dynamic-symbol surfaces.

```text
semantic match       69
semantic mismatch     0
```

The 11 remaining package ELF objects were already byte-identical, reflecting the locked dependency products.

## Metadata surface

All structured metadata key sets were preserved.

The exact deltas resolve as follows.

### Producer host identity

```text
historical BUILD_GNU_TYPE  aarch64-apple-darwin24.6.0
replay BUILD_GNU_TYPE      x86_64-conda_cos6-linux-gnu
```

This is an expected producer-host delta, not a target-host delta. The target remains `aarch64-linux-android`.

### Git command paths

`GITBRANCH`, `GITTAG`, and `GITVERSION` contain commands, not captured Git results.

```text
historical source relation  ../../.git
replay source relation      ../../source/.git
```

The actual source identity is independently fixed by the replay plan:

```text
c63aec69bd59c55314c06c23f4c22c03de76fe45
```

### Toolchain and workspace paths

The remaining CONFIG_ARGS, CC, AR, build-Python, source-dir, flags, and module dependency values substitute:

```text
macOS runner workspace
darwin-x86_64 NDK prebuilt
python.exe
historical relative source layout

with

Victor workspace
linux-x86_64 NDK prebuilt
python
detached source/ layout
```

Target compiler identity remains Android API 24 with NDK 27.3.13750724.

### userbase

```text
/Users/runner/.local
/home/hwjang/.local
```

This is producer-user metadata, not a runtime-prefix dependency.

### build-details extension suffix

```text
historical  .cpython-314-darwin.so
replay      .cpython-314-x86_64-linux-gnu.so
```

This field reflects the producer host Python used to generate build details. It is not the Android extension ABI suffix.

The target evidence remains:

```text
SOABI       cpython-314-aarch64-linux-android
EXT_SUFFIX  .cpython-314-aarch64-linux-android.so
67 actual extension filenames use the Android suffix
```

### generated config.c

Only the source-layout comment differs:

```text
../../Modules/config.c.in
../../source/Modules/config.c.in
```

The generated module table is unchanged.

## Phase 4.1 conclusion

The controlled replay package `prefix/` is accepted as the direct generated successor to the historical prefix before project launcher assembly.

Acceptance does not rely on byte identity of regenerated CPython binaries or producer metadata. It relies on:

```text
closed path accounting
zero package-only paths
exact dependency ELF preservation
69/69 regenerated ELF semantic matches
preserved metadata schemas
fully classified producer metadata deltas
explicit project assembly layer
```

Result:

```text
STAGE3B_PHASE4_1=FROZEN
STAGE3B_PHASE4_2=READY
```
