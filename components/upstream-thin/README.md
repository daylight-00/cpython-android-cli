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

The artifact-family increment never rebuilds any frozen archive. It copies the
exact full, install-only, and install-only-stripped bytes into one flat
Astral-like release set and deterministically emits per-asset artifact,
manifest, provenance, qualification, license-file-inventory, and attestation
sidecars together with `SHA256SUMS` and `release-index.json`. The family remains
qualified but unselectable and unpublished until the separately cataloged
release-blocking experiments and complete component-to-license mapping close.

The release-blocker census command is evidence-only:

```text
cpython-android-upstream-thin census-licenses --family-dir FAMILY --output-dir OUT
cpython-android-upstream-thin resolve-license-provenance --family-dir FAMILY --cpython-source Python-3.14.6.tgz --output-dir OUT
```

It verifies the frozen family first, reads the canonical full archive without
extracting or modifying it, records component/version and packaged license-file
evidence, and emits an explicit gap register. It must not promote file-name or
binary-string observations into a complete legal mapping; unresolved libffi
versioning, missing dependency license texts, project notice packaging, and
Android external-provider notice policy remain blocking findings.
### RB-1 license evidence lane

`bin/cpython-android-upstream-thin acquire-license-evidence` verifies the frozen artifact family and exact source archives, preserves license-like source evidence, detects distributed HACL* and libmpdec 2.5.1 byte evidence, quarantines mismatched XZ/mpdecimal source coordinates, and emits only a non-closing component-map and NOTICE candidate. It never mutates release artifact bytes and cannot authorize selectability or publication.

### RB-1 legal integration candidate

```sh
cpython-android-upstream-thin integrate-legal-family \
  --family-dir FAMILY_R1 \
  --output-dir FAMILY_R2_CANDIDATE

cpython-android-upstream-thin verify-legal-family \
  --candidate-dir FAMILY_R2_CANDIDATE \
  --predecessor-dir FAMILY_R1
```

The revised family preserves all three artifact archives and eighteen artifact sidecars byte-for-byte, integrates the frozen legal overlay and project license, and records all pip vendored review units. It remains owner-approval-pending, unselectable, and unpublished.
