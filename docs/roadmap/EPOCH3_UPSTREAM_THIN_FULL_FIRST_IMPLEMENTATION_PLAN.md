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

## 7. First real full target transaction

The first real candidate transaction is prepared as one bounded owner runner.
It performs these operations without starting either downstream flavor:

1. reuse or acquire the exact locked Python.org Android archive and verify its
   filename, exact byte size, and SHA-256;
2. reuse or acquire the exact locked Astral 3.14.6 AArch64 GNU full reference,
   enforce a download cap, and verify its release SHA-256;
3. build the selected `Py_BytesMain` launcher from the official headers and
   shared libpython;
4. normalize the selected relocation-aware runtime and on-device SDK metadata;
5. install pip package bytes only from the upstream-carried ensurepip wheel and
   add the selected relocation-safe Android command wrappers;
6. apply and record LR-3 for every final ELF;
7. assemble the same full twice and require byte identity;
8. observe the Astral golden member tree and format-8 `PYTHON.json` before
   accepting the candidate conformance boundary;
9. verify the final member manifest, partial truthful `build_info`, native
   provider closure, AArch64 identity, exact RUNPATH, 16 KiB static alignment,
   and active-tree host neutrality;
10. execute the final extracted prefix at two locations and read-only, importing
    all 67 native modules and testing child re-entry, pip, `python-config`,
    pkg-config, and a newly created venv;
11. run an independent evidence and static-artifact audit; and
12. return the full candidate and complete evidence without freezing authority
    or creating install-only.

A passing returned result is an input to the next repository transaction. It is
not itself the full authority and does not broaden API, page-size, non-Termux,
selectability, or publication claims.

## 8. First real full execution history

### r1 — bounded harness correction required

The first owner execution acquired and verified both exact locked inputs, then
stopped before launcher construction because the safe extractor rejected the
normal leading `.` directory member in the official Python.org tar archive.
This was a harness classification error, not a product, upstream-byte, loader,
relocation, Astral-conformance, or Android-runtime failure. No full artifact was
created, the independent audit was correctly blocked, local main rolled back to
`00ac96f`, and remote main remained unchanged.

The bounded r2 correction permits `.` only when it is a directory root marker.
Absolute paths, `..` traversal, duplicate normalized members, special files,
hard links, and escaping symlinks remain rejected. Positive, expected-negative,
and incomplete fixture coverage is retained before the real target rerun.

### r2 — full assembly succeeded; qualification harness and verifier correction required

The second owner execution consumed the exact locked Python.org and Astral
inputs, built the LA-2 launcher, assembled the canonical full archive twice,
and proved byte-for-byte reproducibility. Both assemblies produced the same
3,752-member, 81-ELF archive:

```text
sha256 = 20fe6b6a7877af303461cd271f658f40750b6a3d1981f437dd730aea07c0ff12
size   = 39408292
```

The run then stopped in target qualification because Android did not provide an
optional `getconf` executable. The harness allowed `FileNotFoundError` from a
diagnostic command to abort after the substantive runtime probes had run but
before the qualification receipt was written. This is a harness error, not an
Android runtime failure. r3 records unavailable optional tools with return code
127 and derives the device page size through the candidate Python's
`os.sysconf("SC_PAGE_SIZE")`.

The r2 static verifier also over-classified seven immutable upstream strings as
active host dependencies. Six were ordinary standard-library source or test
references to `LD_LIBRARY_PATH`; one was an upstream zstd source filename in an
ELF `.rodata` diagnostic string. None was an ELF loader path, RUNPATH, NEEDED
provider, command wrapper, sysconfig value, pkg-config value, or other active
consumer configuration. Astral also documents that build-time paths may remain
as non-runtime build provenance. r3 therefore separates:

- **operational residue**, which remains a hard failure in launch commands and
  consumed runtime/SDK metadata; and
- **informational upstream provenance**, which is inventoried but preserved so
  thin does not rewrite upstream bytes without a runtime requirement.

The corrected verifier independently passes the exact r2 full archive with zero
operational residue while reporting the inert provenance strings. No full
authority, install-only implementation, selectability, or publication claim was
created by r2, and local and remote main remained at `00ac96f`.


### r3 — observed Astral representation and qualification-context paths

The same full again assembled reproducibly and passed static verification,
runtime execution at two locations, read-only execution, all 67 extension
imports, pip, venv, subprocess re-entry, and native closure checks. Two remaining
failures were verifier assumptions contradicted by the returned evidence:

- the exact Astral 20260610 full omits explicit directory members for `python/`,
  `python/build/`, and `python/install/`; those roots are represented by member
  path prefixes, and its `PYTHON.json` encodes format version as the string
  `"8"`;
- correct relocated `python-config` and pkg-config outputs necessarily contained
  the candidate prefix, which was itself under the Termux app's temporary
  directory. The verifier confused this execution-context location with a
  dependency on the external Termux package prefix.

The r4 correction follows the exact Astral archive representation and removes
the exact candidate prefix before testing for any remaining
`/data/data/com.termux/files/usr` leakage. It therefore continues to reject
external Termux compiler, include, library, or tool paths while allowing the
Android-native candidate to be tested inside the current Termux app process.
No full authority, downstream flavor, selectability, or publication claim is
created by these harness corrections.
