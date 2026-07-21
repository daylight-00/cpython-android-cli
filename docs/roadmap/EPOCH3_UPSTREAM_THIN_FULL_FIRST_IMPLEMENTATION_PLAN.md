# Epoch 3 upstream-thin full-first implementation plan

> **Status:** active
> **Execution model:** single append-only `main`
> **Primary rule:** adopt Astral-like behavior and structure unless the exact upstream input makes it impossible or a bounded Android adaptation is required

## 1. Work lanes

Assembly and decision-closing experiments run in parallel, but each release
surface has an explicit merge gate.

| Lane | Immediate work | Blocking gate |
|---|---|---|
| A — Full assembly | exact input verification, safe extraction, normal prefix layout, launcher integration, LR-3, metadata, full archive | E3-G1 through E3-G4 local/full receipt |
| B — Astral conformance | current golden full/install-only/stripped tree and `PYTHON.json` observations | E3-X1 before final member contract |
| C — Runtime parity | launcher/getpath/subprocess/relocation regression | E3-X2 before full qualification |
| D — Metadata consumers | standard-field policy, partial `build_info`, uv/PBS parser behavior | E3-X6 before managed-consumer claim |
| E — Data and commands | pip wrappers, CA, timezone | E3-X5 and E3-X9 before those surfaces ship |
| F — Platform claims | non-Termux context, API 24, real 16 KiB | E3-X7 and E3-X8 before broad platform claims |

## 2. Full assembly sequence

1. Verify exact official archive filename, size, and SHA-256 from the product lock.
2. Safely extract into a disposable staging root and verify one `prefix/` source tree.
3. Copy upstream `prefix/` into `python/install/` while preserving bytes, modes,
   and symlink topology.
4. Build the LA-2 launcher from the official headers/shared libpython and install
   it as `python/install/bin/python3.14`; create Astral-like aliases only after
   the golden fixture confirms exact names and link directions.
5. Apply LR-3 to the launcher and every packaged ELF. Emit one mutation row per
   object with before/after hash, dynamic tags, and alignment surface.
6. Apply only selected runtime/sysconfig normalization. Preserve producer
   metadata separately and reject unknown absolute producer paths in active
   consumer metadata.
7. Assemble `python/build/` from exact upstream material, project adaptation
   records, audits, licenses, and qualification evidence. Never fabricate
   producer object/static surfaces.
8. Generate standard Astral `PYTHON.json` format 8 from the final install tree.
9. Generate a deterministic full member manifest, create `.tar.zst`, extract it
   afresh, and verify member, metadata, ELF, host-neutrality, and relocation
   invariants.
10. Freeze the first full-assembly receipt before implementing the install-only
    projection.

## 3. Install-only sequence

1. Open and verify the accepted full archive.
2. Select only `python/install/**`.
3. Rewrite `python/install/X` to `python/X` without changing payload bytes or
   symlink semantics.
4. Exclude `python/PYTHON.json` and all `python/build/**` members.
5. Apply the E3-X1/E3-X3 golden filtering decision for tests and test-only
   extensions.
6. Emit deterministic `.tar.gz`, verify it is exactly reproducible from full,
   and qualify direct extraction and execution.

## 4. Stripped sequence

1. Start only from the verified install-only projection.
2. Census ELF debug/symbol sections before mutation.
3. Apply one pinned Android-compatible strip operation per eligible ELF.
4. Verify dynamic tags, 16 KiB alignment, native closure, extension imports,
   launcher behavior, and relocation.
5. If no bytes change because the producer already stripped all eligible
   objects, record an explicit alias/omission decision instead of pretending a
   distinct optimization occurred.

## 5. Decision points

- Golden archive observations may refine member names, aliases, filtering, and
  optional `PYTHON.json` fields, but may not change the three root/flavor rules.
- A missing upstream dependency is omitted. It is not rebuilt in Epoch 3.
- A project adaptation is accepted only when it is necessary for standalone
  Android consumption, versioned, reproducible, and fully recorded.
- A passed experiment becomes product code only through the selection register.
- No result expands publication, ABI, device, page-size, or execution-context
  claims automatically.

## 6. Immediate repository start

The first implementation increment establishes:

- `components/upstream-thin/` as the active clean product root;
- the selected LA-2 launcher source;
- deterministic safe archive primitives;
- LR-3 mutation primitives;
- a full-layout assembler and full structural verifier;
- synthetic success and negative fixtures;
- no install-only or stripped assembler before the full projection contract is
  executable.
