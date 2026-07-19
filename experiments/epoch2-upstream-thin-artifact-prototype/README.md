# E2-R1/UT-1 — Astral artifact and metadata prototype

This experiment derives three deterministic local prototype artifacts from the exact official Python.org Android package frozen by UT-0:

- a full Astral-style `python/PYTHON.json + build/ + install/` audit artifact;
- `install_only`, preserving official install bytes while rewriting the archive root;
- `install_only_stripped`, with every ELF mutation recorded by before/after SHA-256.

The official package contains shared `libpython`, extensions, headers, pkg-config files, and the standard library, but no packaged Python interpreter executable. The prototype therefore marks `python_exe` unavailable, does not invent a launcher, object files, static libraries, extension object lists, or relinkable inittab material, and remains unselectable.

The accepted claim is deterministic artifact representation and consumer-readable limitations. Android execution, loader behavior, getpath, relocation, launcher selection, product selection, and publication remain outside this authority.
