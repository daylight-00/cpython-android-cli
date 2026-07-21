# Epoch 3 upstream-thin product component

This is the only active product-assembly component for Epoch 3.

The component consumes the exact official Python.org Android archive, inherits
its BeeWare-derived native dependency topology, adds only bounded project
support required for a standalone Android CLI, and emits Astral-structured
artifacts in this order:

```text
full -> install_only -> install_only_stripped
```

`full` is the sole assembly authority. The other flavors are projections and
must never be assembled independently.

The initial implementation contains deterministic archive primitives, the
selected LA-2 launcher source, LR-3 mutation support, a full-layout assembler,
and local structural tests. It does not authorize publication or claim target
qualification.
