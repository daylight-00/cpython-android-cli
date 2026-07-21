# E2-R1/API36-1 Evidence Freeze

```text
authority                 experiments/epoch2-upstream-thin-api36-controlled-comparison/api36-controlled-comparison-authority.json
authority sha             576f0f833164a2748a5c494780f429b4c22af5cb07d331248ac7572611b1339e
class A compile API       24 exact official
class B compile API       36 exact CPython-builder-pinned dependency release assets
class C compile API       36 pinned source-built dependencies, host-isolated
source dependency tags    6
official dependency tags  6
B dependency manifest      319/319 retained
C host isolation           True
additional deltas         13 enumerated
audit                     101/101 PASS
```

Accepted: bounded three-class comparison, exact authority bindings, runtime/ELF/behavior/benchmark/sysconfig/native-extension evidence, and explicit build/provenance burden.

Not accepted: minimum Android API, 16 KiB runtime device qualification, Epoch 3 input selection, product selectability, or publication.
