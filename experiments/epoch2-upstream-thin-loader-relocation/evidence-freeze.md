# E2-R1/UT-2 Evidence Freeze

```text
authority       experiments/epoch2-upstream-thin-loader-relocation/loader-relocation-authority.json
authority sha   05a6a21d9803d01880c6a81e0a33785edfd2b0b27b1ca4b508bd23f42219a6d2
loader          LR-3 -> LR-4
launcher        LA-2
LD_LIBRARY_PATH absent
self-reexec     absent
internal edges  0
extension fails 0
relocation      PASS
audit           33/33 PASS
```

Accepted: bounded Android/Bionic execution, relative native loader closure, selected launcher semantics, executable/getpath boundary evidence, whole-prefix relocation, and subprocess re-entry.

Not accepted: broad device qualification, Epoch 3 product selection, product selectability, or publication.
