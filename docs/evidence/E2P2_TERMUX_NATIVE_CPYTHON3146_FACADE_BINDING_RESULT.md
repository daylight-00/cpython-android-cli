# E2-P2 Termux-native CPython 3.14.6 façade binding result

## Decision

The stable standalone façade is explicitly bound to the frozen Termux-native CPython 3.14.6 producer authority.

## Binding

```text
stable command       components/standalone/bin/cpython-android-standalone
build host role      termux
package host role    termux
producer authority   experiments/epoch2-termux-native-cpython3146-producer/producer-authority.json
binding contract     components/standalone/contracts/termux-native-cpython3146-producer-binding-v1.json
selected input       runtime-base + development-addon
preserved artifact   test-addon
```

The exact artifacts are acquired from private authority storage, independently hashed, safely inspected, and reconstructed according to their frozen manifests. The selected prefix has 1,168 owned paths and two non-owning structural-parent references.

## Preserved boundaries

- the stable command and operation names remain version-1 interfaces;
- the historical Gate 1 authority is not rewritten;
- the Stage 3-B producer remains historical and is not relabeled;
- a real stable façade build and package execution remain unclaimed;
- no real E2-P1 envelope, target qualification, selectability, publication, or transition behavior is accepted here.

## Next gate

Execute the bound stable façade on the canonical Termux producer host, preserve the build receipt and complete unqualified E2-P1 envelope, and perform an independent envelope review.
