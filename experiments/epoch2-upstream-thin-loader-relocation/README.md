# E2-R1/UT-2 — Loader, relocation, launcher, and getpath

This experiment executes the official CPython 3.14.6 Android package on the owner Android/Termux environment and compares loader variants LR-0 through LR-3, launcher variants LA-0 through LA-3, and a clean LR-4 candidate.

Selected loader input: `LR-3`. Selected launcher: `LA-2`.

The accepted result removes project-required `LD_LIBRARY_PATH` and loader-bootstrap self-reexec, closes every packaged native dependency edge with relative `DT_RUNPATH`, preserves 16 KiB ELF alignment, imports every packaged native extension, passes direct/transitive/dlopen probes, survives whole-prefix movement, and records executable/symlink/venv/getpath boundaries.

The selected launcher binary remains a result artifact, not a committed product. Device qualification, Epoch 3 product selection, product selectability, and publication remain outside this authority.
