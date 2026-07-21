# Epoch 3 upstream-thin product contract

> **Status:** frozen for implementation
> **Primary machine contract:** `components/upstream-thin/contracts/product-v1.json`
> **Selection authority:** `docs/epochs/EPOCH3_UPSTREAM_THIN_SELECTION_REGISTER.json`

## 1. Product identity

The product is an **Astral-structured, Python.org-produced, Android-adapted
upstream-thin standalone CPython distribution**.

It satisfies three non-negotiable conditions:

1. CPython and native dependency bytes originate from the exact official
   Python.org Android archive and its inherited BeeWare dependency topology.
2. The runtime is Android/Bionic native and has no required Termux native
   dependency or Termux prefix identity.
3. Archive roots, flavor relationships, metadata semantics, installation
   layout, extraction behavior, and consumer-facing structure follow Astral
   python-build-standalone wherever the upstream input makes that truthful.

“Astral 1:1” applies to the distribution contract, not to producer ownership.
The product must not invent Astral-style object files, static libraries,
optimization variants, or dependency build records that do not exist in the
official upstream package.

## 2. Full-first invariant

The assembly order is fixed:

```text
verified official input
  -> full
  -> install_only
  -> install_only_stripped
```

No downstream flavor may be created from a separate staging tree. A verifier
must be able to reconstruct `install_only` from `full` and obtain the same
member identities. The stripped flavor is derived only from the verified
install-only projection.

## 3. Canonical full archive

```text
python/
├── PYTHON.json
├── build/
└── install/
```

The full archive is `.tar.zst`. All members have one safe `python/` root,
deterministic ordering, normalized ownership and timestamps, no absolute or
parent-traversal paths, no hard links, no special files, and only relative
non-escaping symbolic links.

### `python/install/`

This is a normal standalone prefix containing the official `prefix/` payload,
the selected project launcher, launcher aliases, bounded LR-3 ELF mutations,
and selected metadata/data adaptations. Native modules and dependency versions
remain those selected by Python.org and BeeWare.

### `python/build/`

Because upstream-thin does not own the producer object graph, this directory is
a truthful substitute containing only:

- exact upstream archive identity and retained input material;
- extracted upstream metadata and licenses;
- project launcher source/build records;
- mutation manifests with before/after identities;
- ELF, extension, dependency-closure, and host-neutrality audits;
- qualification and projection records.

It must not contain fabricated core objects, static libpython, extension object
lists, static dependency archives, or relinkable inittab material.

### `python/PYTHON.json`

The file uses Astral format version 8. Standard Astral fields retain their
standard meaning. Unavailable producer fields are omitted rather than
fabricated. Project-specific provenance remains under `python/build/hw-t/`
until a real consumer experiment proves that an additional top-level field is
safe.

## 4. Android adaptations

The selected launcher is the POSIX-equivalent CPython `Programs/python.c`
`Py_BytesMain` frontend. It owns no loader bootstrap, CA policy, prefix parser,
or custom argument semantics.

Every ELF object receives one relative `DT_RUNPATH` from its own location to
the install `lib` directory. The mutation must preserve `DT_NEEDED`, SONAME,
architecture, ELF kind, and the 16 KiB program-segment alignment contract.
Project-required `LD_LIBRARY_PATH` and bootstrap self-re-execution are
forbidden.

Runtime data and writable state follow the three-root model:

```text
INSTALL_ROOT  immutable archive-derived prefix
DATA_ROOT     independently updateable CA and timezone payloads
STATE_ROOT    caller-owned writable cache, temporary, user-site, and venv state
```

## 5. Product omissions

The initial upstream-thin product does not provide:

- project-built native dependencies or additional native extensions;
- static libpython, producer object trees, or custom built-in relinking;
- a bundled cross-build NDK/sysroot/toolchain;
- API-36 custom builds, PGO/LTO/BOLT/debug/free-threaded/JIT variants;
- detached symbols or a separate debug product;
- general multiprocessing support;
- APK/JNI packaging as part of the standalone archive.

These omissions are product boundaries, not archive defects.

## 6. Qualification and release boundary

Selection and implementation may proceed concurrently with the registered
experiments, but an affected surface cannot be published before its experiment
gate closes. Full assembly begins first. Install-only implementation may start only after
a full authority freezes the accepted full archive and its projection invariants;
stripped implementation may start only after the install-only authority freezes
the verified projection.

This contract does not authorize selectability or publication.
