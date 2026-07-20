# E2-R1/UT-4 Evidence Freeze

```text
authority       experiments/epoch2-upstream-thin-android-data-policy/android-data-policy-authority.json
authority sha   be25e52aba1d6c9d0b2e25fec2bd1d8a0a0d9eb870436f00e81f347e90d012b7
CA policy       bundled-default-with-caller-override
timezone policy bundled-raw-zoneinfo-tree
policy coverage 6/6
negative hits   0
read-only tree  PASS
data update     PASS
audit           49/49 PASS
```

Accepted: three-root host-neutral policy, caller override semantics, raw zoneinfo mechanics, writable-state routing, fresh-venv behavior after base movement, immutable-install behavior, and data updates independent of Python updates.

Not accepted: final production CA/tzdata source selection, broad device qualification, Epoch 3 product selection, product selectability, or publication.
