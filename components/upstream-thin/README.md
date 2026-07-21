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

The second implementation increment promotes the scaffold to a bounded Android
T-class candidate workflow. It adds the selected relocation-aware sysconfig,
pkg-config, `python-config`, and upstream-wheel pip surfaces; validates every
final ELF and mutation row; assembles the full twice for byte reproducibility;
observes an exact Astral 3.14.6 AArch64 full golden; and runs launcher,
67-extension, subprocess, prefix-relocation, pip, SDK, venv, and read-only
runtime qualification. The returned result remains a candidate until its
external evidence is reviewed and frozen as the full authority.

The canonical install-only r1 projection is now frozen as the only stripped
input authority. The stripped increment may modify only regular ELF files by a
recorded safe strip operation; all non-ELF bytes, modes, paths, and symlinks
must remain identical. A separate stripped asset requires a real byte delta and
full Android requalification.

The stripped implementation censuses every regular ELF in the frozen
install-only input and applies `--strip-unneeded` only to objects that still
contain removable symbol/debug sections. The accepted input currently has 81
regular ELF files; 80 upstream-provided objects are already stripped, and only
the project-owned `bin/python3.14` launcher is eligible. A distinct stripped
asset is valid only if exactly that launcher changes while its dynamic and load
alignment surface remains identical and the complete Android qualification is
repeated.
