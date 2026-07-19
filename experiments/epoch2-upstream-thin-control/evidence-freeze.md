# E2-R1/UT-0 Evidence Freeze

```text
authority       experiments/epoch2-upstream-thin-control/upstream-control-authority.json
authority sha   6cc0acee911239eb2e82267dbb2d2de0043260fe482d45e10d6aeebffebe540c
package         python-3.14.6-aarch64-linux-android.tar.gz
package sha     38bbe77d3167b5cd554e03b1021324926f09f3825202b065951dd7638e9c37e5
version         3.14.6
target          aarch64-linux-android
minimum API     24
members         3193
ELF objects     80
extensions      67
audit           17/17 PASS
```

Accepted: exact official package identity, no-mutation member fingerprint, package topology, inherited dependency provider closure, sysconfig surface, provenance map, and bounded producer delta.

Not accepted: Android runtime behavior, relocation, launcher/getpath behavior, device qualification, Epoch 3 selection, product selectability, or publication.
