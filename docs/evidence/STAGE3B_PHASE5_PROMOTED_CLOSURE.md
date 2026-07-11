# Stage 3-B Phase 5 Promoted Closure Equivalence

> **Status:** Selected target evidence
> **Execution host:** Termux on Android arm64
> **Candidate:** `work/termux/stage3b-promoted-runtime/prefix`
> **Baseline:** frozen Stage 3-A closure model
> **Result:** PASS

## Purpose

This document records the clean rerun of the Stage 3-B promoted-runtime closure gate after the probe-induced bytecode mutation defect was diagnosed and repaired.

The repaired child contract is:

```text
python -I -B -S -c ...
```

The candidate was not cleaned in place. It was freshly reassembled from the canonical promoted product before validation.

## Commands

```sh
bash \
  experiments/stage3b-target-assembly/prepare-promoted-runtime.sh

rm -rf \
  results/termux/stage3b-promoted-closure

bash \
  experiments/stage3b-target-validation/validate-promoted-closure.sh
```

## Assembly result

```text
Launcher SHA-256:
1854c482fec1ee111beae7255e713a61450351664dbf550ee2f075ed0ebd187d

STAGE3B_PROMOTED_RUNTIME_ASSEMBLY=PASS
```

## Complete inventory and mutation result

```text
candidate file entries      3155
symlinks                        5
ELF objects                    81
DT_NEEDED edges               329
inspection errors               0
unresolved edges                0

BEFORE_TREE_SHA256=131b725dc5b68580f9b9658ad57755dca75f1a3b195fb17a80158ba60af1d1d6
AFTER_TREE_SHA256=131b725dc5b68580f9b9658ad57755dca75f1a3b195fb17a80158ba60af1d1d6
MUTATION_CHECK=PASS
```

The complete candidate tree remained unchanged across the workflow.

## Native closure equivalence

```text
object_count_with_needed_edges        81
needed_edge_count                    329
unique_needed_soname_count             9

classification edges
  RUNTIME_INTERNAL                    80
  ANDROID_SYSTEM                     249

classification unique SONAMEs
  RUNTIME_INTERNAL                     4
  ANDROID_SYSTEM                       5

ambiguous_provider_soname_count        8
```

The semantic closure matched the frozen Stage 3-A model.

The ambiguous-provider aggregate remained `8`, but it is not a hard gate because filesystem provider candidates depend on the tested Android/APEX image. Edge and unique-SONAME classifications are the frozen semantic gate.

## Android-system loadability

```text
unique Android-system SONAMEs          5
dlopen PASS                            5
dlopen FAIL                            0

SYSTEM_SONAME_PROBE=PASS
```

## Extension surface

```text
extension candidates                  67
isolated imports PASS                 67
isolated imports FAIL                  0

extension discovery method      sys.path
EXTENSION_IMPORT_PROBE=PASS
```

The active extension directory was discovered from candidate runtime state:

```text
work/termux/stage3b-promoted-runtime/prefix/lib/python3.14/lib-dynload
```

The stale configured `DESTSHARED` value remained metadata only:

```text
/usr/local/lib/python3.14/lib-dynload
```

## Runtime identity

The machine verifier confirmed the active runtime identity points to the promoted candidate:

```text
sys.executable
sys.prefix
sys.base_prefix
sys.exec_prefix
active sysconfig paths
active lib-dynload discovery
LD_LIBRARY_PATH candidate component
Termux SSL_CERT_FILE
```

Observed identity included:

```text
platform              android
sysconfig platform    android-24-arm64_v8a
Python                 3.14.6 final
```

## File-entry count interpretation

The frozen Stage 3-A aggregate was:

```text
3280
```

The freshly assembled promoted candidate contained:

```text
3155
```

Delta:

```text
-125
```

This aggregate is intentionally non-gating. The complete row-level inventory is retained in the generated result tree, while closure structure, runtime identity, import surface, and mutation controls are the semantic gates.

This result must not be confused with the earlier `+43` mutation incident:

```text
earlier failed attempt
  +4 __pycache__ directories
  +39 .pyc files
  +43 total entries
  candidate mutation gate FAIL

clean repaired attempt
  before fingerprint == after fingerprint
  candidate mutation gate PASS
```

The earlier incident was validation-induced state creation. The clean rerun proves the repaired probes do not reproduce it.

## Machine verdict

The generated verifier reported:

```text
check_count     37
failed_checks   []
pass            true
```

Final markers:

```text
UNRESOLVED_EDGE_COUNT=0
SYSTEM_SONAME_PROBE=PASS
EXTENSION_IMPORT_PROBE=PASS
CANDIDATE_RUNTIME_MUTATION_CHECK=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
STAGE3B_PROMOTED_CLOSURE=PASS
```

## Conclusion

Gate 2 is closed:

```text
promoted runtime semantic closure equivalence    PASS
candidate mutation control                       PASS
frozen runtime mutation control                  PASS
machine-readable combined verdict                PASS
```

The next Phase 5 gate is CA and timezone boundary equivalence, followed by whole-prefix relocation.
