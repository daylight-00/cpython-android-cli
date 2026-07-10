# Stage 3-A Closure Census Phase 1 Summary

> **Status:** Selected evidence
> **Stage:** 3-A
> **Result:** PASS

## Purpose

This summary freezes the first two observational steps of the Stage 3-A runtime closure census:

1. complete runtime file/ELF/DT_NEEDED inventory;
2. aggregation by unique SONAME and fresh-process Android-system SONAME loadability probes.

The runtime under test was the already-validated Stage 2-C assembled runtime.

## Phase 1 inventory result

Observed summary:

```text
file_entry_count             3280
symlink_count                   5
elf_object_count               81
needed_edge_count             329
inspection_error_count          0
unresolved_edge_count           0
mutation_check               PASS
```

Initial edge classifications:

```text
ANDROID_SYSTEM             249
RUNTIME_INTERNAL            80
```

No DT_NEEDED edge was classified as:

```text
TERMUX_HOST_INTEGRATION
UNRESOLVED
```

## Non-mutation result

The runtime tree fingerprints before and after inventory were identical:

```text
BEFORE_TREE_SHA256=397ff3ece20c908ab6f9664725579b8aff3cecc92394ad8214381a58ed390ddd
AFTER_TREE_SHA256=397ff3ece20c908ab6f9664725579b8aff3cecc92394ad8214381a58ed390ddd
MUTATION_CHECK=PASS
```

Frozen interpretation:

> The first Stage 3-A census inspected the runtime without mutating the runtime-prefix tree according to the content-oriented inventory fingerprint used by the harness.

## Unique SONAME aggregation

The 329 DT_NEEDED edges reduced to 9 unique SONAMEs:

```text
unique_needed_soname_count          9

ANDROID_SYSTEM unique SONAMEs       5
RUNTIME_INTERNAL unique SONAMEs      4
```

Edge counts remained:

```text
ANDROID_SYSTEM edges               249
RUNTIME_INTERNAL edges              80
```

This distinction matters:

```text
edge count
    !=
unique dependency-name count
```

Repeated references to common SONAMEs account for the difference between 329 edges and 9 unique names.

## Provider ambiguity result

Observed:

```text
ambiguous_provider_soname_count=8
```

This count means that the initial filesystem provider census found more than one candidate provider path for eight unique SONAMEs, or otherwise produced a provider/classification ambiguity according to the aggregation rule.

It does **not** mean that the runtime loads eight conflicting providers simultaneously.

Candidate-path ambiguity is expected to require interpretation on Android because system and APEX trees may expose multiple filesystem locations or aliases for a SONAME.

The actual runtime loader decision is a separate question from filesystem candidate enumeration.

## Android-system fresh-process loadability probe

All five unique SONAMEs classified as `ANDROID_SYSTEM` were probed through fresh runtime-Python subprocesses using SONAME-based `dlopen` behavior.

Observed summary:

```text
unique_android_system_soname_count   5
dlopen_pass_count                    5
dlopen_fail_count                    0
SYSTEM_SONAME_PROBE                PASS
```

Frozen interpretation:

> On the tested device and runtime environment, every unique SONAME classified as Android-system-backed by the initial census was loadable by name from a fresh subprocess of the frozen runtime Python.

This is stronger than filesystem candidate discovery alone.

It is still target-scoped evidence and is not generalized to every Android release, device, vendor image, ABI, or linker namespace configuration.

## Native closure interpretation after Phase 1

The strongest currently supported native-boundary model is:

```text
runtime prefix
    |
    +-- launcher
    +-- libpython
    +-- extension modules
    +-- bundled/internal native libraries
    |
    +-- DT_NEEDED -> 4 unique runtime-internal SONAMEs
    |
    +-- DT_NEEDED -> 5 unique Android-system SONAMEs
                          |
                          +-- fresh-process SONAME dlopen PASS
```

No Termux-prefix native library provider edge was observed in the census.

However, this does not remove all Termux integration. Stage 2 and Stage 2-C still use the Termux CA bundle through `SSL_CERT_FILE` on the tested workflow.

Therefore the current boundary is:

```text
native ELF closure:
  runtime prefix + tested Android system providers

known non-ELF host integration:
  Termux CA bundle
```

## What Phase 1 does not yet prove

The following remain open:

```text
all extension modules import successfully in isolated fresh processes
all runtime-internal provider relationships are semantically correct
non-ELF external filesystem dependencies are fully enumerated
runtime behavior without Termux-provided CA data
behavior on other Android devices/API levels/vendor images
whole-prefix relocation after Stage 3-A tooling and later distribution changes
```

## Next Stage 3-A step

The next decision-bearing test is an isolated extension-module import sweep.

Each extension module under the runtime dynamic-load directory should be imported in a fresh subprocess so that:

```text
one failing extension does not hide later results
native load failures are isolated per module
process crashes are captured as per-module return codes
```

After the import sweep, Stage 3-A should inspect non-ELF external dependencies separately.

This summary is evidence for `docs/stages/STAGE3_SCOPE.md`.
